# Builds the final text sent to the model from the prompt templates, the few shot examples and the region
# load_few_shot reads few_shot.json and format_examples lays out the hand labeled examples, which only the logic prompt receives
# build_system gives the router prompt no examples and the logic prompt its examples, and system_prompt_hash hashes the result for provenance
# build_user_message and every example share one layout with the file path, the base or a note on why it is missing, both sides and the AST evidence

import hashlib
import json

from classifier.llm.prompts import FEW_SHOT_PATH, LOGIC_TESTS, MAX_EXAMPLE_CHARS, PROMPT_A, PROMPT_B
from classifier.schema import BASE_EMPTY, BASE_PRESENT, find_base_state, strip_family

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


def base_block(base_state, base_text):
    # Tells the model how to read the base, an empty base differs from a missing one
    if base_state == BASE_PRESENT:
        return f"BASE:\n{base_text}"
    return EMPTY_BASE_NOTE if base_state == BASE_EMPTY else NO_BASE_NOTE


def message_text(file_path, base, ours, theirs, evidence):
    # One layout for the real message and for every example, so the model sees the same shape in both
    return (f"File path: {file_path}\n\n{base}\n\n"
            f"OURS:\n{ours}\n\nTHEIRS:\n{theirs}\n\n"
            f"AST evidence:\n{json.dumps(evidence)}")


def _show(ex, answer):
    # Each side is shortened, but the base note is the same one a real message gets
    base_text = ex.get("base")
    base = base_block(find_base_state({"base_text": base_text}), _clip(base_text))
    evidence = ex.get("ast_equivalence") or {"equivalence": "not_analyzed"}
    body = message_text(ex.get("file_path"), base, _clip(ex.get("ours")), _clip(ex.get("theirs")), evidence)
    return f"{body}\n\nANSWER: {json.dumps(answer)}"


def format_examples(examples):
    # Only examples hand labeled with all seven answers are shown, because the answers cannot be derived from a label
    blocks = []
    for ex in examples:
        if strip_family(ex.get("true_label")) in LOGIC_TESTS and ex.get("test_answers"):
            blocks.append(f"Example {len(blocks) + 1}:\n" + _show(ex, {"tests": ex["test_answers"]}))
    return "Examples from labeled data:\n\n" + "\n\n".join(blocks) if blocks else ""


def build_system(prompt, examples=None):
    # The router gets no examples, because the hand labels are nearly all logic labels and would teach it to always answer semantic
    if prompt == "A":
        return PROMPT_A.strip()
    examples = load_few_shot() if examples is None else examples
    return PROMPT_B.replace("<<EXAMPLES>>", format_examples(examples)).strip()


def system_prompt_hash(prompt):
    # Hashes one final system prompt including its few shot examples
    return hashlib.sha256(build_system(prompt).encode("utf-8")).hexdigest()


def describe_base(region):
    return base_block(region.base_state, region.base_text)


def build_user_message(region, eq=None):
    evidence = ({"equivalence": eq.equivalence, "renames": eq.renames, "changed_nodes": eq.changed_nodes}
                if eq is not None else {"equivalence": "not_analyzed"})
    return message_text(region.file_path, describe_base(region), region.ours_text, region.theirs_text, evidence)
