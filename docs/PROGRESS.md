# Classifier progress

Last updated: 2026-11-08. Update this file whenever a task changes state. `docs/START_HERE.md` has the full picture.

**Goal:** run `data/raw/final_dataset.jsonl` with the LLM stage on, and get a trustworthy label or status for every region.

**Where we are:** roughly 52 percent of the way there. This percentage is a judgment, not a measurement. The full run started on 2026-11-08 with GPT-6 Luna and `logic-v2`. The first accuracy number exists (batch 1, 16 of 30). The main gaps are batch 3 labels, the rule and validator fixes, and labels for the rules part.

## Phase 2 build order

| Step | What | Owner | State |
|---|---|---|---|
| 1 | Classifier block and `schema.py` | Aneeza | Done |
| - | Rule stage fixes (D4, D9, D14) | Aneeza, then Fatima | Done, batch 2 of the rule review is open |
| 2 | Trace for Stages 0 to 3, `run_stages_0_to_3` | Fatima | Not started. Stage 4 has its trace. |
| 3 | `export-shape` | Fatima | Not started |
| 4 | Router and 7 logic tests prompts | Aneeza | Done. `router-v1`, `logic-v2` (D15) |
| 5 | Validators and `confirm_structural` | Fatima, Aneeza reviews | Logic validators done (D10). Gaps found in D15. `confirm_structural` always returns None |
| 6 | `capped`, `llm-error`, retries, temperature zero, truncation | Aneeza | Done, retries changed in D13 |
| 7 | Confirming test, joint use lines, confluent-interference as unknown | Aneeza | Done |
| 7 | Changed names | Fatima | Not started, needs an agreed definition |
| 8 | `--no-llm` and `scripts/run_funnel.py` | Fatima, Aneeza reviews | Done (D11), funnel numbers in D14 |
| after 8 | `scripts/make_split.py` | Aneeza | Done |
| after 8 | `scripts/evaluate.py` | Aneeza | Done, 2026-11-08 |
| after 8 | `scripts/revalidate.py`, current rules and validators on a finished run with no model calls | Aneeza | Done, 2026-11-08 |

## Road to the goal

| # | Milestone | Owner | State |
|---|---|---|---|
| 1 | LLM stage code | Aneeza | Done |
| 2 | Budget guard, `--max-calls` and stop after 10 failures in a row | Aneeza | Done |
| 3 | Train, dev and test split | Aneeza | Done, not stratified by agent because `filtered_prs.csv` is missing |
| 4 | Smoke test, 100 dev regions | Aneeza | Done, 0 failed calls, about 0.09 dollars |
| 5 | Validators confirm the labels | Fatima | Done for logic labels, gaps listed in D15 |
| 6 | Evaluation script | Aneeza | Done |
| 7 | Hand labels for a dev sample | Both | Batch 1 (30) reviewed. Batch 2 (30, for few shot) reviewed by Aneeza. Batch 3 (50, for scoring) with Fatima. Regions 61 to 70 to be labeled by both, separately |
| 8 | Few shot examples, with per test answers | Aneeza | 7 built, kept off in `few_shot_candidates.json` after no gain on batch 1 (D15) |
| 9 | Tune prompts and rules, compare models on dev | Both | One prompt round (`logic-v2`). Model comparison waits for batch 3 |
| 10 | Full run on the dataset | Aneeza | Running since 2026-11-08, see below |
| 11 | Labels for regions the rules decide, so the rules part has an accuracy | Both | Not started, all hand labels so far are regions that reach the model |
| 12 | Final numbers on the test set, once only, per agent too | Both | Needs items 10 and 11, test labels and `filtered_prs.csv` |

## Full run

| Item | Value |
|---|---|
| Input | `data/raw/final_dataset.jsonl`, 36,589 records, about 14,000 reach the model |
| Output | `outputs/full/luna_v2.jsonl` on Aneeza's machine, git ignored, plus `commit.txt` and `pip_freeze.txt` |
| Code | branch `aneeza`, commit `e025275` |
| Model and prompts | `hackclub-classify` (GPT-6 Luna), `router-v1`, `logic-v2`, no few shot examples |
| Cost estimate | about 0.0006 dollars per model region, about 8 dollars in total, at listed prices not checked word for word |
| Daily cap | `--max-calls 8000`, about 2.5 dollars, then the same command again the next day |
| Speed | about 20 seconds per model region, about 4 days |

No code in `src/` changes on Aneeza's machine until the run ends, because each daily restart loads the code again. Rule and validator fixes are applied after the run with `scripts/revalidate.py`.

## Accuracy so far

Batch 1, 30 dev regions, GPT-6 Luna. Tuned and scored on the same regions, so the gain is optimistic.

| Prompt | All | Model part |
|---|---|---|
| `logic-v1` | 14/30 | 13/29 |
| `logic-v2` | 16/30 | 15/29 |

8 of the 29 model regions have a rule only label the model cannot write.

## Open questions

- What counts as a changed name?
- Does a taxonomy document exist, or should the "taxonomy rules 1 to 16" comments go?
- Tie breaks: one side only reformats while the other really changes the code, and whether a component or a test setup block counts as an entity for overlap-contamination.
- Where is `filtered_prs.csv`, which the per agent table needs?
- Fatima to agree `provenance.revalidated_commit`, a new field written by `scripts/revalidate.py`.
