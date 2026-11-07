# Builds the few shot example file for the prompts from real hand labeled regions, nothing is invented
# main reads the dataset regions and one or more hand label files, matched by pull request, file path and conflict index
# For each logic label it keeps up to a set number of examples with base, both sides, the guarded AST verdict, notes and per test answers
# A label is skipped when its seven answers are incomplete, its first met test is not the label, or the prompt would cut off its quotes

import argparse
import json

from classifier.llm.parsing import parse_test_answer
from classifier.llm.prompt_builder import _clip
from classifier.llm.prompts import FEW_SHOT_PATH, LOGIC_TESTS
from classifier.rules.ast_diff import compute_ast_equivalence
from classifier.rules.ast_gate import apply_guards
from classifier.rules.validators import AST_KIND, quoted_pieces, squeeze
from classifier.schema import strip_family

SIDES = ("base_text", "ours_text", "theirs_text")


def region_key(pr_key, file_path, conflict_index):
    return (pr_key, file_path, conflict_index)


def read_regions(input_path):
    regions = {}
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            for region in record.get("regions", []):
                key = region_key(record.get("pr_key"), region.get("file_path"), region.get("conflict_index"))
                regions[key] = region
    return regions


def read_labels(labels_paths):
    # Files are read in the order given so a later batch adds to an earlier one
    labels = []
    for path in labels_paths:
        with open(path, "r", encoding="utf-8") as f:
            labels.extend(json.loads(line) for line in f if line.strip())
    return labels


def answers_problem(answers, true_label):
    # Returns why the answers cannot be shown as an example, or None when they can
    # Each answer must pass the parser that checks a model reply, so an example never shows a shape the model may not give
    if not isinstance(answers, list) or len(answers) != len(LOGIC_TESTS):
        return "the seven test answers are not all there"
    if any(parse_test_answer(item, test_id) is None for item, test_id in zip(answers, LOGIC_TESTS)):
        return "a test answer is empty, out of order or has no evidence"
    first_met = next((item["test_id"] for item in answers if item["met"]), None)
    if first_met != true_label:
        return f"the first met test is {first_met}, not the label"
    return None


def hidden_quotes(answers, region):
    # Lists the quotes of met tests that fall outside the part of each side the prompt shows
    shown = [squeeze(_clip(region.get(side))) for side in SIDES]
    hidden = []
    for item in answers:
        if not item["met"]:
            continue
        for piece in quoted_pieces(item["evidence"]):
            if not AST_KIND.match(piece) and not any(squeeze(piece) in text for text in shown):
                hidden.append(piece)
    return hidden


def build_example(label, true_label, region):
    # The verdict goes through the same guards as in the pipeline so the example shows what the model sees in a run
    ours, theirs = region.get("ours_text") or "", region.get("theirs_text") or ""
    eq = apply_guards(compute_ast_equivalence(label.get("file_path"), ours, theirs), ours, theirs)
    return {
        "file_path": label.get("file_path"),
        "base": region.get("base_text"),
        "ours": ours,
        "theirs": theirs,
        "ast_equivalence": {"equivalence": eq.equivalence, "renames": eq.renames,
                            "changed_nodes": eq.changed_nodes},
        "true_label": true_label,
        "notes": label.get("notes"),
        "test_answers": label.get("test_answers"),
    }


def describe(label):
    return f"label {label.get('number', '?')} {label.get('file_path')}"


def pick_examples(labels, regions, per_subtype):
    picked = {subtype: [] for subtype in LOGIC_TESTS}
    for label in labels:
        true_label = strip_family(label.get("true_label"))
        region = regions.get(region_key(label.get("pr_key"), label.get("file_path"), label.get("conflict_index")))
        if true_label not in picked or region is None or len(picked[true_label]) >= per_subtype:
            continue
        problem = answers_problem(label.get("test_answers"), true_label)
        if problem is None:
            hidden = hidden_quotes(label["test_answers"], region)
            if hidden:
                problem = f"the prompt cuts off quoted text {hidden}"
        if problem:
            print(f"Skipped {describe(label)}, {problem}")
            continue
        picked[true_label].append(build_example(label, true_label, region))
    return picked


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build few_shot.json from hand labeled data")
    parser.add_argument("input_path")
    parser.add_argument("labels_paths", nargs="+", help="One or more hand label files, read in order")
    parser.add_argument("--out", default=FEW_SHOT_PATH)
    parser.add_argument("--per-subtype", type=int, default=2)
    args = parser.parse_args(argv)

    picked = pick_examples(read_labels(args.labels_paths), read_regions(args.input_path), args.per_subtype)
    examples = [ex for subtype in LOGIC_TESTS for ex in picked[subtype]]
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(examples, f, indent=2)
    print(f"Wrote {len(examples)} examples to {args.out}")
    for subtype in LOGIC_TESTS:
        if len(picked[subtype]) < args.per_subtype:
            print(f"Gap, {subtype} has {len(picked[subtype])} of {args.per_subtype} examples")


if __name__ == "__main__":
    main()
