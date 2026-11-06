# read only review of the rename guard, no model calls and nothing is changed
# it finds regions the parser calls a rename and shows which ones the guard rejects and why

import argparse
import json
import os
import random
import re
from collections import Counter, defaultdict

from classifier.rules.ast_diff import compute_ast_equivalence
from classifier.rules.ast_gate import is_declared_in_region, is_named_export, passes_guards
from classifier.schema import Region

DEFAULT_DATASET = "data/raw/final_dataset.jsonl"
DEFAULT_OUTPUT = "outputs/rename_review.txt"


def old_names(eq):
    # The renames can be a dict or a set, either way the old names are what we loop over
    renames = eq.renames
    if hasattr(renames, "keys"):
        return list(renames.keys())
    return list(renames)


def why_not_declared(name, text):
    # A rough guess at the form that the guard does not read, so we can count them
    escaped = re.escape(name)
    if re.search(rf"\b(?:const|let|var)\s*[{{\[][^=;]*\b{escaped}\b", text):
        return "destructuring"
    if re.search(rf"\bcatch\s*\(\s*{escaped}\b", text):
        return "catch parameter"
    if re.search(rf"\bimport\b[^;]*\b{escaped}\b", text):
        return "imported name"
    if re.search(rf"\b[\w$]+\s*\([^()]*\b{escaped}\b[^()]*\)\s*(?::[^{{;=]+)?\{{", text):
        return "looks like a method or callback parameter"
    if re.search(rf"(?<![\w$]){escaped}\s*\(", text) or re.search(rf"\.{escaped}(?![\w$])", text):
        return "only called or used as a property"
    return "other"




def pick_group(ours, theirs, names):
    # Returns the outcome and the reason for one rename region, in the same order as the gate
    if not passes_guards(ours, theirs):
        return "failed the newline or directive guard", "no rename check needed"
    exported = [name for name in names if is_named_export(name, ours)]
    if exported:
        return "rejected by the rename guard", "a named export"
    missing = [name for name in names if not is_declared_in_region(name, ours)]
    if missing:
        return "rejected by the rename guard", why_not_declared(missing[0], ours)
    return "kept as rename", "all old names are local"


def review_region(region):
    if not region.file_path.endswith((".ts", ".tsx")):
        return None
    eq = compute_ast_equivalence(region.file_path, region.ours_text, region.theirs_text)
    if eq.equivalence != "identifier_rename_only":
        return None
    ours = region.ours_text or ""
    theirs = region.theirs_text or ""
    names = old_names(eq)
    outcome, reason = pick_group(ours, theirs, names)
    return {
        "group": f"{outcome} / {reason}",
        "pr_key": region.pr_key,
        "file_path": region.file_path,
        "names": names,
        "ours": ours,
        "theirs": theirs,
    }


def short(text, limit=500):
    return text if len(text) <= limit else text[:limit] + " ...cut"


def write_examples(rows, per_group, seed, path):
    by_group = defaultdict(list)
    for row in rows:
        by_group[row["group"]].append(row)
    rng = random.Random(seed)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for group, group_rows in sorted(by_group.items()):
            f.write(f"===== {group} ({len(group_rows)} regions) =====\n\n")
            for row in rng.sample(group_rows, min(per_group, len(group_rows))):
                f.write(f"pr {row['pr_key']}  file {row['file_path']}\n")
                f.write(f"old names {row['names']}\n")
                f.write("OURS:\n" + short(row["ours"]) + "\n")
                f.write("THEIRS:\n" + short(row["theirs"]) + "\n\n")

def keys_outside_test(split_file):
    # Pull requests in the test split are left out so the test set stays untouched
    with open(split_file, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    return {row["pr_key"] for row in rows if row["split"] != "test"}

def main():
    parser = argparse.ArgumentParser(description="Review what the rename guard keeps and rejects")
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--max-prs", type=int, default=0, help="only read this many pull requests, 0 means all")
    parser.add_argument("--per-group", type=int, default=8)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()
    allowed = keys_outside_test("data/splits/split.jsonl")
    rows = []
    with open(args.dataset, encoding="utf-8") as f:
        for number, line in enumerate(f):
            if args.max_prs and number >= args.max_prs:
                break
            record = json.loads(line)
            if record["pr_key"] not in allowed:
                continue
            for position, raw in enumerate(record.get("regions", [])):
                row = review_region(Region.from_raw(record["pr_key"], position, raw))
                if row:
                    rows.append(row)

    print(f"Regions the parser calls a rename before the guard: {len(rows)}")
    for group, count in sorted(Counter(row["group"] for row in rows).items(), key=lambda item: -item[1]):
        print(f"  {count:6d}  {group}")
    write_examples(rows, args.per_group, args.seed, args.output)
    print(f"Examples written to {args.output}")


if __name__ == "__main__":
    main()