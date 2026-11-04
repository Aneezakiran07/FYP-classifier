# AST Git Resolver

Merge conflict classifier for AI agent pull requests on TypeScript.
The report design in docs/classifier_design_from_report.md is the source of truth.

## Layout
- src/classifier/rules/ owned by Fatima, stages 0 to 3, AST engine, patterns, validators
- src/classifier/llm/ owned by Aneeza, prompts, providers, reply parsing, few shot examples
- src/classifier/pipeline.py, cli.py, report.py, schema.py shared by both owners
- rules never imports llm and llm never imports rules, only pipeline.py calls both
- tests/rules, tests/llm and tests/test_pipeline.py
- data/samples, data/labels, data/splits, data/raw and outputs
- scripts/ for helper scripts such as build_few_shot.py

## Setup
- copy .env.example to .env and fill in only the keys you need
- pip install -e ".[dev,providers]"

## Run
- single model: python -m classifier.cli data/samples/sample_input.jsonl outputs/out.jsonl --model gemini-3.5-flash-lite
- multi model: python -m classifier.cli data/samples/sample_input.jsonl outputs/out.jsonl --models gemini-3.5-flash-lite,claude-haiku-4-5
- tests: pytest tests/rules and pytest tests/llm and pytest tests/test_pipeline.py
- rebuild few shot examples: python scripts/build_few_shot.py <input.jsonl> <labels.jsonl>

## Notes carried over from the flat version
The text below is the original README and its file names and commands refer to the old flat layout.

---

# Classifier v2: gate first, small prompts second

## What changed from v1
- Three layers now. Text patterns (unchanged), then an AST gate, then the model. The gate labels whitespace, comments, rename and formatting cases with no model call.
- ast_diff.py only gained `ASTEquivalence` and `compute_ast_equivalence()`, a thin wrapper over `build_ast_summary`. Nothing existing was edited.
- The 150 line prompt is gone. Prompt A asks structural, semantic or unknown. Prompt B runs only after semantic and names one of 7 subtypes. Both live in prompts.py (33 lines).
- Output records keep every old field and gain `needs_verification` and `verification_priority` at the end.
- providers.py adds Gemini, Claude and OpenAI style (DeepSeek) calls. A missing SDK or key skips the model with a warning.
- The v1 one line counter is replaced by the per layer report block.
- Extra files: prompt_builder.py (builds system messages from prompts.py plus the json), build_few_shot.py, tests/conftest.py.

## How to run
- Single model: `python classify.py in.jsonl out.jsonl --model gemini-3.5-flash-lite` (or set CLASSIFIER_MODEL).
- Multi model: `python classify.py in.jsonl out.jsonl --models gemini-3.5-flash-lite,gemini-3.5-flash,claude-haiku-4-5,deepseek-r1`. This writes out.<model>.jsonl per model and prints the table.
- Accuracy columns read `sample_labels.jsonl` next to the input, or pass `--labels path`. Use `--max-retries N` so a bad model name gives up instead of retrying forever (default 0 retries forever, as in v1).
- Keys: GEMINI_API_KEY, ANTHROPIC_API_KEY, DEEPSEEK_API_KEY, OPENAI_API_KEY. Aliases: claude-haiku-4-5 and deepseek-r1 map to their full API names in providers.py.
- Tests: `python -m pytest tests/`.

## Swap few-shot examples
- Edit few_shot_examples.json, or rebuild it: `python build_few_shot.py sample_input.jsonl sample_labels.jsonl` (run inside classifier_refactor/). It picks up to 2 real regions per subtype, adds the AST verdict, and prints every gap.
- Format: `{file_path, ours, theirs, ast_equivalence, true_label}` plus an optional `notes` copied from your labels, used as the example reason.

## Results on the sample
- Not measured. sample_labels.jsonl never reached me and my environment cannot reach the model APIs, so I have no accuracy or speed numbers and will not invent them.
- To fill this in: run the multi model command above with your keys. The table gives deterministic share, llm_called, agreed_with_gt and accuracy per model. `overall_acc` covers every labeled region.
- The table only counts regions handled in that run, so start from an empty output file.

## Few-shot gaps
- few_shot_examples.json ships empty, so all 7 subtypes have 0 of 2 real examples: overlap_contamination, confluent_interference, assignment_override, execution_perturbation, type_incompatibility, null_safety_conflict, business_logic_conflict.
- Prompts run zero shot until you run build_few_shot.py, which reports the true gaps.

## Decisions
- Shared examples: one json feeds both prompts. A treats subtype labels as semantic and structural, rename, whitespace, documentation labels as structural. B uses subtype examples only. One place to edit beats a small accuracy gain.
- `not_analyzed` files (md, json, css) go to prompt A too, otherwise nothing could classify them. A can answer unknown.
- Uncertainty: B returning low confidence, other or null gives logic_subtype other and needs_verification true. Priority is high for low confidence, normal for a confident other. A unknown, a call that gave up, or an unparseable reply gives label unknown, needs_verification true, priority high.
- Prompt A structural is labeled structural with medium confidence, and it cannot say rename or documentation.
- Two identical sides (both empty) are labeled whitespace by the gate, as v1 did.
- The gate calls line wrapping whitespace, not structural, because the parser treats wrapping as layout.
- Caveat: Python indentation is not tokens, so the gate can call an indentation change whitespace. Check this on your data.
- Known regression risk: v1 could answer dependency for manifests like package.json. The new prompts cannot, only the lockfile pattern can.
- One region counts as one call toward the per file cap, whether it used A or A and B.
- A model that answers in the wrong shape is retried 3 times, then the region is marked unknown.
- classify_region no longer takes a client because providers.py owns clients.
