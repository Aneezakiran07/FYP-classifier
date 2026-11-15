# Classifier progress

Last updated: 2026-11-15. Update this file whenever a task changes state. `docs/START_HERE.md` has the full picture.

**Goal:** run `data/raw/final_dataset.jsonl` with the LLM stage on, and get a trustworthy label or status for every region.

**Where we are:** the full run is finished, joined and revalidated (2026-11-15, D20), and the code is frozen at `5a08ae3`. Every region of the eligible pool has a record. Dev accuracy on batches 1 and 3 is 41 of 80. What is left is FYP-II work: hand labels for the two test sheets and the 61 to 70 agreement check, then the one final scoring, plus the missing classifier parts (export-shape, `confirm_structural`, the rule trace, changed names).

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
| 7 | Hand labels for a dev sample | Both | Batch 1 (30) reviewed. Batch 2 (30, for few shot) reviewed by Aneeza. Batch 3 (50, for scoring) labeled by Fatima by hand, 2026-11-14. Aneeza's second set for regions 61 to 70 is not done, left for FYP-II (D20) |
| 8 | Few shot examples, with per test answers | Aneeza | 7 built, kept off in `few_shot_candidates.json` after no gain on batch 1 (D15) |
| 9 | Tune prompts and rules, compare models on dev | Both | One prompt round (`logic-v2`). Model comparison waits for batch 3 |
| 10 | Full run on the dataset | Both | Done 2026-11-15, joined and revalidated, see below and D20 |
| 11 | Labels for regions the rules decide, so the rules part has an accuracy | Both | The rules test sheet (301 to 350) is drawn and not labeled, left for FYP-II (D20) |
| 12 | Final numbers on the test set, once only, per agent too | Both | Left for FYP-II (D20). Both test sheets are drawn and already classified by the full run, so scoring needs labels only. Per agent still needs `filtered_prs.csv` |

## Full run

| Item | Value |
|---|---|
| Input | `data/raw/final_dataset.jsonl`, 36,589 records, about 14,000 reach the model |
| Output | `outputs/full/luna_v2.jsonl` on Aneeza's machine, git ignored, plus `commit.txt` and `pip_freeze.txt` |
| Code | branch `aneeza`, commit `e025275` until 2026-11-10, then `2d0ab73` (D16 validators) from 2026-11-11. The model input is the same, and `revalidate.py` applies the newest validators to every record after the run |
| Model and prompts | `hackclub-classify` (GPT-6 Luna), `router-v1`, `logic-v2`, no few shot examples |
| Cost estimate | about 0.0006 dollars per model region, about 8 dollars in total, at listed prices not checked word for word |
| Daily cap | `--max-calls 8000`, about 2.5 dollars, then the same command again the next day |
| Speed | about 20 seconds per model region, about 4 days |

No code in `src/` changes on Aneeza's machine until the run ends, because each daily restart loads the code again. Rule and validator fixes are applied after the run with `scripts/revalidate.py`.

### Split of the run, from 2026-11-11

The run is shared so it ends sooner, each half on its own Hack Club key. Both halves use the same code (`2d0ab73`), model, prompts and flags. The split is by whole pull request rows of `final_dataset.jsonl`, never by region, so the keys and the per file call ceiling stay the same. When the split was made, rows 0 to 946 were done (9,853 records), and 10,720 model regions were left.

| Who | Input file | Rows | Model regions left | Output | `Get-FileHash` of the input |
|---|---|---|---|---|---|
| Aneeza | `outputs/full/input_aneeza.jsonl` | 0 to 2642, `24taro/notebooklm-collector#243` to `SwellPatrol/meditation.surf#149` | about 5,360 | `outputs/full/luna_v2.jsonl`, resumed | `BA4392A7B5338C5C57D524B13F634E66ACD9731C588586933AC7E5C0A5B90C5B` |
| Fatima | `outputs/full/input_fatima.jsonl` | 2643 to 4118, `SwellPatrol/meditation.surf#150` to `zxvxl/pet#52` | about 5,360 | `outputs/full/luna_v2_fatima.jsonl`, new | `55AD39BEC78E99E42C3C2727AC74F1E501B7F0884845ACCC19F1648690DBABE2` |

- Both input files are exact line copies of `final_dataset.jsonl` (hash `4E5DC859A66F089A8F70778EB28A152DA73C06900EB5C1A50C65C9D27B187F14`), and joined in order they are byte identical to it.
- Fatima runs from a folder with no rule changes until her half ends.
- After both halves end: check that no key is in both outputs and that the model name, prompt hashes and component version match, join them into a new `luna_v2_merged.jsonl`, then run `revalidate.py` and `evaluate.py` on it. Done on 2026-11-15, see below.

### Run ended, 2026-11-15 (D20)

| Item | Value |
|---|---|
| Joined file | `outputs/full/luna_v2_merged.jsonl`, 36,589 records in the order of `final_dataset.jsonl`, `Get-FileHash` `5F6B19572FA770F5DE0548E9F7037BE302D2C7E25F2A695FAED6E41FC3473CC4` |
| Revalidated file | `outputs/full/luna_v2_reval.jsonl`, rules and validators of `5a08ae3`, `Get-FileHash` `51DAFEB09D43DE2F3661A8A9710E2D7901840ECE7710684B46BD9109501A2944` |
| Reached the model | 14,030 regions (8,671 Aneeza, 5,359 Fatima), 13,931 decided, 99 capped (9 and 90), 0 llm-error after one `--retry-errors` pass on 84 regions |
| Model calls and time | 27,201 calls, about 78 hours of active time (42 and 36), about 20 seconds per model region |
| Revalidation | 242 records changed: 240 validator-failed to a logic label, 2 assignment-override to unknown. No rule decision changed and no region needs the model again |
| Unknown share of decided model regions | 54.6 percent before revalidation, 52.9 percent after (52.4 Aneeza, 53.7 Fatima) |

Both files are git ignored and were made on Aneeza's machine. Send them to Fatima and compare `Get-FileHash`.

## Accuracy so far

Batch 1, 30 dev regions, GPT-6 Luna. Tuned and scored on the same regions, so the gain is optimistic.

| Prompt | All | Model part |
|---|---|---|
| `logic-v1` | 14/30 | 13/29 |
| `logic-v2` | 16/30 | 15/29 |

8 of the 29 model regions have a rule only label the model cannot write.

Final dev numbers, `scripts/evaluate.py` on `luna_v2_reval.jsonl`, 2026-11-15 (D20):

| Sheet | All | Model part |
|---|---|---|
| Batch 1 (tuned on) | 18/30 | 17/29 |
| Batch 3 (not tuned on) | 23/50 | 23/50 |
| Both | 41/80 | 40/79 |

29 of the 36 logic labels the model gave are right. 23 of the 39 misses have a rule only label the model cannot write, 15 of them `disjoint-edits`. No test set number exists yet.

## Open questions

- What counts as a changed name?
- Does a taxonomy document exist, or should the "taxonomy rules 1 to 16" comments go?
- Tie breaks: one side only reformats while the other really changes the code, and whether a component or a test setup block counts as an entity for overlap-contamination.
- Where is `filtered_prs.csv`, which the per agent table needs?
- Fatima to agree `provenance.revalidated_commit`, a new field written by `scripts/revalidate.py`.
