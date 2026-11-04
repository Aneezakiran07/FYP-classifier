---
name: run-classifier
description: Run the classifier in the right order and cost safe way, from the rules only funnel to the final evaluation. Use when asked to run, test or evaluate the classifier.
---

Follow this order and stop to show results after each step.
1. Rules only funnel: run scripts/run_funnel.py with the no-llm flag on the input jsonl. Report how many regions each pattern and stage decides and how many reach Stage 4.
2. Smoke test: run about 100 rows with one cheap model and a max retries limit. Check records look sane and few shot examples load.
3. Full run only after the funnel and smoke test are reviewed. Start from an empty output file. The run resumes if it stops.
4. Evaluate with scripts/evaluate.py using the dev labels while tuning, and the test labels only for the final numbers.
Report accuracy for the rules part and the LLM part separately, plus counts of unknown, capped and llm-error.
Never print API keys.

Model and budget: we are still improving the prompts and still finding out which model works best for this classifier, so do not assume a model. The budget is 3 dollars per day on Hack Club AI, plus a 10 dollar reserve for Claude or DeepSeek that stays unused until the final run. Always start with about 100 dev rows on a cheap model with a max retries limit, and check the cost before any bigger run. Ask me before any run that could cost more than 1 dollar. Never use Pro, Opus, Fable or Astra models and never use Latest alias models. Report the model name and the cost of every run.