# Start here

The starting point for Aneeza and Fatima, as of 2026-11-08. It says what exists, what the numbers are, and who does what next.

Read this first. Then read `CLAUDE.md` (the design and the rules) and `docs/decisions.md` (every choice made so far, D1 to D15). `docs/PROGRESS.md` is the live checklist, so update that one as work moves.

## 1. Where we are

**The full run is going.** It started on 2026-11-08 on Aneeza's machine with GPT-6 Luna and the `logic-v2` prompt, and takes about 4 days at about 2.5 dollars a day.

**The first accuracy number exists, and it is low.** On batch 1 (30 dev regions) the classifier gets 16 of 30 right, and the model part 15 of 29. This is a small sample, tuned and scored on the same regions.

Most misses are not the model's fault:

| Cause of a miss on batch 1 | Count | Fix |
|---|---|---|
| The true label is one only the rules can write | 8 | Rules: D12 value-only, DisjointEdits on an empty base, `confirm_structural` |
| The model was right and the validator rejected it | 2 | Validator, listed in D15 |
| The model shortened a quote | 1 | Small prompt fix, after the run |
| The model was wrong or the label is disputed | about 3 | Prompt, tie break or model |

**What is still needed for trustworthy numbers:** batch 3 labels, the rule and validator fixes, labels for regions the rules decide, and `filtered_prs.csv` for the per agent table.

## 2. How a region moves through the classifier

There is one command, and the rules and the model both run inside it. The regions the rules cannot decide go to the model automatically.

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

## 3. What exists

### Rules, `src/classifier/rules/` (Fatima)
| Part | State |
|---|---|
| `ast_diff.py`, the AST engine with 7 verdicts | Working, template string and semicolon fixes in D14 |
| `ast_gate.py`, verdicts to labels, with the guards | Working. A failed guard means content changed. |
| `patterns/`, 14 patterns in stage order | Working. Generated files out of scope (D14) |
| `validators.py`, `validate_logic_test` | Working (D10). Gaps in D15: JSX child, return type annotation, nested backticks |
| `confirm_structural` | Wired, always returns None, so a structural hint ends `unknown` (ambiguous) |
| `export-shape`, trace for Stages 0 to 3, `run_stages_0_to_3`, changed names | **Missing** |

### LLM, `src/classifier/llm/` (Aneeza)
| Part | State |
|---|---|
| `prompts.py` | `router-v1` and `logic-v2` (D15) |
| `prompt_builder.py`, `parsing.py`, `classify_llm.py`, `providers.py` | Working. Retries follow D13. Default model `hackclub-classify` |
| `few_shot.json` | Empty on purpose. 7 built examples wait in `few_shot_candidates.json` (D15) |

### Shared
| Part | State |
|---|---|
| `schema.py`, `pipeline.py`, `cli.py`, `report.py` | Working, with `--no-llm` (D11) |

### Scripts
| Script | What it does |
|---|---|
| `make_split.py` | The seeded train, dev and test split |
| `make_smoke_input.py` | A random set of regions that reach the model, train or dev only |
| `run_funnel.py` | The rules only funnel, no model calls |
| `compare_funnels.py`, `explain_disjoint.py` | Compare two funnels, explain one DisjointEdits decision (Fatima, D14) |
| `build_few_shot.py` | Builds few shot examples from hand labels with all seven answers |
| `evaluate.py` | Scores a run against hand labels: rules and model apart, by stage, per label precision and recall, confusion matrix, misses. Leaves out few shot examples, and the test split unless `--final` |
| `revalidate.py` | Applies the current rules and validators to a finished run with no model calls, into a new file |

### Tests
All pass with no real API calls: 259 in `tests/rules`, `tests/llm` and `tests/test_pipeline.py`, 313 in the whole folder.

### Not in git
- `.env`: your own keys. Never read, print or commit it.
- `data/raw/`, `data/splits/split.jsonl`, `outputs/`: each of us keeps our own copy. Send changed files to the other person and compare `Get-FileHash`.

## 4. Hand labels, `data/labels/` (in git)

| File | Regions | Purpose | State |
|---|---|---|---|
| `dev_labels.jsonl`, `to_label.md` | 1 to 30, random, under 1,500 characters | Scoring | Drafted with AI help, reviewed by Aneeza |
| `dev_labels_batch2.jsonl`, `to_label_batch2.md`, `review_batch2.md` | 31 to 60, picked by text filters | Few shot only, never accuracy | Drafted with AI help, reviewed by Aneeza |
| `dev_labels_batch3.jsonl`, `to_label_batch3.md` | 61 to 110, random, under 1,500 characters | Scoring | Fatima labels all 50 by hand without AI. Aneeza also labels 61 to 70 separately to measure agreement |

All three batches are regions that reach the model, so there is no accuracy for the rules part yet. A batch of regions the rules decide is still needed.

Report the labels as "drafted with AI help, reviewed by the authors" for batches 1 and 2, and "labeled by hand" for batch 3.

## 5. The numbers

All figures describe `final_dataset.jsonl` (4,119 pull requests, 36,589 records). The report describes a larger population of 4,266, so always say which one a figure uses.

- **Rules funnel, train and dev** (D14, `funnel_d14c`): 30,355 marker regions, 11,893 reach Stage 4.
- **Split:** by `pr_key`, seed 20261105, 70, 15 and 15 percent, stratified by file count bucket, not by agent.
- **Smoke test:** 100 dev regions, 0 failed calls, about 0.09 dollars.
- **Batch 1:** see section 1 and D15.
- **Full run:** see `docs/PROGRESS.md`.

## 6. How to run things

Setup:
```powershell
pip install -e ".[dev]"
copy .env.example .env
python scripts/make_split.py
```

Tests:
```powershell
python -m pytest tests
```

A small run on chosen regions, then its score:
```powershell
python -m classifier.cli input.jsonl out.jsonl --model hackclub-classify --max-retries 2 --max-calls 80 --delay 1
python scripts/evaluate.py out.jsonl --labels data/labels/dev_labels.jsonl
```

After the full run, apply rule and validator fixes with no model calls:
```powershell
python scripts/revalidate.py outputs/full/luna_v2.jsonl outputs/full/luna_v2_reval.jsonl
```

Useful flags on `classifier.cli`: `--max-calls N` stops after about N calls (run again to resume), `--retry-errors` reruns only `llm-error` regions, `--rerun` overwrites, `--no-llm` skips Stage 4. A run stops by itself after 10 model failures in a row.

Money: 3 dollars per day on Hack Club. Dry run, row count and cost estimate before any bigger run. Ask each other before anything over 1 dollar. Do not use the test set for tuning.

## 7. What each of us does next

### Fatima
| # | Task |
|---|---|
| 1 | Label batch 3 by hand, without AI, in `dev_labels_batch3.jsonl` |
| 2 | Validator gaps from D15: JSX child and return type annotation for assignment-override, nested backticks in quotes |
| 3 | The D12 value-only rule and DisjointEdits on an empty base (batch 2 of the rule review) |
| 4 | Read D15 and the `revalidated_commit` field, and agree or change them |
| 5 | `confirm_structural` checks, `export-shape`, the Stage 0 to 3 trace, changed names |
| 6 | Confirm or change the older rule choices from D4 that may still be open: whole file deletion as business-logic-conflict at Stage 1, `next.config.mjs` treated as code, guards on every verdict except identical, and non deletion no-marker records as `unknown` |

### Aneeza
| # | Task |
|---|---|
| 1 | Keep the full run going: restart each day, check the record count and the `llm-error` count |
| 2 | Label regions 61 to 70 without looking at Fatima's labels |
| 3 | Build a batch of regions the rules decide, for rules accuracy |
| 4 | Find `filtered_prs.csv` for the per agent table |
| 5 | After the run: `revalidate.py`, then `evaluate.py` on batches 1 and 3, then the candidate few shot examples and a second model on batch 3 |

### Both
| # | Task |
|---|---|
| 1 | Compare the two sets of labels for 61 to 70 and settle the tie breaks in the label guidelines |
| 2 | Agree the shared fix: a logic label's reason comes from the selected test's evidence, not the router |
| 3 | Test set, once, per agent too |

## 8. Known limits

- Validators are cheap text checks. They reject made up evidence, but a passed label is not proven right (D10).
- A structural hint never gets a label until `confirm_structural` has checks.
- The data has no lines around a region, so DisjointEdits cannot see a joint use outside it and confluent-interference is always `unknown`.
- The call ceiling of 50 per file is our choice.
- Hand labels cover only short regions (under 1,500 characters), so accuracy describes short regions.
- The agent is not in the dataset, so a per agent table needs `filtered_prs.csv`.

## 9. Working together

- Branches: `aneeza` and `fatima`, one per person, started from `main`.
- Own folders can change freely. For shared files, tell the other person what changed (`docs/TEAM_GUIDE.md` section 5).
- `rules` never imports `llm`, and `llm` never imports `rules`. Only `pipeline.py` calls both.
- Run all the test suites after every change and report the result honestly.
- Record every choice the report is silent on in `docs/decisions.md`, and update `docs/PROGRESS.md` when a task moves.
