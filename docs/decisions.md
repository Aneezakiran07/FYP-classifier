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

## D4. Rule fixes made before Fatima starts (2026-11-05)

Aneeza asked for the known rule bugs to be fixed in place so `main` does not carry them. Fatima owns `rules/` from here and should review these.

### Fixed to match the report
- Stage order: `ValueOnlyChange` moved to Stage 3, and the AST gate now runs between Stage 2 and Stage 3.
- Guards: a verdict that fails a guard is now treated as content changed and is never labeled. The keyword and directive guards apply to every verdict except identical. The report names the keyword guard for whitespace and the directive guard for comments, and applying them more widely is our choice because a failure only sends the region onward.
- A file with no parser now gets `not_analyzed` from the gate, so a YAML indentation change is not called whitespace-only.
- Stage 0 now keeps only TypeScript (`.ts`, `.tsx`, as in definition E), lockfiles, manifests, config and prose.
- Lockfiles now include any dependency lockfile, such as `bun.lock`, `bun.lockb` and `Cargo.lock`.
- Whole file deletions are `business-logic-conflict`, decided at Stage 1 by a rule. This does not fit the Stage 1 label list in `CLAUDE.md`, so it is recorded here.

### Proposed, waiting for confirmation
- No-marker regions that are not deletions are `unknown` with reason `no-markers`. Fatima to confirm.
- JavaScript files named like `next.config.mjs` stay in scope and are handled as code, not as `config-schema`.

### Added on Aneeza's approval, the report does not define these
- Prose list: `.md`, `.mdx`, `.rst`, `.txt`.
- Rename guard: the report says "renamed local identifiers" but defines no check. A rename verdict now counts only when every old name is declared in the region, as a variable, function, class, type, interface, enum or function parameter. Otherwise the verdict is treated as content changed, so swapping `isAdmin(user)` for `isOwner(user)` is no longer labeled `rename`. Forms the check does not read, such as destructuring and method parameters, go onward to later stages, which is the safe direction. Fatima to review.

### Known and not fixed
- `DisjointEdits` cannot check for a joint use outside the region because the data has no context lines.

## D5. Stage 4 prompts, Phase 2 step 4 (2026-11-05)

Built on Aneeza's go ahead. `pipeline.py` is shared, so Fatima should review the Stage 4 part.

### Built to match the report
- The router asks for `structural`, `semantic` or `unknown`. The logic prompt presents seven tests in Table 5.1 order and the model answers every test with evidence.
- The pipeline selects the first test marked as met. The model never names a label.
- Both prompts now receive the base. An empty base says both sides are additions. No base says the direction of change is unknown.
- A structural hint never becomes a label. Until `confirm_structural` exists it is `unknown` with reason `ambiguous`, and the invented candidate labels are gone.
- Each prompt has a version string, recorded in provenance next to its hash.
- Few shot examples for the logic prompt must carry hand labeled `test_answers` in the per test format. An example without them is left out of that prompt, because the seven answers cannot be derived from a label alone.

### Agreed by Aneeza, the report is silent on these
- No test met gives `unknown` with reason `no-test-met`.
- `other`, `null` and the confidence field are removed from the model answer, so there is no confidence threshold in the classifier.
- A test id is the name of the label it supports, so no mapping table is needed.
- `llm.route` returns the kind and the reason together, because a router `unknown` needs a reason. The contract in `CLAUDE.md` names only the kind. Fatima still needs to agree to this one, because the contract is shared.
- A test after the selected one is `skipped` in the trace even when the model marked it as met, and the answer of the model is kept on that entry.

### Temporary until later steps
- No validator exists yet, so a selected label is written with `needs_verification` true and a `validator` trace entry of `skipped` with reason `validator-not-built`. No full run should happen before step 5.
- Rule stages write no trace yet, so the trace only covers Stage 4 for now.

## D6. Failure handling and the call ceiling, Phase 2 step 6 and part of step 7 (2026-11-05)

`pipeline.py`, `cli.py` and `report.py` are shared, so Fatima should review this.

### Built to match the report
- A failed call or an invalid answer is `llm-error` with no label and no source. It is never counted as `unknown`. The model name and prompt hashes stay in provenance.
- Every call uses temperature zero. A reply that ran out of length is thrown away and is `llm-error` with reason `truncated-output`, with no retry.
- A format error is retried once with a stricter reminder. A wrong answer is not retried.
- A selected `confluent-interference` test is `unknown` with reason `no-context-lines`, and a later test does not take over.
- `confirming_test` is the selected test for a model label, and the pattern or AST verdict for a rule label.
- Joint use lines stay empty. Changed names are not done, because they wait for a definition agreed with Fatima.

### Chosen because the report is silent, Aneeza gave the go ahead
- Reason codes for `llm-error`: `provider-unavailable`, `provider-rejected`, `transport-error`, `invalid-answer`, `truncated-output`.
- Transport errors get at most 5 attempts in total, with backoff. `--max-retries` changes that number and 0 no longer means forever.
- Status codes 400, 401, 403 and 404 are not retried, because sending the same request again cannot help.
- Error text from a provider is not written to the record or printed, because it can echo a key. Only the error type and status code are kept.
- The ceiling counts model replies per file within one pull request, including format retries, and not failed transport attempts. A transport outage therefore gives `llm-error`, not `capped`.
- The count is stored in the block as `model_calls`, so it survives a resume.
- The ceiling is 50 calls per file. The old value of 15 counted regions, not calls. On the 14,013 regions of `final_dataset.jsonl` that reach the model, if every region uses two calls, 50 calls caps 103 regions in 8 files. 30 calls would cap 241 and 15 would cap 998. A region that starts below the ceiling finishes, so a file can pass 50 slightly.
- An `llm-error` is skipped on resume. `--retry-errors` runs those regions again against one model and overwrites their records. A rerun is free to restart the count.
- A single model run stops at the start when its key or SDK is missing, so a bad setup does not write thousands of `llm-error` records.

## D7. The three old rules test failures (2026-11-05)

Aneeza asked for these to be fixed. They were stale tests, so the tests changed and the code did not. Fatima should review them, since `tests/rules/` is hers.

- The registry test expected 11 patterns, and there are 14. It now pins the 14 names in stage order, which also catches a pattern moved to the wrong stage.
- Two whitespace cases expected the AST gate to decide, but the `WhitespaceOnly` pattern decides them first. Both are Stage 2 and give the same label. These two inputs now assert the pattern decides.
- Two new inputs that do reach the gate replace them in the gate test: fragments that do not parse and hold a regex or JSX. This keeps coverage of the gate's whitespace verdict.
- `CLAUDE.md` section 0 and `docs/TEAM_GUIDE.md` section 9 still mention these failures. They need updating once Fatima agrees.

## D8. Merging without waiting for review (2026-11-05)

Aneeza decided to merge the work in D4 to D7 to `main` without waiting for Fatima's review, so both can start from one state. This includes changes to shared files and to `tests/rules/`. Wherever D4 to D7 say Fatima should review, read it as: Fatima was not asked first and can still change it. `docs/START_HERE.md` lists what to check.

The split in `scripts/make_split.py` is also our choice, because the report gives no ratios: 70 percent train, 15 percent dev and 15 percent test, seed 20261105, stratified by the file count bucket. It is not stratified by agent, because `filtered_prs.csv` is not in the repo. Adding the agent would change which pull requests land in each set, so decide before anyone hand labels the dev set.

## D9. Rename guard change after reviewing the rename regions (2026-11-06)

Fatima reviewed the rename guard from D4 and changed it. Aneeza agreed to this entry.

### What was found
The parser calls 434 regions in train and dev a rename. The old guard kept 40 of them. Most rejections were right, for example a renamed import, a renamed method call, or a name declared outside the region. Two kinds of mistake were found.
- A renamed named export was kept as a local rename. Other files import that name, so it is not local. Table 5.1 has a separate export-shape label for this.
- Array destructuring and catch parameters were rejected, even though they declare local names. Array destructuring is by position, so a new name is a real local rename.
- A bare `type X` inside an import list was counted as a declaration. The name comes from another file.

### What changed in `ast_gate.py`
- A named export (`export const x`, `export function x`, `export { x }`) fails the guard. A default export does not, because each importing file picks its own name.
- `const [a, b] = ...`, `let [a, b] = ...` and `catch (e)` count as declarations.
- `type X` counts as a declaration only for a type alias (`type X =` or `type X<T> =`).
- Object destructuring was left out on purpose. The name picks which property is read, so a new name changes behavior.
- The stale comment about a "clarification document" and the rule 10 graph check was replaced.

### The comparison
Old guard against new guard on every parser rename region, train and dev only.

| Result | Regions |
|---|---|
| Kept by both | 29 |
| Rejected by both | 387 |
| Newly kept | 11 |
| Newly rejected | 6 |
| Failed the newline or directive guard | 1 |

All 17 changed regions were read by hand. The newly kept ones are array destructuring and one catch parameter. The newly rejected ones are named exports and a type name in an import list. The first look also covered the test split before the scripts were limited to train and dev. The change rests on what the code means and not on test examples, and the test split is not used again until the final numbers.

Reproduce with `python scripts/review_rename_guard.py` and `python scripts/compare_rename_guard.py`. Both need `data/splits/split.jsonl` from `scripts/make_split.py`.

### Known limits
- The guard reads the region text with regular expressions, so a declaration inside a comment or a string would still match.
- A kept rename is only checked inside the region. The same name may be used elsewhere in the file, and the data has no context lines.
- A rename that also changes or drops a comment still counts as a rename. This is about 4 regions in the first look.

### Open
- Should a rename plus a comment change still be `rename`? The report says "consistent identifier rename, nothing else".
- Where did the "clarification document" in the old comment come from? It is not in the report extract.
## D10. Validators and their wiring into Stage 4 (2026-11-07)

Fatima built `rules/validators.py` and wired it into `pipeline.py`. Aneeza said to go ahead and review afterwards, so every choice below was made without waiting for her. Aneeza can still change any of it, the same way D8 worked the other way round. `pipeline.py` and `tests/test_pipeline.py` are shared. Nothing in `llm/` or `tests/llm/` changed.

### What `validate_logic_test(region, test_id, evidence)` checks
Two checks, and both must pass.

1. **The evidence is real.** The evidence must hold at least one quoted piece. Backticks are read first, and double quoted text of three or more characters only when there are no backticks. A leading `OURS:`, `THEIRS:` or `BASE:` is removed. Every piece must appear in the ours, theirs or base text once all whitespace is removed. A parser change name such as `call_added` is accepted, because it comes from the AST summary and not from the region text.
2. **A cheap check for the selected test holds on the region.**

| Test | Check |
|---|---|
| null-safety-conflict | The two sides have a different count of `null`, `undefined`, `?.`, `??` or `!.` |
| type-incompatibility | The set of signature lines differs (function, arrow, interface, type alias, return type) |
| execution-perturbation | The control flow lines differ in order or content (`if`, `return`, `throw`, loops, `try` and similar), with comments ignored |
| overlap-contamination | Both sides changed lines against the base and those lines share an identifier that is not a keyword |
| assignment-override | The same target is given different values on the two sides |
| confluent-interference | Always fails, because there are no context lines to show a joint use |
| business-logic-conflict | The two sides differ once whitespace is removed |

An unknown test id fails. On the 67 smoke records with a met test, 60 pass both checks (`scripts/measure_validators.py`, train and dev only). The checks are deliberately cheap. They catch evidence the model made up and answers that cannot be true for the region. They do not prove the label is right.

### Wiring of the logic tests
- After the pipeline picks the first met test, it calls `validate_logic_test` with the Stage 4 region, which includes the base.
- A pass writes the label as before. The trace gets a `validator` entry of `passed` with the test id.
- A fail gives `unknown` with `unknown_reason` `validator-failed`, priority `high` and no confirming test. The trace gets a `validator` entry of `failed`, reason `validator-failed` and the test id.
- A later met test does not take over after a fail. The first met test is the answer of the model, and a fail means that answer is not supported. This matches how `confluent-interference` already works.
- `confluent-interference` still becomes `unknown` with `no-context-lines` before the validator runs.

### Decided without waiting, with the reason
- **Where the code `validator-failed` goes.** In `unknown_reason`, with a plain sentence in `reason`. This is the convention `no-test-met`, `ambiguous` and `router-unknown` already use, so `evaluate.py` can count every unknown cause from one field.
- **`needs_verification` stays true for every model label, also after a pass.** The validators are text checks, so a person still reviews. The priority tells them apart: `normal` after a pass, `high` for an unknown.
- **Source of a structural label confirmed by a rule after the hint of the model: `model`.** This was open since D3, and Aneeza had proposed `model`. The rule only runs because the model hinted, so the decision belongs to Stage 4 and counts in the LLM part of the evaluation. Stage is 4 and the provenance carries the model name and router prompt hash. `confirming_test` is `confirm-structural`, so the evaluation can still pick these regions out.

### Wiring of `confirm_structural`
- On a structural hint, the pipeline calls `confirm_structural(region, ast_verdict)`.
- None gives `unknown` with `ambiguous`, as before. The trace entry is now `confirm-structural` `failed` with reason `structural-not-confirmed`, where it used to be `skipped` with `validator-not-built`. The constant `VALIDATOR_NOT_BUILT` is gone because nothing uses it now.
- A label is written with the bare name, so `structural/rename` becomes `rename`. Only `formatting`, `documentation`, `import-restructure` and `rename` are allowed. Any other label is a bug in the rule and stops the run with an error, so it cannot be written silently.
- **`confirm_structural` still returns None for every region**, so in practice every structural hint is still `unknown` with `ambiguous`. When Fatima builds the checks, nothing in `pipeline.py` has to change.

### Test changes in `tests/test_pipeline.py`
- The fake model used the evidence `"quoted"`, which is in no region, so the validator rejected it. The fake now quotes region text the way the real model does, such as `` `OURS: x = 1` ``.
- The two selection tests used `execution-perturbation` on `x = 1` against `x = 2`, which has no control flow change. They now use a region where one side guards a call with `if`, so they still check that the first met test wins.
- The validator trace entry is now expected to be `passed`. The test for an unbuilt validator became a test that a confirmed label stays flagged.
- New tests: evidence not in the region fails, a failing test check fails, a structural hint confirmed by a rule becomes a `model` label, and a rule that confirms a hint with a logic label stops the run. The structural hint test also checks the new trace reason.

### For Aneeza to look at
- The table of checks above, mainly whether any check is too strict for real answers. The 7 smoke records that fail are listed by `scripts/measure_validators.py`.
- The `model` source for a confirmed structural label.
- Nothing else waits on her. Fatima continues with `confirm_structural` checks, the Stage 0 to 3 trace, `export-shape` and `--no-llm`.

## D11. `--no-llm` and the rules only funnel, Phase 2 step 8 (2026-11-07)

Fatima built these. `cli.py`, `pipeline.py`, `report.py` and `tests/test_pipeline.py` are shared, so Aneeza should review. Nothing in `llm/`, `rules/` or `tests/llm/` changed.

### `--no-llm` in `cli.py`
- Runs Stages 0 to 3 as usual and skips Stage 4 by choice. No model is called and no API key is checked, so it runs on a laptop with no key.
- **A region that reaches Stage 4 gets no record.** It is counted, and the report prints `reached Stage 4 with the model off, no record written`. It is never written as `capped`, because `capped` means the call ceiling was hit (report 6.4.5 and `CLAUDE.md` section 11).
- Why no record, and not a new status: a new status would change the frozen status set in `schema.py` (D3). Every resume rule would also have to treat it as unfinished. With no record, a later normal run on the same input and output resumes and classifies only the regions that reached Stage 4. The rule records are reused, and the model is called only for the regions that need it.
- `CLAUDE.md` section 7 says a region that fails still produces a record. A region skipped by `--no-llm` has not failed, and a real run with the model still writes a record for every region. The output of a `--no-llm` run is a partial file on purpose. The funnel counts the missing regions from the input.
- `--no-llm` refuses `--models`, `--retry-errors` and `--max-calls`, because they only make sense with a model.
- `--no-llm` also refuses `--rerun`. A region that reaches Stage 4 writes nothing, so an old model record for that key would survive the rerun and mix into the counts. To count again, start from an empty output file. `run_funnel.py` does this with `--overwrite`.
- `rules.jsonl` from the funnel is not a complete run. Regions that reached Stage 4 have no record there, so `evaluate.py` must not score it as one.
- `pipeline.run_one` and the functions it calls take a new `use_llm` argument, true by default. Nothing changes for a normal run.

### `scripts/run_funnel.py`
- Reads `data/raw/final_dataset.jsonl` and `data/splits/split.jsonl`, keeps the chosen splits, and runs the normal pipeline with the model off. It writes four files to `outputs/funnel/`: `input.jsonl`, `rules.jsonl`, `run.log` and `summary.json`.
- **Train and dev by default.** The test split needs `--splits test` or a list that includes it, plus `--include-test`. Without the flag the script refuses, because the test set is used only once, for the final numbers.
- It counts marker regions by the stage that decided them, and how many reached Stage 4. The same counts are shown for `.ts` and `.tsx` alone, because the report figures are given that way.
- It counts each deciding rule with its label. The rule is the pattern name, or the AST verdict for the gate, taken from `confirming_test`.
- No marker records are counted apart and are not part of the region numbers (`CLAUDE.md` section 8).
- It refuses to write over an earlier `rules.jsonl` unless `--overwrite` is given, so model records from another run cannot mix into the counts.
- The pipeline prints one line per region, so that output goes to `run.log`. The summary is printed and also saved as JSON for the report.
- It prints the population (dataset and splits), because the two populations in `CLAUDE.md` section 8 must never be mixed.

### Tests
- Three new tests in `tests/test_pipeline.py`. `--no-llm` writes only rule records, calls no model and needs no key. A normal run after it classifies only the Stage 4 regions and keeps the rule records unchanged. `--no-llm` refuses options that need a model.
- New file `tests/test_run_funnel.py` with four tests: the counts per stage and per rule, the test split left out unless asked for, no silent overwrite, and an unknown split name refused. A fake model fails the test if it is ever called.
- No existing test was changed.

### First funnel numbers (2026-11-07)
Population: `final_dataset.jsonl`, train and dev only, 3,502 pull requests, 30,355 marker regions (15,247 in `.ts` or `.tsx`) and 1,061 no marker records. A separate count straight from the dataset matched every number (`check_funnel_counts.py`, not committed).

| Stage | All marker regions | `.ts` and `.tsx` |
|---|---|---|
| Stage 0 scope | 1,673 (5.5%) | 5 (0.0%) |
| Stage 1 identity | 562 (1.9%) | 509 (3.3%) |
| Stage 2 shape | 1,447 (4.8%) | 804 (5.3%) |
| Stage 3 boundary | 14,793 (48.7%) | 2,142 (14.0%) |
| Reached Stage 4 | 11,880 (39.1%) | 11,787 (77.3%) |

- Lockfiles alone are 11,711 regions, which is most of Stage 3. Without lockfiles the rules decide far less, so the `.ts` and `.tsx` column is the honest figure for code: the rules decide 22.7 percent of it.
- `DisjointEdits` decides 1,946 regions, 1,934 of them TypeScript. This is the largest rule label on code, and it cannot check for a joint use outside the region because the data has no context lines (D4). Check it first when hand labeling dev.
- `rename` decides 39 regions after the D9 guard.
- No marker records: 584 one side deletions as `business-logic-conflict`, 477 `unknown`.
- 11,880 of 30,355 is 39.1 percent. D6 counted 14,013 of 35,241 on the whole dataset, 39.8 percent, so train and dev look like the whole.
