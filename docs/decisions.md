# Decisions

A running log of decisions for the AST Git Resolver classifier. Add new entries at the bottom.
Each entry says what we decided, why, and how to reproduce or undo it.

## D1. How the dataset goes from 4,266 to 4,119 pull requests (2026-11-04)

### Decision
The classifier and the train, dev and test split work on `final_dataset.jsonl`, which has 4,119 pull requests.
It is made from `combined_success.jsonl` (4,266 rebuilt pull requests) by removing every pull request with eleven or more conflict files.

### The rule
- A pull request is excluded when its conflict file count is above 10. It is kept when the count is 10 or fewer.
- The filter is at pull request level, not repository level.
- Kept pull requests fall into two groups: 1 to 3 files (primary population) and 4 to 10 files (evaluated separately).
- The cutoff of 10 is a command line option (`--max-files`), because the report says it may change after the pilot. The primary group edge is `--primary-max` (default 3).

### What counts as a conflict file
The report does not define it, so we tested it. The definition we use is **E**:

> the number of distinct `.ts` and `.tsx` file paths across all regions of the pull request, including the no marker records (for example `deleted_by_us`).

Counted this way, the real data gives exactly the numbers in the report.

| Definition | Excluded | Kept | Kept with 1 to 3 files | Matches report |
|---|---|---|---|---|
| A: distinct files with conflict markers | 192 | 3,969 | 3,044 | no |
| B: A limited to .ts and .tsx | 125 | 3,987 | 3,365 | no |
| C: A plus no marker records | 238 | 4,028 | 3,021 | no |
| **E: distinct .ts and .tsx over all regions, including no marker records** | **147** | **4,119** | **3,436** | **yes, all three** |

For A and B the kept count drops because pull requests with zero counted files are dropped as well (A has 105, B has 154). Definition E has no zero file pull requests and no pull requests missing from the data.

### The numbers, step by step
| Step | Pull requests |
|---|---|
| Rebuilt pull requests in `combined_success.jsonl` | 4,266 |
| Excluded for eleven or more conflict files | 147 |
| Dropped for zero conflict files | 0 |
| **Kept in `final_dataset.jsonl`** | **4,119** |
| of which 1 to 3 files (primary) | 3,436 |
| of which 4 to 10 files (evaluated separately) | 683 |

### How we found the definition
1. The first version of the filter tried A, B and C. None matched, so we did not choose one by guessing.
2. A read only diagnostic (`explore_definitions.py`) tried every combination of file types, with and without no marker records, at cutoffs 9, 10 and 11. Exactly one combination matched all three report numbers: `.ts` and `.tsx` only, including no marker records, cutoff 10. The next closest was off by 7.
3. Separately, the earlier pilot script counted the files listed in `expected_conflict_files` of `filtered_prs.csv`. That is a second way the numbers may have been produced (called definition D in the script). It was not run for the final dataset, see open items.

### Files produced
All three are written next to the input. The input is never edited.
- `final_dataset.jsonl`: the 4,119 kept pull requests. Lines are exact copies of the originals with no added fields.
- `excluded_prs.jsonl`: the 147 excluded `pr_key` values with their file count and reason.
- `final_dataset_index.jsonl`: `pr_key`, file count, group and definition, for later grouping by 1 to 3 and 4 to 10 files.

### How to reproduce
Put `filter_dataset.py` and `combined_success.jsonl` in one folder and run:
```
python filter_dataset.py --definition E
```
Expected output: kept 4,119, excluded 147, kept with 1 to 3 files 3,436, kept with 4 to 10 files 683.
The script refuses to overwrite existing output unless `--overwrite` is given.

### Suggested wording for the report
The report says "conflict files" without defining it. Suggested half sentence: "conflict files are counted as distinct TypeScript (.ts and .tsx) files across all conflict records of the pull request, including records where one side deleted the file".

### Open items
- **Cross check with the CSV (definition D).** E matches all three headline numbers. We have not yet confirmed that the CSV based definition D picks the same pull requests. Run `python filter_dataset.py --definition D --overwrite --output d_check.jsonl --excluded d_excluded.jsonl --index d_index.jsonl` with `filtered_prs.csv` present and compare. If the kept sets differ, decide which one the report describes.
- **Per agent breakdown.** `combined_success.jsonl` has no agent field. The agent column is in `filtered_prs.csv`, so the per agent table needs that file.

## D2. Decisions made during the Phase 1 refactor (2026-11-04)

- `build_few_shot.py` lives in `scripts/`, not in `llm/`. It imports the AST engine from `rules/`, and llm must never import rules.
- The `--no-llm` flag is not part of Phase 1. It changes behavior, so it comes in Phase 2 step 8.
- `schema.py` is a comment only placeholder until Phase 2, because the old code has no Region, Result or TestAnswer types.
- `smoke_test.jsonl` is classifier output, so it was placed in `outputs/`.
- Three tests already failed in the original code and were left alone: one expects 11 patterns but there are 14, and two whitespace cases are now decided by the pattern layer before the AST gate. They need a decision from the owners.
- Dev set is for tuning. The test set is touched only for the final numbers.

## D3. Decisions made for the Phase 2 gap list (2026-11-05)

Answered by Aneeza. Everything that touches `rules/` or a shared file still needs Fatima's review before merge.

### Record format, applied in step 1
- Join key: `pr_key`, `file_path` and `effective_index` (report Figure 6.6). `pr_key` plus `conflict_index` alone has 11,081 duplicates in the final dataset.
- Labels use the bare names of Table 5.1. Rule patterns still emit the old prefixed names until Fatima approves changing them, and the pipeline converts them when it writes the block.
- Status of a normal labeled region: `classified`.
- Base state values: `present`, `empty`, `missing`, `no-markers`.
- Provenance: component version from `pyproject.toml`, plus the SHA-256 of each final system prompt including few shot examples. Rule decided regions carry no model name.
- Input hash: the report does not define it, so this is our choice. SHA-256 over file path, conflict type, base, ours and theirs, with absent values kept as null. Identical regions can share a hash, which is fine because the join key differs.
- Capped block: stage 4, source null, model name null, reason `call-ceiling`.
- Small samples are committed, so `data/samples/` is in git. Big files such as `data/raw/` stay out.
- Reruns: one block per key, and a rerun overwrites it (report 6.5). `--rows` and `attempt_number` are dropped. `--rerun` overwrites the keys in its input, so a partial rerun or a smoke test uses a smaller input file.

### Open, for Fatima to review
- **Source of a structural label confirmed by a rule after the model's hint.** Aneeza chose `model`. Not built until steps 4 and 5.
- **Two prompt hashes.** The report says "the prompt hash" in the singular, and there are two prompts. Aneeza chose two fields, so a router only region is not affected by a change to the logic prompt. `router_prompt_hash` is recorded on every region that went to the model. `logic_prompt_hash` is recorded only when the logic prompt ran, and is null otherwise.

### Answered, applied in later steps
- Stage 0 (step 2): the report scopes to TypeScript, so `.js`, `.jsx`, `.mjs` and `.css` are out of scope unless they are config files. Any dependency lockfile counts, including `bun.lock`, `bun.lockb` and `Cargo.lock`. The prose list is to be proposed.
- Deletions (step 2): a deletion on one side is `business-logic-conflict`, not `one-side-change` (Table 5.1 and 5.3.2). The other no-marker regions are proposed as `unknown` with a reason, to be agreed with Fatima.
- Trace (step 2): tests after the deciding one appear as skipped with a reason.
- Base in prompts (step 4): the prompts include the base. An empty base means both sides are additions. With no base the direction is unknown.
- Proposed for step 4: no test met gives `unknown` with reason `no-test-met`, and the low confidence threshold is dropped because the validator is the gate.
- Call ceiling (step 6): counts model calls per file, and the count is recorded in the block so it survives resume. The limit of 15 is a placeholder.
- Retries (step 6): format errors are retried once with a stricter reminder. Transport errors are retried with backoff up to a bounded number, to be proposed.
- `llm-error` on resume (step 6): skipped by default, with a flag for a separate retry run against one model (report 6.4.5).
- No model fallback inside a run (report 6.4.5): the fallback aliases are never used mid run.
- Changed names (step 7): a definition from `identifier_delta` is to be proposed and approved by Fatima.
- Taxonomy document: Aneeza will confirm whether it exists. If not, `label-guidelines` is the stand-in and the "taxonomy rules 1 to 16" comments are removed.
