# Scores classifier records against hand labels and prints accuracy for the rules part and the model part apart
# It joins records and labels on pull request, file path and conflict index, and leaves out few shot examples and test split labels
# Capped and llm-error regions are counted apart and never scored, and an unknown label is scored like any other label
# It prints accuracy by source and by stage, per label precision and recall, a confusion matrix and the unknown reasons

# read only script that never calls a model
# the test split is refused unless the final flag is given, because test labels are used once for the final numbers
# a label file picked by text filters is not a random sample, so its numbers must not be reported as accuracy

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from classifier.schema import (  # noqa: E402
    LABELS, SOURCE_MODEL, SOURCE_RULE, STATUS_CAPPED, STATUS_CLASSIFIED, STATUS_LLM_ERROR, bare_label,
)

DEFAULT_LABELS = [str(ROOT / "data" / "labels" / "dev_labels.jsonl")]
DEFAULT_FEW_SHOT = ROOT / "src" / "classifier" / "llm" / "few_shot.json"
DEFAULT_SPLIT = ROOT / "data" / "splits" / "split.jsonl"


def region_key(row):
    # The join key from Figure 6.6, never the pull request and conflict index alone
    return (row.get("pr_key"), row.get("file_path"), row.get("conflict_index"))


def read_jsonl(path):
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def read_records(path):
    # Keeps one record per key and refuses a file with duplicates, since each block is written once per key
    records = {}
    for row in read_jsonl(path):
        key = region_key(row)
        if key in records:
            raise SystemExit(f"Duplicate record for {key} in {path}")
        records[key] = row
    return records


def read_labels(paths):
    # Reads label files in order and refuses a key that appears twice or a label outside the taxonomy
    labels, seen, unlabeled = [], set(), 0
    for path in paths:
        for row in read_jsonl(path):
            if not row.get("true_label"):
                unlabeled += 1
                continue
            key = region_key(row)
            if key in seen:
                raise SystemExit(f"Region {key} is labeled twice across {paths}")
            seen.add(key)
            try:
                true_label = bare_label(row["true_label"])
            except ValueError as error:
                raise SystemExit(f"{path}: {error}")
            labels.append({"key": key, "true_label": true_label, "notes": row.get("notes"),
                           "source_file": os.path.basename(path)})
    return labels, unlabeled


def few_shot_signatures(path):
    # A few shot example carries no join key, so it is matched to its label by file path, label and notes
    if not path or not os.path.exists(path):
        return set()
    with open(path, "r", encoding="utf-8") as f:
        examples = json.load(f)
    return {(ex.get("file_path"), ex.get("true_label"), ex.get("notes")) for ex in examples}


def read_test_keys(path):
    # Pull request keys in the test split, or None when the split file is not there
    if not path or not os.path.exists(path):
        return None
    return {row["pr_key"] for row in read_jsonl(path) if row.get("split") == "test"}


def model_name(classifier):
    return (classifier.get("provenance") or {}).get("model_name")


def select_scored(labels, records, few_shot, test_keys, final, model):
    # Splits the labels into the scored ones and counts every reason a label was left out
    scored, left_out = [], Counter()
    for label in labels:
        if (label["key"][1], label["true_label"], label["notes"]) in few_shot:
            left_out["used as a few shot example"] += 1
            continue
        if test_keys is not None and label["key"][0] in test_keys and not final:
            left_out["in the test split, needs --final"] += 1
            continue
        record = records.get(label["key"])
        if record is None:
            left_out["no record in this output"] += 1
            continue
        block = record.get("classifier") or {}
        if model and block.get("source") == SOURCE_MODEL and model_name(block) != model:
            left_out["decided by another model"] += 1
            continue
        scored.append({**label, "block": block})
    return scored, left_out


def ratio(part, whole):
    return f"{part}/{whole} ({100.0 * part / whole:.1f}%)" if whole else f"{part}/0 (n/a)"


def accuracy_rows(items):
    # Accuracy over classified items only, overall and by the source that decided
    rows = []
    for name, source in (("all", None), ("rules", SOURCE_RULE), ("model", SOURCE_MODEL)):
        group = [i for i in items if source is None or i["block"].get("source") == source]
        right = sum(i["block"].get("label") == i["true_label"] for i in group)
        rows.append({"part": name, "correct": right, "scored": len(group)})
    return rows


def stage_rows(items):
    rows = []
    for stage in sorted({i["block"].get("stage") for i in items}, key=lambda s: (s is None, s)):
        group = [i for i in items if i["block"].get("stage") == stage]
        right = sum(i["block"].get("label") == i["true_label"] for i in group)
        rows.append({"stage": stage, "correct": right, "scored": len(group)})
    return rows


def per_label_rows(items):
    # Precision is right over predicted and recall is right over true, for every label that appears on either side
    true_counts = Counter(i["true_label"] for i in items)
    predicted_counts = Counter(i["block"].get("label") for i in items)
    right_counts = Counter(i["true_label"] for i in items if i["block"].get("label") == i["true_label"])
    rows = []
    for label in LABELS:
        if not true_counts[label] and not predicted_counts[label]:
            continue
        rows.append({"label": label, "true": true_counts[label], "predicted": predicted_counts[label],
                     "correct": right_counts[label],
                     "precision": right_counts[label] / predicted_counts[label] if predicted_counts[label] else None,
                     "recall": right_counts[label] / true_counts[label] if true_counts[label] else None})
    return rows


def confusion(items):
    # Rows are the true labels and columns are the predicted labels, both in Table 5.1 order
    pairs = Counter((i["true_label"], i["block"].get("label")) for i in items)
    used = [label for label in LABELS if any(label in pair for pair in pairs)]
    return {"labels": used, "counts": [[pairs[(t, p)] for p in used] for t in used]}


def evaluate(records, labels, unlabeled, few_shot, test_keys, final=False, model=None):
    scored, left_out = select_scored(labels, records, few_shot, test_keys, final, model)
    statuses = Counter(i["block"].get("status") for i in scored)
    classified = [i for i in scored if i["block"].get("status") == STATUS_CLASSIFIED]
    unknown_reasons = Counter(i["block"].get("unknown_reason") or "none given"
                              for i in classified if i["block"].get("label") == "unknown")
    return {
        "labels_read": len(labels), "labels_without_true_label": unlabeled,
        "left_out": dict(left_out), "considered": len(scored),
        "classified": statuses[STATUS_CLASSIFIED], "capped": statuses[STATUS_CAPPED],
        "llm_error": statuses[STATUS_LLM_ERROR],
        "accuracy": accuracy_rows(classified), "by_stage": stage_rows(classified),
        "per_label": per_label_rows(classified), "confusion": confusion(classified),
        "predicted_unknown_reasons": dict(unknown_reasons),
        "true_unknown": sum(i["true_label"] == "unknown" for i in classified),
        "models": dict(Counter(model_name(i["block"]) for i in classified
                               if i["block"].get("source") == SOURCE_MODEL)),
        "misses": [{"key": list(i["key"]), "true": i["true_label"], "predicted": i["block"].get("label"),
                    "stage": i["block"].get("stage"), "unknown_reason": i["block"].get("unknown_reason")}
                   for i in classified if i["block"].get("label") != i["true_label"]],
    }


def short(value):
    return "n/a" if value is None else f"{value:.2f}"


def print_summary(result, records_path, label_paths, model):
    print(f"Records: {records_path}")
    print(f"Labels:  {', '.join(label_paths)}")
    if model:
        print(f"Model filter: {model}")
    print(f"\nHand labels read: {result['labels_read']}, rows with no true label yet: {result['labels_without_true_label']}")
    for reason, count in sorted(result["left_out"].items()):
        print(f"  left out, {reason}: {count}")
    print(f"Regions considered: {result['considered']}")
    print(f"  classified {result['classified']}, capped {result['capped']}, llm-error {result['llm_error']}")
    print("  capped and llm-error are counted here only and never scored")

    print("\nAccuracy on classified regions")
    for row in result["accuracy"]:
        print(f"  {row['part']:<6} {ratio(row['correct'], row['scored'])}")
    print("\nBy stage")
    for row in result["by_stage"]:
        print(f"  stage {row['stage']}  {ratio(row['correct'], row['scored'])}")
    if result["models"]:
        print(f"\nModel decided regions by model: {result['models']}")

    print("\nPer label")
    print(f"  {'label':<26}{'true':>6}{'pred':>6}{'right':>7}{'prec':>7}{'recall':>8}")
    for row in result["per_label"]:
        print(f"  {row['label']:<26}{row['true']:>6}{row['predicted']:>6}{row['correct']:>7}"
              f"{short(row['precision']):>7}{short(row['recall']):>8}")

    print(f"\nUnknown: {result['true_unknown']} true, predicted reasons {result['predicted_unknown_reasons']}")

    matrix = result["confusion"]
    if matrix["labels"]:
        print("\nConfusion matrix, rows are true and columns are predicted")
        for n, label in enumerate(matrix["labels"]):
            print(f"  {n:>2} {label}")
        print("     " + "".join(f"{n:>4}" for n in range(len(matrix["labels"]))))
        for n, row in enumerate(matrix["counts"]):
            print(f"  {n:>2} " + "".join(f"{c if c else '.':>4}" for c in row))

    if result["misses"]:
        print("\nMisses")
        for miss in result["misses"]:
            reason = f" ({miss['unknown_reason']})" if miss["unknown_reason"] else ""
            print(f"  {miss['key'][0]} {miss['key'][1]} #{miss['key'][2]}: true {miss['true']}, "
                  f"predicted {miss['predicted']}{reason}, stage {miss['stage']}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Score classifier records against hand labels")
    parser.add_argument("records_path", help="Output jsonl written by the classifier")
    parser.add_argument("--labels", nargs="+", default=DEFAULT_LABELS, help="Hand label files, read in order")
    parser.add_argument("--few-shot", default=str(DEFAULT_FEW_SHOT),
                        help="Few shot file whose examples are left out of scoring")
    parser.add_argument("--keep-few-shot", action="store_true", help="Score few shot examples too")
    parser.add_argument("--split-file", default=str(DEFAULT_SPLIT))
    parser.add_argument("--final", action="store_true", help="Allow test split labels, for the final numbers only")
    parser.add_argument("--model", default=None, help="Score only model decisions made by this model name")
    parser.add_argument("--json-out", default=None, help="Also write the numbers to this json file")
    args = parser.parse_args(argv)

    test_keys = read_test_keys(args.split_file)
    if test_keys is None:
        print(f"Warning: no split file at {args.split_file}, test split labels cannot be detected")
    labels, unlabeled = read_labels(args.labels)
    few_shot = set() if args.keep_few_shot else few_shot_signatures(args.few_shot)
    result = evaluate(read_records(args.records_path), labels, unlabeled, few_shot, test_keys,
                      final=args.final, model=args.model)
    print_summary(result, args.records_path, args.labels, args.model)
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f"\nWrote {args.json_out}")
    return result


if __name__ == "__main__":
    main()
