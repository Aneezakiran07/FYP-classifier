# Team guide: how Aneeza and Fatima work on the classifier

Who owns what, what each folder does, and who does which task. Keep it in the repo at `docs/team_guide.md`.
Two files outrank it: `docs/classifier_design_from_report.md` (the report design) and `CLAUDE.md`.
Dataset decisions live in `docs/decisions.md`.

**Short version.** Aneeza does the LLM side: prompts, prompt tuning, parsing, providers, few shot examples.
Fatima does the rules side: Stages 0 to 3, the AST engine, patterns and validators.
`pipeline.py`, `cli.py`, `report.py` and `schema.py` are shared and need both of us to agree.

## 1. Ground rules
- The report design is the source of truth. If code and report disagree, the report wins. Ask before changing the report design.
- If the report and the code are both silent, we ask each other. We do not guess.
- Never read, print, copy or commit `.env`. Use `.env.example` as the template.
- Do not set `ANTHROPIC_API_KEY` in the shell that runs Claude Code.
- The dev set is for tuning. The test set is touched only once, for the final numbers.
- Run `pytest tests/rules`, `pytest tests/llm` and `pytest tests/test_pipeline.py` after every change and report the result honestly. Do not edit a test just to make it pass.
- Code comments are plain English sentences. No dashes, arrows or symbols, no end punctuation, one space after the hash.
- Keep functions small with plain English names.

## 2. Who owns what

| Area | Owner | Can change alone? |
|---|---|---|
| `src/classifier/llm/` | Aneeza | yes |
| `tests/llm/` | Aneeza | yes |
| `src/classifier/rules/` | Fatima | yes |
| `tests/rules/` | Fatima | yes |
| `schema.py`, `pipeline.py`, `cli.py`, `report.py` | shared | no, both must agree first |
| `tests/test_pipeline.py`, `docs/`, `CLAUDE.md`, `.claude/skills/` | shared | no |
| `scripts/` | whoever wrote the script | yes, but tell the other |

The one hard boundary: **rules never imports llm and llm never imports rules.** Only `pipeline.py` calls both.
If you need something from the other side, ask for a function in the contract below. Do not import it.

## 3. What each folder does

**`src/classifier/rules/` (Fatima, Stages 0 to 3, no LLM)**
- `ast_diff.py` compares two sides as syntax trees and returns one of seven verdicts.
- `ast_gate.py` maps AST verdicts to labels.
- `patterns/` has one file per rule. The ordered `PATTERNS` list is in `patterns/__init__.py`.
- `validators.py` (to be written) holds the deterministic checks that confirm an LLM answer.

**`src/classifier/llm/` (Aneeza, Stage 4, the only LLM stage)**
- `prompts.py` holds the router prompt and the logic tests prompt.
- `prompt_builder.py` builds the system and user messages and loads few shot examples.
- `providers.py` is the single entry point for Gemini, Claude, DeepSeek, OpenAI and Hack Club models.
- `parsing.py` turns raw model replies into dictionaries and rejects bad shapes.
- `classify_llm.py` is the model call loop with retries and the two prompt flow.
- `few_shot.json` holds the examples used in the prompts.

**Shared files in `src/classifier/`**
- `schema.py`: Region, Result, TestAnswer, label constants, status constants.
- `pipeline.py`: Stages 0 to 5, call ceiling, trace building, record writing, resume.
- `cli.py`: command line entry point.
- `report.py`: per layer counts and the accuracy table.

**Everything else**
- `data/samples/`, `data/labels/`, `data/splits/`, `data/raw/`: data. Big files are gitignored, so share them outside git. The final dataset is `data/raw/final_dataset.jsonl` with 4,119 PRs.
- `outputs/`: classifier output, not committed.
- `scripts/`: helper scripts. Scripts may import from both sides.
- `docs/`: this guide, the report design, decisions.
- `.claude/skills/`: `report-check`, `run-classifier`, `label-guidelines`.

## 4. The contract between our two sides
`pipeline.py` is the only caller. Both sides keep these signatures stable.

| Function | Side | Returns |
|---|---|---|
| `rules.run_stages_0_to_3(region)` | rules | a Result, or None meaning go to Stage 4 |
| `llm.route(region, ast_verdict)` | llm | structural, semantic or unknown |
| `llm.run_logic_tests(region, ast_verdict)` | llm | 7 TestAnswer objects with test_id, met, evidence |
| `rules.confirm_structural(region, ast_verdict)` | rules | a structural label or None |
| `rules.validate_logic_test(region, test_id, evidence)` | rules | True or False |

Design points from the report that both of us must respect:
- Stage 4 uses a router prompt first. For semantic regions a 7 logic tests prompt runs in fixed order. The first met test wins and the validator confirms it. **The model never assigns a label itself.**
- `capped` and `llm-error` are statuses with no label.
- confluent-interference is recorded as unknown while context lines are unavailable.
- One record per region, joined by `pr_key` plus `conflict_index`. Our block is overwritten on rerun and runs are resumable.

## 5. How we change shared files
1. Say in chat which shared file you want to change and why.
2. The other person agrees, or says what they need.
3. One person makes the change and runs all three test suites.
4. The other person reviews before it is merged.

## 6. Task division (Phase 2)
This is a proposal. It becomes final when both of us confirm it. Steps use the numbers from the Phase 2 plan.

### Aneeza: LLM side
| Task | Plan step | What it means |
|---|---|---|
| A1 Router prompt | 4 | structural, semantic or unknown, with a short reason. Tune on the dev set. |
| A2 Logic tests prompt | 4 | seven tests in fixed order. The model answers each test with evidence. Returns 7 TestAnswer objects. The pipeline picks the first met test, not the model. |
| A3 Evidence format | 5 (input) | for each of the 7 tests, write down exactly what the model must quote as evidence. Hand this to Fatima so she can build the validators. |
| A4 Parsing and retries | 6 | strict parsing of both prompts. A bad answer after the allowed retries becomes status llm-error with no label. |
| A5 Providers | 6 | clean failure types and the max retries limit, so a failed call is recorded as llm-error. |
| A6 Provenance | 1 | model name and prompt hash written into the classifier block. |
| A7 Few shot examples | 4 | build `few_shot.json` from hand labeled dev examples. Never invent examples. |
| A8 Prompt tuning | 4 | smoke test about 100 rows on one cheap model, then compare models on the dev set. Record the choices in `docs/decisions.md`. |
| A9 LLM tests | all | tests in `tests/llm/` use a fake provider. No real API calls. |

### Fatima: rules side
| Task | Plan step | What it means |
|---|---|---|
| F1 Stage 0 and 1 | 2 | scope, identity and base checks. The trace records every test, including skipped ones, each with a reason. |
| F2 Run stages 0 to 3 | 2 | `rules.run_stages_0_to_3(region)` returns a Result or None. |
| F3 Export-shape pattern | 3 | limited to detecting an exported signature change inside the region with needs_verification set. Ask before going further. |
| F4 Validators | 5 | `rules.validate_logic_test` and `rules.confirm_structural`. Propose the checks first, then agree them with Aneeza. Minimum: cited evidence must literally appear in ours or theirs, plus one cheap token check per test. |
| F5 Changed names | 7 | changed names from the AST engine go into the record. |
| F6 Funnel script | 8 | `scripts/run_funnel.py` counts, per pattern and per stage, how many regions are decided without the LLM and how many reach Stage 4. |
| F7 Rules tuning | all | tune patterns on the dev set. Decide what to do with the 3 tests that already fail (see section 9). |
| F8 Rules tests | all | tests in `tests/rules/`. |

### Shared, with a lead and a reviewer
| Task | Plan step | Lead | Reviewer |
|---|---|---|---|
| S1 Output block and `schema.py` types | 1 | Aneeza | Fatima |
| S2 capped status, the per file call ceiling, llm-error in the pipeline | 6 | Aneeza | Fatima |
| S3 Confirming test, empty joint use lines, confluent-interference as unknown | 7 | Aneeza | Fatima |
| S4 `--no-llm` flag in `cli.py` | 8 | Fatima | Aneeza |
| S5 `scripts/make_split.py` (split by pr_key, seeded, stratified) | after 8 | Aneeza | Fatima |
| S6 `scripts/evaluate.py` (accuracy, per label precision and recall, confusion matrix, rules part and LLM part separately) | after 8 | Aneeza | Fatima, for the rules part |
| S7 Hand labeling of the dev set | before tuning | both | each checks the other on ties |

## 7. Order of work and how to work in parallel
1. Both read the gap list from Phase 2 and confirm it together.
2. First agree S1 and the contract in section 4, including the Result and TestAnswer shapes. After that we can work in parallel, because each side only has to match the contract.
3. In parallel:
   - Fatima: F1, F2, F3.
   - Aneeza: A1, A2, A3, A4, A5.
4. Then F4 (validators) uses A3 (evidence format). This is the one place where we depend on each other, so agree it in chat.
5. Then S2, S3, S4, F5, F6, A6.
6. Then S5 and S6, then hand labeling and tuning on the dev set (A7, A8, F7).
7. Test set only at the end, for the final numbers.

Each side tests against the contract with fakes. Aneeza uses a fake provider and a made up region. Fatima uses plain regions with no model.

## 8. Running the classifier (the `run-classifier` skill)
Follow this order and stop to review after each step.
1. Rules only funnel: `scripts/run_funnel.py` with the no LLM flag. Report how many regions each pattern and stage decides and how many reach Stage 4.
2. Smoke test: about 100 rows, one cheap model, a max retries limit.
3. Full run only after the first two are reviewed. Start from an empty output file. It resumes if it stops.
4. Evaluate with `scripts/evaluate.py` on the dev labels while tuning. Use the test labels only for the final numbers.

Report accuracy for the rules part and the LLM part separately, plus counts of unknown, capped and llm-error.

## 9. Open decisions for both of us
- The 3 tests that already fail in the original code: a stale assertion of 11 patterns (there are 14), and two whitespace cases where the pattern layer now fires before the AST gate. These are rules tests, so Fatima decides whether to update the tests or change the code.
- Which person labels which part of the dev set.
- The proposed lead and reviewer split in section 6.

## 10. Hand labeling
Follow the `label-guidelines` skill. One label per region. When two labels fit, apply the stage order: scope, identity, shape, boundary, then logic. Write a one line reason for every label. Record agreed tie breaks in `.claude/skills/label-guidelines/SKILL.md`.

## 11. Using Claude Code on this repo
Each of us opens the repo in our own editor and runs our own Claude Code session. At the start of a session, say which person you are and which tasks are yours, for example:

> I am Aneeza and I own src/classifier/llm. My tasks are A1 to A9 in docs/team_guide.md. Do not edit src/classifier/rules. Start with task A1.

Fatima does the same with her tasks F1 to F8. Shared files need the agreement process in section 5.
