# CLAUDE.md: AST Git Resolver classifier

Start with `docs/START_HERE.md` for the current state and who does what next. Read this whole file before you touch anything. It is the design of the classifier, taken from the FYP report
(FAST NUCES Lahore, supervisor Mr. Muhammad Waqas Manzoor). Authors: Aneeza (LLM side) and Fatima (rules side).
The classifier assigns one of 23 labels to every merge conflict region. Stages 0 to 3 are rules. Stage 4 is the only LLM stage.

## 0. Rules you always follow
- Never read, print, copy or commit `.env`. Use `.env.example` as the template.
- Do not set `ANTHROPIC_API_KEY` in the shell that runs Claude Code.
- Git ignored data is not shared through git, so each person has their own copy of `data/raw/`, `data/splits/`, `outputs/` and `data.zip`. Before anything writes, regenerates, moves or deletes a file there, stop and raise a flag to the user: name the file and say the other person will not get the change through git. After the change, tell the user to send the new file to the other person and to compare `Get-FileHash` on both machines, so both work on identical data. A script that only reads these files needs no flag. This does not cover `.env`, which holds each person's own keys and is never shared, or the local caches (`__pycache__/`, `.pytest_cache/`, `.venv/`, `*.egg-info/`, `.refactor_project_marker`), which each machine builds for itself.
- The report design wins over the code. If the code disagrees with this file, the code is wrong. Ask before changing the design.
- If the report and the code are both silent, ask. Do not guess. Section 12 lists what is already known to be open.
- The dev set is for tuning. The test set is touched only once, for the final numbers.
- Run `pytest tests/rules`, `pytest tests/llm` and `pytest tests/test_pipeline.py` after every change. Report the result honestly. Never edit a test just to make it pass. Show every test change to the user for approval.
- Tests use a fake provider. No real API calls in tests.
- Money: Hack Club gives 3 dollars per day. Never start a full run without a dry run, a row count and a cost estimate first. Smoke test about 100 rows first.
- Code comments: plain English sentences, one space after the hash, no dashes, no em dashes, no arrows, no symbols, no markdown, no end punctuation. Example: `# strips whitespace from all text columns before comparison`. Keep functions small with plain English names.
- Ownership: `src/classifier/llm/` and `tests/llm/` are Aneeza's. `src/classifier/rules/` and `tests/rules/` are Fatima's. `schema.py`, `pipeline.py`, `cli.py`, `report.py`, `tests/test_pipeline.py`, `docs/`, `CLAUDE.md` and `.claude/skills/` are shared and need both of them to agree. At the start of a session the user says who they are. Do not edit the other person's folder.
- Hard boundary: `rules` never imports `llm` and `llm` never imports `rules`. Only `pipeline.py` calls both. Scripts may import from both.
- Shared full run, from 2026-11-11 until both halves are joined and revalidated (see `docs/PROGRESS.md`, "Split of the run"). Aneeza runs `outputs/full/input_aneeza.jsonl` into `luna_v2.jsonl` and Fatima runs `outputs/full/input_fatima.jsonl` into `luna_v2_fatima.jsonl`, both on commit `2d0ab73`. Rule and validator changes are allowed during the run, because `scripts/revalidate.py` reruns Stages 0 to 3 and the validators on every record afterwards. Stop and flag to the user before any of these, and say why it matters:
  - Editing `rules/ast_diff.py` or `rules/ast_gate.py`. The AST verdict after the guards goes into the prompt, so a change means later regions are asked with different evidence, and revalidate cannot fix that without new model calls.
  - Editing anything in `llm/` that changes the prompt text, the few shot examples or the model settings. That mixes two prompt versions in one run.
  - Starting or restarting the run with the model on from a folder that has uncommitted changes, failing tests or code other than the run commit. Ask the user to confirm which commit the run should load, and to note it with `git rev-parse HEAD`.
  - Running the classifier with the model on against `final_dataset.jsonl` or the other person's input file instead of your own half, or using `--rerun` on a run output. That pays twice for the same regions or overwrites finished records. `--retry-errors` is for the end of the run only.
  - Writing, moving or deleting any `outputs/full/input_*.jsonl` or `luna_v2*.jsonl` file (the git ignored data rule above also applies).
  - Remove this rule once the merged output has been revalidated.

## 1. Where the classifier sits
The full pipeline has a classifier, a resolver, a verifier and an evaluation layer. Each one is a separate module with one job.
The classifier does not resolve. The resolver does not verify. The verifier does not classify.
Each stage writes its own block into one JSON Lines record per region and can be rerun on its own.
The classifier decides which regions are logic conflicts. Only logic conflicts go on to the LLM resolver, so every label we write decides what the next stages do.
Three quality attributes matter: reproducibility (every output traceable to inputs, model version and code version), separation of concerns, and honesty about uncertainty (never report a clean result when the evidence does not support one).

## 2. Requirements for the classifier (FR-1)
Given a conflict region with base, ours and theirs text, assign exactly one label from the 23 label taxonomy.
When no single label is supported, assign `unknown` with a mandatory reason.
A region past the per file call ceiling, or whose model call fails, is recorded with no label and a status of `capped` or `llm-error`.
Use case: every region gets a record with a label (or a capped or llm-error status), a stage, and a decision trace.
If the LLM call fails at Stage 4, the record is written with status `llm-error` and a reason.

## 3. The 23 labels (Table 5.1, frozen)
Use the bare names below. No family prefix. Do not rename, add or drop a label.

| Family | Label | Meaning |
|---|---|---|
| Mechanical | same-change | Both sides made the identical edit |
| Mechanical | one-side-change | Only one side changed this block |
| Mechanical | whitespace-only | Same tokens, different spacing |
| Mechanical | reorder-only | Same items in a different order |
| Mechanical | value-only-change | Only an infrastructure literal differs |
| Mechanical | disjoint-edits | Both sides changed different, non-interacting parts |
| Structural | formatting | Only optional punctuation or style differs |
| Structural | documentation | Only comments or prose differ |
| Structural | import-restructure | Same imports, arranged differently |
| Structural | rename | Consistent identifier rename, nothing else |
| Logic | null-safety-conflict | One side guards null, the other dereferences |
| Logic | type-incompatibility | Signature change breaks how the other side uses it |
| Logic | execution-perturbation | Control-flow change skips the other side's code |
| Logic | overlap-contamination | Same entity modified on both sides, hybrid state |
| Logic | assignment-override | Both assign the same target, only one can survive |
| Logic | confluent-interference | Different variables, used together later |
| Logic | business-logic-conflict | Residual class: competing intent or modify/delete |
| Dependency | lockfile | Conflict inside a dependency lockfile |
| Dependency | package | Conflict inside package.json |
| Dependency | config-schema | Conflict inside declarative config |
| Dependency | import-path | Same binding imported from two module paths |
| Dependency | export-shape | Exported signature changed, other files import it |
| Unknown | unknown | No single label is supported by the evidence, or the region is out of scope |

The five families: mechanical labels a rule can decide from text or tokens alone. Structural labels are shape changes that should behave the same either way. Logic labels are behavioral disagreements. Dependency labels are module level changes. Unknown is the escape.
Origin: four of the seven logic labels come from ConflictLens. The other three logic labels and the dependency labels were defined for this project, and the FYP-II evaluation tests them. Mechanical labels overlap with what GitWand handles.
Exact tie breaks for hand labeling live in `.claude/skills/label-guidelines/SKILL.md`. When two labels fit, apply the stage order in section 4.

## 4. The six stages
The classifier processes each region in stages. Deterministic checks run first and the model is consulted only when the rules cannot decide. If a check cannot be verified, the region moves to the next stage and never receives a guessed label.

- **Stage 0, scope.** Binary, generated, minified, snapshot and vendored files are out of scope and get `unknown` at once. A file that is none of TypeScript, lockfile, manifest, config or prose also gets `unknown` with reason `out-of-scope`.
- **Stage 1, identity and base-relative checks.** Does one side match the other byte for byte (same-change)? Did exactly one side change relative to base (one-side-change)? Was the whole file deleted on one side?
- **Stage 2, shape checks.** Whitespace, comments, formatting, renames, import order, reordering. Uses the AST difference engine (section 5).
- **Stage 3, boundary checks.** Lockfile, manifest and config conflicts, infrastructure value changes, import-path differences, edits that do not interact (disjoint), exported symbol changes (export-shape).
- **Stage 4, LLM.** Only for regions the rules could not decide. Section 6.
- **Stage 5, finalize.** Writes the record. Section 7.

Stages 0 to 3 are deterministic and never call a model. Only regions that reach Stage 4 need LLM reasoning.
The stage order is also the tie break order for ambiguous labels: scope, identity, shape, boundary, then logic.
Which label each stage can write: Stage 1 writes same-change and one-side-change. Stage 2 writes whitespace-only, documentation, formatting, rename, import-restructure and reorder-only. Stage 3 writes lockfile, package, config-schema, value-only-change, import-path, disjoint-edits and export-shape. Stage 4 writes the logic labels, and a structural label only when a deterministic check confirms the model's hint. This split is read from the report text, so confirm any case that does not fit.

The 22 percent of regions with an empty or missing base need care: when the base is empty both sides are pure additions. Only 57 regions have no base at all (37 of them in .ts and .tsx).

## 5. The AST difference engine (`rules/ast_diff.py`)
It compares the two sides as syntax trees and returns exactly one of seven verdicts:
identical, whitespace only, comments only, formatting only, identifier rename only, content changed, not analyzed.
Each verdict has guards:
- A whitespace-only result is rejected if the two sides differ in how many lines end in `return`, `throw`, `break`, `continue` or `yield`, because a newline there changes behavior.
- A comments-only result is rejected if a directive comment differs, such as a TypeScript suppression (`@ts-ignore`, `@ts-expect-error`) or an ESLint disable, because those comments change behavior.
- A result becomes a deterministic label only if it passes its guards. A result that fails a guard is treated as content changed and goes to the next stage. It must never still be labeled whitespace-only or documentation.

## 6. Stage 4, the LLM layer (`llm/`)
There are two prompts. The model answers questions. **The model never assigns a label itself.**

1. **Router prompt.** Asks the model to classify the difference as `structural`, `semantic` or `unknown`.
   - structural: deterministic checks try to confirm one of the structural labels. If they cannot, the region is `unknown` with reason `ambiguous`.
   - semantic: go to the logic tests prompt.
   - unknown: the region is `unknown` with a reason.
2. **Logic tests prompt.** Presents seven logic tests in a fixed order. The model answers every test with supporting evidence. The tests match the seven logic labels in Table 5.1 order, with business-logic-conflict as the residual last test (check against `prompts.py` and do not reorder).
   - The pipeline, not the model, selects the first test the model marked as met.
   - A deterministic validator confirms that selection. If the validator fails, the region is `unknown`.
   - Few shot examples must be in the same per-test answer format. Build them only from hand labeled dev examples. Never invent examples.
3. **Context for the model.** FR-1 gives base, ours and theirs, so the prompts must include the base. When the base is empty, say so in the prompt (both sides are additions). For regions with no base at all, say that the direction of change is unknown.
4. **Cost and reproducibility.**
   - Every LLM call uses temperature zero.
   - No model fallback inside a run. If the primary model is unavailable, the affected regions are recorded `llm-error` and can be retried in a separate run against a single model. Do not use the `fallback` aliases in `providers.py` mid run.
   - Each file has a ceiling on the number of model calls. A region past the ceiling is not classified. It is recorded with no label and status `capped`, counted separately, and never treated as unknown.
   - A model call that fails, or returns an invalid answer after the allowed retries, is recorded with no label and status `llm-error`.
   - Retry policy: format errors are retried once with a stricter reminder, transport errors are retried with backoff up to a bounded number of attempts. A wrong answer is the validator's job, not a retry.
   - Truncated output (the model ran out of length) is a terminal error for that region. Discard the partial output.
5. **Hints, not labels.** A structural hint from the router becomes a label only after a deterministic check confirms it.

## 7. The classifier record
One record per region. Join key: **pull request, file path, conflict index** (Figure 6.6). Never join on the pull request and conflict index alone, since that pair has duplicates in the real data.
Each stage adds its own block to the record. The classifier block holds:
- label (absent when status is `capped` or `llm-error`)
- status (a fixed set of values; every non-success status has a reason code)
- reason (mandatory for `unknown` and for every non-success status)
- stage that decided
- source: whether the decision came from a rule or the model
- base state of the region (base present, empty, missing or no markers)
- input hash (the resolver compares it to the hash it recorded)
- the full trace: every test the region went through, with the result passed, failed or skipped and the reason for each
- confirming test: the test that confirmed the label (the resolver reads it)
- changed names: the identifier names that changed (the resolver reads them)
- joint use lines: empty for now, because the reconstructed data holds only the conflict region with no surrounding lines
- provenance: component version, plus model name and prompt hash for the classifier block. Rule decided regions have no model name.

Rules for the record:
- confluent-interference is recorded as `unknown` while context lines are unavailable. The resolver never sees it.
- A region that fails at any stage still produces a record, so the funnel from region to outcome can be rebuilt from records alone.
- Each block is written once per run per key. A rerun overwrites that block for that key only, so a partial rerun does not disturb other regions. Do not append duplicate records.
- Runs are resumable. The pipeline skips keys that already have a finished block.
- If the model identifier changes between runs, the new records carry the new identifier and the evaluation can filter by it.
- Every component and every prompt has a version string. Bump it when it changes.
- Input and output are JSON Lines.

What the resolver does with the classifier output, so you know why the fields matter: it reads the label, a short instruction for that label, the base state, the input hash, and (when present) the reason, confirming test, changed names and joint use lines. The resolver handles logic labels only. business-logic-conflict is escalated to a human and never sent to the LLM. A whole file modify and delete conflict has no conflict markers, so the resolver skips it as ineligible. assignment-override still goes to the LLM, flagged for human review. Nothing the resolver does changes the classifier label.

## 8. Data facts
- Final dataset: `data/raw/final_dataset.jsonl`, 4,119 pull requests, made from 4,266 rebuilt pull requests by dropping 147 with eleven or more conflict files (definition E, see `docs/decisions.md`). 3,436 have 1 to 3 files (primary population), 683 have 4 to 10 files (reported separately).
- The rebuilt data used Git's diff3 conflict style, so the base text is available. Ours and theirs text of the diff3 dataset is not claimed to be hash verified (only 26.8 percent of regions matched AgenticFlict hashes).
- The reconstructed data holds only the conflict region with no surrounding lines.
- Two populations, do not mix them. The report numbers describe all 4,266 rebuilt pull requests: 54,641 marker regions (27,690 in `.ts` or `.tsx`), 3,710 no-marker file records, 57 regions with no base. The trimmed `final_dataset.jsonl` (4,119 pull requests) holds 35,241 marker regions, 1,348 no-marker records (36,589 records in total) and 54 marker regions with no base. Always say which population a figure describes.
- No-marker records (whole file modify/delete and similar) are excluded from region statistics.
- About 22 percent of regions (report population) have an empty or missing base.
- Agents: OpenAI Codex 68.2 percent of pull requests, Devin, Cursor, Copilot, Claude Code. Results are reported per agent too.
- Split by `pr_key`, seeded and stratified, never by region.

## 9. Models and budget
- Hack Club AI gives 3 dollars per day. 10 dollars of extra API credit is on hold. Stay inside the daily limit.
- Aliases in `providers.py`: `hackclub-classify` is GPT-6 Luna, `hackclub-fallback-classify` is Gemini 3.8 Flash, `hackclub-resolve` is DeepSeek V4 Pro 0813, `hackclub-fallback-resolve` is Kimi K3. Fallback aliases are for a separate run, never inside one run.
- We are still finding out which model works best for the classifier. Enhance the prompts, compare models on the dev set, and record the choice and the cost in `docs/decisions.md`. Use the cheapest model that holds accuracy.

## 10. Repo layout
```
src/classifier/
  schema.py          shared types: Region, Result, TestAnswer, label and status constants
  pipeline.py        shared: Stages 0 to 5, call ceiling, trace, record writing, resume
  cli.py  report.py  shared
  rules/             Fatima: ast_diff.py, ast_gate.py, patterns/, validators.py
  llm/               Aneeza: prompts.py, prompt_builder.py, providers.py, parsing.py, classify_llm.py, few_shot.json, few_shot_candidates.json
scripts/             build_few_shot.py, make_split.py, make_smoke_input.py, run_funnel.py, evaluate.py, revalidate.py, compare_funnels.py, explain_disjoint.py
tests/rules  tests/llm  tests/test_pipeline.py  tests/test_schema.py  tests/test_make_split.py
docs/                START_HERE.md, PROGRESS.md, TEAM_GUIDE.md, classifier_design_from_report.md, decisions.md
data/  outputs/      data is mostly gitignored, outputs are never committed
```
Contract between the two sides (only `pipeline.py` calls them, signatures stay stable):

| Function | Side | Returns |
|---|---|---|
| `rules.run_stages_0_to_3(region)` | rules | a Result, or None meaning go to Stage 4 |
| `llm.route(region, ast_verdict)` | llm | the kind (structural, semantic or unknown) and a reason |
| `llm.run_logic_tests(region, ast_verdict)` | llm | 7 TestAnswer objects with test_id, met, evidence |
| `rules.confirm_structural(region, ast_verdict)` | rules | a structural label or None |
| `rules.validate_logic_test(region, test_id, evidence)` | rules | True or False |

## 11. How to run, in this order
1. Rules only funnel: `scripts/run_funnel.py`, which runs the pipeline with the model off, the same as `--no-llm`. Report how many regions each pattern and stage decides and how many reach Stage 4. `--no-llm` means Stage 4 is skipped by choice. It is not the same as `capped`. Those regions get no record, so a later normal run on the same output classifies only them (D11).
2. Smoke test: about 100 rows, one cheap model, a max retries limit.
3. Full run only after steps 1 and 2 are reviewed. Start from an empty output file. It resumes if it stops.
4. Evaluate with `scripts/evaluate.py` on dev labels while tuning. Test labels only for the final numbers.
Report accuracy for the rules part and the LLM part separately, plus counts of unknown, capped and llm-error. Capped and llm-error are never counted as unknown.

Phase 2 build order: (1) classifier block and `schema.py`, (2) stage order with Stage 0 and 1 and the full trace, (3) export-shape in Stage 3 (limited to detecting an exported signature change inside the region with needs_verification set, ask before going further), (4) router prompt then the 7 logic tests prompt with evidence per test, first met test wins, (5) deterministic validator per test (propose the checks and wait for approval), (6) `capped` and `llm-error` as statuses with no label, (7) changed names, confirming test, empty joint use lines, confluent-interference as unknown, (8) `--no-llm` and `scripts/run_funnel.py`, then `make_split.py` and `evaluate.py`. Stop and report after each step.

## 12. Open decisions (the report is silent, so ask, do not guess)
Record each answer in `docs/decisions.md` when it is made. Entries D3 to D8 hold the answers so far, including status values, Stage 0 lists, no-marker regions, no test met, the removed confidence answers, the call ceiling and retries.
Still open:
- What exactly counts as a changed name.
- Which checks `confirm_structural` runs (Fatima proposes).

Decided in D10, Aneeza to review: the checks of `validate_logic_test`, and the source `model` for a structural label confirmed by a rule after the model's hint.

## 13. Devlogs
When the user asks for a devlog, use this exact format and nothing else:
```
## devlog

**short title describing the change** | ~Xh or ~Xmin

**# Before**
- bullet describing what was broken or missing

**# Now**
- bullet describing what was fixed or added

**time estimate**
- filename.py -- X min (short reason what you touch in this file)
```
Before describes the problem state, Now describes the new state. Bullets are lowercase, plain English, no jargon, one line each, 6 to 10 bullets in total across Before and Now. List every file that changes with realistic minutes, and the total must match the header.