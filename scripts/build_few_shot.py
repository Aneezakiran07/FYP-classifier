import argparse
import json

from classifier.llm.prompts import FEW_SHOT_PATH, SUBTYPES
from classifier.rules.ast_diff import compute_ast_equivalence

# Reads the hand labels and the raw regions, keeps up to two real examples
# per subtype and writes few_shot_examples.json, nothing is ever invented


def region_key(pr_key, file_path, conflict_index):
    return (pr_key, file_path, conflict_index)


def main():
    parser = argparse.ArgumentParser(description="Build few_shot_examples.json from labeled data")
    parser.add_argument("input_path")
    parser.add_argument("labels_path")
    parser.add_argument("--out", default=FEW_SHOT_PATH)
    parser.add_argument("--per-subtype", type=int, default=2)
    args = parser.parse_args()

    regions = {}
    with open(args.input_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            for region in record.get("regions", []):
                key = region_key(record.get("pr_key"), region.get("file_path"), region.get("conflict_index"))
                regions[key] = region

    picked = {subtype: [] for subtype in SUBTYPES}
    with open(args.labels_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            label = json.loads(line)
            true_label = label.get("true_label")
            key = region_key(label.get("pr_key"), label.get("file_path"), label.get("conflict_index"))
            region = regions.get(key)
            if true_label not in picked or region is None or len(picked[true_label]) >= args.per_subtype:
                continue
            ours, theirs = region.get("ours_text") or "", region.get("theirs_text") or ""
            eq = compute_ast_equivalence(label.get("file_path"), ours, theirs)
            picked[true_label].append({
                "file_path": label.get("file_path"),
                "ours": ours,
                "theirs": theirs,
                "ast_equivalence": {"equivalence": eq.equivalence, "renames": eq.renames,
                                    "changed_nodes": eq.changed_nodes},
                "true_label": true_label,
                "notes": label.get("notes"),
            })

    examples = [ex for subtype in SUBTYPES for ex in picked[subtype]]
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(examples, f, indent=2)
    print(f"Wrote {len(examples)} examples to {args.out}")
    for subtype in SUBTYPES:
        if len(picked[subtype]) < args.per_subtype:
            print(f"Gap, {subtype} has {len(picked[subtype])} of {args.per_subtype} examples")


if __name__ == "__main__":
    main()
