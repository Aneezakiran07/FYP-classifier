# Start here

The starting point for Aneeza and Fatima, as of 2026-11-05. It says what exists on `main`, what the numbers are, and who does what next.

Read this first. Then read `CLAUDE.md` (the design and the rules) and `docs/decisions.md` entries D3 to D8 (every choice made so far). `docs/PROGRESS.md` is the live checklist, so update that one as work moves.

## 1. Where we are

**The whole classifier runs end to end, including a real model, but its labels are not trustworthy yet.**

Two things are missing before we can trust them:
1. **Validators.** Done for logic labels on 2026-11-07 (D10). A model label whose evidence or check fails is now `unknown` with `validator-failed`. Every model label is still flagged `needs_verification`, and `confirm_structural` has no checks yet.
2. **Hand labels.** We have none, so no accuracy number exists for the rules or for the model.

Do not start a full run until both exist and the prompts have been tuned.

**Goal:** run `data/raw/final_dataset.jsonl` with the LLM stage on, and get a trustworthy label or status for every region. Then report the final numbers on the test set, once.

## 2. How a region moves through the classifier

There is one command, and the rules and the model both run inside it. Nobody hands filtered pull requests to anyone: the regions the rules cannot decide go to the model automatically.

```
final_dataset.jsonl
   |
   Stage 0   scope: out of scope files get unknown
   Stage 1   identity: same-change, one-side-change, whole file deletion
   Stage 2   shape patterns, then the AST gate with its guards
   Stage 3   boundary: lockfile, package, config, values, import paths, disjoint edits
   |
   Stage 4   only what is left: router prompt, then 7 logic tests prompt
   |           The model answers tests. The pipeline picks the first met test.
   |           A validator confirms it, or the region is unknown.
   Stage 5   one record per region in a JSON Lines file
```

## 3. What exists on `main`

### Rules, `src/classifier/rules/` (Fatima owns this from here)
| Part | State |
|---|---|
| `ast_diff.py`, the AST engine with 7 verdicts | Working |
| `ast_gate.py`, verdicts to labels, with the guards | Working. A failed guard means content changed. |
| `patterns/`, 14 patterns in stage order | Working |
| Rename guard | Working, our own choice, and probably strict (see section 7) |
| `export-shape` | **Missing** |
| `validators.py` (`validate_logic_test`, `confirm_structural`) | `validate_logic_test` working and wired (D10). `confirm_structural` wired, always returns None |
| `run_stages_0_to_3` | **Missing.** `pipeline.py` calls the patterns and the gate directly for now. |
| Trace for Stages 0 to 3 | **Missing.** Only Stage 4 writes a trace. |
| Changed names | **Missing**, needs an agreed definition |

### LLM, `src/classifier/llm/` (Aneeza owns this)
| Part | State |
|---|---|
| `prompts.py`, router and 7 logic tests, with version strings | Working, not tuned |
| `prompt_builder.py`, sends the base and explains empty or missing base | Working |
| `parsing.py`, refuses any answer that is not all 7 tests in order with evidence | Working |
| `classify_llm.py`, `route` and `run_logic_tests`, retries, reason codes | Working |
| `providers.py`, temperature zero, truncation check, token counting | Working |
| `few_shot.json` | **Empty**, needs hand labels |

### Shared
| Part | State |
|---|---|
| `schema.py`, 23 labels, statuses, base states, input hash | Working |
| `pipeline.py`, stage order, Stage 4 selection, records, resume, rerun, call ceiling | Working |
| `cli.py`, `report.py` | Working |
| `--no-llm` flag | Working (D11). Regions that reach Stage 4 get no record, never `capped` |

### Scripts
| Script | State |
|---|---|
| `make_split.py` | Working |
| `make_smoke_input.py` | Working, picks random regions that reach the model from train or dev |
| `build_few_shot.py` | Working, nothing to build from yet |
| `run_funnel.py` | Working (D11). Train and dev by default, the test split only with `--include-test` |
| `evaluate.py` | **Missing** |

### Tests
All pass with no real API calls:

| Suite | Passed |
|---|---|
| `tests/rules` | 93 |
| `tests/llm` | 43 |
| `tests/test_pipeline.py` | 37 |
| `tests/test_schema.py` | 15 |
| `tests/test_make_split.py` | 5 |

### Not in git
- `.env`: your own keys, copied from `.env.example`. Never read, print or commit it.
- `data/raw/`: share outside git.
- `data/splits/split.jsonl`: run `make_split.py`, and the seed gives both of us the same split.
- `outputs/`: run results.

## 4. The numbers so far

All of these describe `final_dataset.jsonl` (4,119 pull requests, 36,589 records). The report describes a different, larger population of 4,266, so always say which one a figure uses.

**What the rules decide, with no model:**

| Result | Regions |
|---|---|
| Reach the model | 14,013 |
| Lockfile | 13,059 |
| OutOfScope | 2,521 |
| DisjointEdits | 2,307 |
| CommentsOnly | 1,158 |
| NoMarkers, deletion as business-logic-conflict | 695 |
| PackageManifest | 646 |
| OneSideChange | 565 |
| ConfigSchema | 515 |
| WhitespaceOnly | 334 |
| ImportPathOnly | 262 |
| AST formatting | 152 |
| NoMarkers, other as unknown | 141 |
| SameChange | 64 |
| AST identical | 47 |
| AST rename | 44 |
| AST whitespace | 40 |
| ImportRestructure | 13 |
| AST comments | 7 |
| ReorderOnly | 6 |

These counts were last taken on the rule fixes. Rule counts have no accuracy behind them yet.

**The split:** by `pr_key`, seed 20261105, 70, 15 and 15 percent, stratified by file count bucket.

| Set | 1 to 3 files | 4 to 10 files | Total |
|---|---|---|---|
| train | 2,406 | 479 | 2,885 |
| dev | 515 | 102 | 617 |
| test | 515 | 102 | 617 |

2,125 dev regions reach the model. The split is not stratified by agent, because `filtered_prs.csv` is not in the repo. Adding it would change the sets, so decide this before hand labeling starts.

**The first real run (smoke test):** 100 random dev regions on GPT-6 Luna (`hackclub-classify`).

| Result | Count |
|---|---|
| Records, unique keys, failed calls | 100, 100, 0 |
| Router: semantic, structural | 95, 5 |
| `unknown`, no test met | 28 |
| `unknown`, structural hint not confirmed | 5 |
| business-logic-conflict | 27 |
| overlap-contamination | 22 |
| assignment-override | 9 |
| execution-perturbation | 7 |
| type-incompatibility | 2 |

- **Tokens and cost:** 242,147 input and 125,870 output, about 0.09 dollars at the listed prices (0.10 and 0.50 per million). The Luna price came from a summary of the Hack Club model list and was not checked word for word.
- **Time:** 46 minutes with a 1 second delay, about 28 seconds per region.
- **Full run estimate:** about 12 dollars and about 4.5 days running without a stop, which fits under 3 dollars per day. This scales from 100 regions, and few shot examples would add to it.
- **These labels are not accuracy.** They only show that the run works. No one has checked whether any of them is right.

**What the smoke test taught us:**
- 28 percent `no-test-met` is high. In the examples we read, the model treats test 7 narrowly, for example two different imports or additions meet no test. Tune this on dev once we have labels.
- 5 regions had more than one met test, so the first met rule does matter.
- Output was about 645 tokens per call, more than we guessed, possibly hidden reasoning tokens. This is why the estimate doubled.
- The model quotes evidence in backticks, usually with `OURS:` and `THEIRS:` in front. 187 of 201 quoted pieces appear in the region text, and all pieces match in 53 of 67 labeled regions. See section 6, the validators task.

## 5. How to run things

Setup:
```powershell
pip install -e ".[dev]"
copy .env.example .env
python scripts/make_split.py
```
Fill in your own key in `.env`. The classifier loads it by itself.

Tests:
```powershell
python -m pytest tests
```

A small real run from dev. Check the dry run output before spending:
```powershell
mkdir outputs/smoke
python scripts/make_smoke_input.py outputs/smoke/input.jsonl --regions 100
python -m classifier.cli outputs/smoke/input.jsonl outputs/smoke/luna.jsonl --model hackclub-classify --max-retries 2 --max-calls 300 --delay 1
```

Useful flags on `classifier.cli`:

| Flag | What it does |
|---|---|
| `--max-calls N` | Stops after about N model calls. Run the same command again to resume. |
| `--retry-errors` | Reruns only the `llm-error` regions against one model |
| `--rerun` | Classifies every region in the input again and overwrites those records |
| `--models a,b` | Runs each model into its own output file |
| `--labels path` | Hand labels for the accuracy columns |

A run also stops by itself after 10 model failures in a row, so running out of budget does not fill the output with errors.

Money: 3 dollars per day on Hack Club. Dry run, row count and cost estimate before any bigger run. Ask each other before anything over 1 dollar. Do not use the test set for tuning.

## 6. What each of us does next

### Fatima

Do these in order. Item 2 was the only one the LLM side was waiting on, and its logic part is done.

| # | Task | Why it matters |
|---|---|---|
| 1 | **Check the rule changes made for you** (section 7). Change anything you disagree with. | You own these, and they were merged without your review. |
| 2 | **Done for logic labels (D10).** `validate_logic_test` is built and wired. Still to do: the checks inside `confirm_structural(region, ast_verdict)`, which is wired and returns None for now. | A structural hint stays `unknown` with `ambiguous` until those checks exist. `pipeline.py` needs no change when they land. |
| 3 | `export-shape`, limited to an exported signature change inside the region with `needs_verification` set | Until then, those regions go to the model. |
| 4 | Trace for Stages 0 to 3, and `run_stages_0_to_3` | Required by the design. Labels do not change. |
| 5 | Changed names, with a definition agreed with Aneeza | The resolver reads this. |
| 6 | **Done (D11).** `--no-llm` and `scripts/run_funnel.py`. Still to do: run the funnel on train and dev and record the numbers | Report numbers. `--no-llm` is not the same as `capped`. |
| 7 | Tune the rules on dev | After hand labels. |

### Aneeza

| # | Task | Why it matters |
|---|---|---|
| 1 | Write `scripts/evaluate.py`: accuracy, per label precision and recall, confusion matrix, rules and LLM separately, plus counts of unknown, capped and llm-error | Nothing can be scored without it. |
| 2 | Review D10: the validator checks, `validator-failed` in `unknown_reason`, and source `model` for a confirmed structural hint | Fatima built these without waiting. Change anything you disagree with and record it in `docs/decisions.md`. |
| 3 | Decide whether a taxonomy document exists, or remove the "taxonomy rules 1 to 16" comments | Cleanup. |
| 4 | Build `few_shot.json` from hand labels, with the seven per test answers on each logic example | The logic prompt skips any example without them. Never invent examples. |
| 5 | Tune the prompts on dev, starting with `no-test-met` | Bump the prompt version on every change. |
| 6 | Compare models on dev, and record the choice and cost in `docs/decisions.md` | Use the cheapest model that holds accuracy. |

### Both

| # | Task |
|---|---|
| 1 | **Hand label a dev sample.** This is the biggest remaining job and blocks all tuning. Follow the `label-guidelines` skill. Agree the sample size and who labels what. Suggested: both label a shared 30 to 50 regions first to compare, so tie breaks are settled early. |
| 2 | Decide whether to add agent stratification to the split, **before** item 1 |
| 3 | Confirm the task split in `docs/TEAM_GUIDE.md`, which still calls itself a proposal |
| 4 | Do the full run, after validators, labels and tuning are reviewed |
| 5 | Report final numbers on the test set, once only, per agent too |

Suggested hand label file, `data/labels/dev_labels.jsonl`, one line per region (`data/labels/` is not ignored by git, so it can be committed):
```json
{"pr_key": "o/r#1", "file_path": "src/a.ts", "conflict_index": 0, "true_label": "assignment-override", "notes": "one line reason"}
```
Add `test_answers` (all seven tests with `test_id`, `met` and `evidence`) to any logic example meant for few shot.

### Order and what blocks what

```
Validators (Fatima)  ─────────────┐
Split decision -> Hand labels ─┬──┼─> Tune prompts and models -> Full run -> Test set, once
evaluate.py (Aneeza) ──────────┘  │
Few shot (Aneeza, from labels) ───┘
```
The validators, `evaluate.py` and hand labels can all happen at the same time.

## 7. What Fatima should check first

These went into `rules/`, `tests/rules/` and shared files without Fatima's review, by Aneeza's decision (D8). Any of them can be changed.

| What | Where | The question |
|---|---|---|
| Rename guard: every old name must be declared in the region | `ast_gate.py`, D4 | `rename` fell from 470 to 44 regions. Real renames using destructuring or method parameters now go to the model. Is that too strict? |
| Non-deletion no-marker regions are `unknown` with reason `no-markers` | `no_markers.py`, D4 | Is that the right label? 141 regions. |
| Whole file deletion is `business-logic-conflict`, decided at Stage 1 | `no_markers.py`, D4 | It does not fit the Stage 1 label list in `CLAUDE.md`. |
| `next.config.mjs` style files stay in scope and are treated as code | `out_of_scope.py`, D4 | Should they be `config-schema` instead? |
| Guards apply to every verdict except identical | `ast_gate.py`, D4 | This is wider than the report. A failure only sends the region onward. |
| The 3 old failing tests were updated | `tests/rules/`, D7 | The tests changed, not the code. Are the new expectations right? |
| `route` returns the kind and a reason | `CLAUDE.md` section 10, D5 | This changes the shared contract. |

## 8. Known limits

- **Validators are cheap text checks.** They reject made up evidence, but a passed label is still not proven right (D10).
- **A structural hint never gets a label yet.** It is `unknown` with reason `ambiguous` until `confirm_structural` has checks. The pipeline side is wired already.
- `DisjointEdits` cannot check for a joint use outside the region, because the data has no surrounding lines.
- `confluent-interference` is recorded as `unknown` for the same reason.
- The call ceiling of 50 per file is our choice. A region that starts below it finishes, so a file can pass it slightly. If every region in a file uses two calls, this caps 103 regions in 8 files.
- The smoke test records name the alias `hackclub-classify`. New records store the real model name.
- The agent is not in the dataset, so a per agent table needs `filtered_prs.csv`.

## 9. Working together

- Branches: `aneeza` and `fatima`, one per person. Start yours from `main`: `git fetch origin`, then `git switch -c fatima origin/main`.
- Own folders can change freely. For shared files, tell the other person what changed (`docs/TEAM_GUIDE.md` section 5).
- `rules` never imports `llm`, and `llm` never imports `rules`. Only `pipeline.py` calls both.
- Run all the test suites after every change and report the result honestly.
- Record every choice the report is silent on in `docs/decisions.md`, and update `docs/PROGRESS.md` when a task moves.
