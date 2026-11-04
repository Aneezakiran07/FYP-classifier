import json

from classifier.llm.prompts import (
    FEW_SHOT_PATH, MAX_EXAMPLE_CHARS, PROMPT_A, PROMPT_B, STRUCTURAL_LABELS, SUBTYPES,
)

# Turns the prompt strings and the few shot json into the final system messages


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
    return (f"File: {ex.get('file_path')}\nOURS: {_clip(ex.get('ours'))}\nTHEIRS: {_clip(ex.get('theirs'))}\n"
            f"AST: {ast}\nANSWER: {json.dumps(answer)}")


def format_examples(examples, prompt):
    # Prompt A learns the kind from every example, prompt B only from semantic ones
    blocks = []
    for ex in examples:
        label, note = ex.get("true_label"), ex.get("notes") or "matches the hand label"
        if prompt == "A" and label in SUBTYPES + ("logic",):
            blocks.append(_show(ex, {"kind": "semantic", "reason": note}))
        elif prompt == "A" and label in STRUCTURAL_LABELS:
            blocks.append(_show(ex, {"kind": "structural", "reason": note}))
        elif prompt == "B" and label in SUBTYPES:
            blocks.append(_show(ex, {"subtype": label, "confidence": "high", "evidence": note}))
    return "Examples from labeled data:\n\n" + "\n\n".join(blocks) if blocks else ""


def build_system(prompt, examples=None):
    text = PROMPT_A if prompt == "A" else PROMPT_B
    examples = load_few_shot() if examples is None else examples
    return text.replace("<<EXAMPLES>>", format_examples(examples, prompt)).strip()


def build_user_message(file_path, ours_text, theirs_text, eq=None):
    evidence = ({"equivalence": eq.equivalence, "renames": eq.renames, "changed_nodes": eq.changed_nodes}
                if eq is not None else {"equivalence": "not_analyzed"})
    return (f"File path: {file_path}\n\nOURS:\n{ours_text}\n\nTHEIRS:\n{theirs_text}\n\n"
            f"AST evidence:\n{json.dumps(evidence)}")