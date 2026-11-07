# Builds the final text sent to the model from the prompt templates, the few shot examples and the region
# load_few_shot reads few_shot.json and format_examples shows router examples for prompt A and per test examples for prompt B
# build_system fills the examples into a prompt and system_prompt_hash hashes the result for provenance
# build_user_message gives the file path, the base or a note that it is empty or missing, both sides and the AST evidence

import hashlib
import json

from classifier.llm.prompts import (
    FEW_SHOT_PATH, LOGIC_TESTS, MAX_EXAMPLE_CHARS, PROMPT_A, PROMPT_B, STRUCTURAL_LABELS,
)
from classifier.schema import BASE_EMPTY, BASE_PRESENT, strip_family

# Turns the prompt strings and the few shot json into the final system messages

EMPTY_BASE_NOTE = "BASE: empty. Both sides are additions, neither side edited existing text here."
NO_BASE_NOTE = "BASE: not available. The direction of change is unknown."


def load_few_shot(path=FEW_SHOT_PATH):
    # A missing or broken file just means the prompts run with no examples
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return []
    return data if isinstance(data, list) else []


def _clip(text):
    text = text or ""
    return text if len(text) <= MAX_EXAMPLE_CHARS else text[:MAX_EXAMPLE_CHARS] + "..."


def _show(ex, answer):
    ast = json.dumps(ex.get("ast_equivalence", {}))
    base = f"BASE: {_clip(ex['base'])}\n" if ex.get("base") else ""
    return (f"File: {ex.get('file_path')}\n{base}OURS: {_clip(ex.get('ours'))}\nTHEIRS: {_clip(ex.get('theirs'))}\n"
            f"AST: {ast}\nANSWER: {json.dumps(answer)}")


def format_examples(examples, prompt):
    # The router learns the kind from every example
    # The logic prompt only shows examples hand labeled in the per test format
    blocks = []
    for ex in examples:
        label, note = strip_family(ex.get("true_label")), ex.get("notes") or "matches the hand label"
        if prompt == "A" and label in LOGIC_TESTS:
            blocks.append(_show(ex, {"kind": "semantic", "reason": note}))
        elif prompt == "A" and label in STRUCTURAL_LABELS:
            blocks.append(_show(ex, {"kind": "structural", "reason": note}))
        elif prompt == "B" and label in LOGIC_TESTS and ex.get("test_answers"):
            blocks.append(_show(ex, {"tests": ex["test_answers"]}))
    return "Examples from labeled data:\n\n" + "\n\n".join(blocks) if blocks else ""


def build_system(prompt, examples=None):
    text = PROMPT_A if prompt == "A" else PROMPT_B
    examples = load_few_shot() if examples is None else examples
    return text.replace("<<EXAMPLES>>", format_examples(examples, prompt)).strip()


def system_prompt_hash(prompt):
    # Hashes one final system prompt including its few shot examples
    return hashlib.sha256(build_system(prompt).encode("utf-8")).hexdigest()


def describe_base(region):
    # Tells the model how to read the base, an empty base differs from a missing one
    if region.base_state == BASE_PRESENT:
        return f"BASE:\n{region.base_text}"
    return EMPTY_BASE_NOTE if region.base_state == BASE_EMPTY else NO_BASE_NOTE


def build_user_message(region, eq=None):
    evidence = ({"equivalence": eq.equivalence, "renames": eq.renames, "changed_nodes": eq.changed_nodes}
                if eq is not None else {"equivalence": "not_analyzed"})
    return (f"File path: {region.file_path}\n\n{describe_base(region)}\n\n"
            f"OURS:\n{region.ours_text}\n\nTHEIRS:\n{region.theirs_text}\n\n"
            f"AST evidence:\n{json.dumps(evidence)}")
