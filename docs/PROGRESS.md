# Classifier progress

Last updated: 2026-11-05. Update this file whenever a task changes state. `docs/START_HERE.md` has the full picture.

**Goal:** run `data/raw/final_dataset.jsonl` with the LLM stage on, and get a trustworthy label or status for every region.

**Where we are:** roughly 60 percent of the way there. This percentage is a judgment, not a measurement. The classifier runs end to end with a real model. The main gaps are validators and hand labels.

## Phase 2 build order

| Step | What | Owner | State |
|---|---|---|---|
| 1 | Classifier block and `schema.py` | Aneeza | Done |
| - | Rule stage fixes (D4) | Aneeza | Done, Fatima can still change them |
| 2 | Trace for Stages 0 to 3, `run_stages_0_to_3` | Fatima | Not started. Stage 4 has its trace. |
| 3 | `export-shape` | Fatima | Not started |
| 4 | Router and 7 logic tests prompts | Aneeza | Done, not tuned |
| 5 | Validators and `confirm_structural` | Fatima proposes, Aneeza agrees | **Not started, needed before a full run** |
| 6 | `capped`, `llm-error`, retries, temperature zero, truncation | Aneeza | Done |
| 7 | Confirming test, joint use lines, confluent-interference as unknown | Aneeza | Done |
| 7 | Changed names | Fatima | Not started, needs an agreed definition |
| 8 | `--no-llm` and `scripts/run_funnel.py` | Fatima | Not started |
| after 8 | `scripts/make_split.py` | Aneeza | Done |
| after 8 | `scripts/evaluate.py` | Aneeza | Not started |

## Road to the goal

| # | Milestone | Owner | State |
|---|---|---|---|
| 1 | LLM stage code | Aneeza | Done |
| 2 | Budget guard, `--max-calls` and stop after 10 failures in a row | Aneeza | Done |
| 3 | Train, dev and test split | Aneeza | Done, decide on agent stratification before labeling |
| 4 | Smoke test, 100 dev regions | Aneeza | Done, 0 failed calls, about 0.09 dollars |
| 5 | Validators confirm the labels | Fatima | Not started |
| 6 | Evaluation script | Aneeza | Not started |
| 7 | Hand labels for a dev sample | Both | Not started, the biggest remaining job |
| 8 | Few shot examples, with per test answers | Aneeza | Needs item 7 |
| 9 | Tune prompts and rules, compare models on dev | Both | Needs items 5, 6 and 7 |
| 10 | Full run on the dataset | Both | Needs item 9, a dry run and a new cost estimate |
| 11 | Final numbers on the test set, once only | Both | Needs item 10 and test labels |

## Full run estimate

Population: `final_dataset.jsonl`. 14,013 regions reach the model, in 7,140 files.

Scaled from the smoke test on GPT-6 Luna, at listed prices the smoke test did not confirm: about 12 dollars and about 4.5 days without a stop. Few shot examples would add to this. Compare it again after tuning.

## Open questions

- Should the split also be stratified by agent? This needs `filtered_prs.csv` and must be settled before hand labeling.
- How large is the dev sample to hand label, and who labels what?
- Which checks do the validators run? Fatima proposes.
- What counts as a changed name?
- Does a taxonomy document exist, or should the "taxonomy rules 1 to 16" comments go?
- Fatima's checks on the rule changes (`docs/START_HERE.md` section 7).
