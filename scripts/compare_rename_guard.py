# Read only comparison of the old and the new rename guard on every rename region, with no model calls
# It reads TypeScript regions outside the test split that the AST engine calls a rename and that pass the other guards
# old_is_declared and old_is_local_rename keep a copy of the old guard, and is_local_rename from ast_gate is the new one
# main counts regions kept or rejected by both, newly kept or newly rejected, and writes the changed regions to a text file

# compares the old rename guard with the new one on every rename region
# read only, no model calls and nothing in the repo is changed

import argparse
import json
import os
import re

from classifier.rules.ast_diff import compute_ast_equivalence
from classifier.rules.ast_gate import is_local_rename, parameter_names, passes_guards
from classifier.schema import Region

DEFAULT_DATASET = "data/raw/final_dataset.jsonl"
DEFAULT_OUTPUT = "outputs/rename_compare.txt"


def old_is_declared(name, text):
    # A copy of the guard before the change, kept here only for this comparison
    escaped = re.escape(name)
    keyword = rf"\b(?:const|let|var|function|class|type|interface|enum)\s+{escaped}(?![\w$])"
    single_arrow = rf"(?<![\w$.]){escaped}\s*=>"
    if re.search(keyword, text or "") or re.search(single_arrow, text or ""):
        return True
    return name in parameter_names(text)


def old_is_local_rename(eq, ours):
    return all(old_is_declared(name, ours) for name in eq.renames)


def short(text, limit=400):
    return text if len(text) <= limit else text[:limit] + " ...cut"

def keys_outside_test(split_file):
    # Pull requests in the test split are left out so the test set stays untouched
    with open(split_file, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    return {row["pr_key"] for row in rows if row["split"] != "test"}

def main():
    parser = argparse.ArgumentParser(description="Compare the old and new rename guard")
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    counts = {"kept both": 0, "rejected both": 0, "newly kept": 0, "newly rejected": 0}
    changed = {"newly kept": [], "newly rejected": []}
    allowed = keys_outside_test("data/splits/split.jsonl")
    with open(args.dataset, encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            if record["pr_key"] not in allowed:
                continue
            for position, raw in enumerate(record.get("regions", [])):
                region = Region.from_raw(record["pr_key"], position, raw)
                if not region.file_path.endswith((".ts", ".tsx")):
                    continue
                eq = compute_ast_equivalence(region.file_path, region.ours_text, region.theirs_text)
                if eq.equivalence != "identifier_rename_only":
                    continue
                ours = region.ours_text or ""
                theirs = region.theirs_text or ""
                if not passes_guards(ours, theirs):
                    continue
                before = old_is_local_rename(eq, ours)
                after = is_local_rename(eq, ours)
                if before and after:
                    counts["kept both"] += 1
                elif not before and not after:
                    counts["rejected both"] += 1
                elif after:
                    counts["newly kept"] += 1
                    changed["newly kept"].append((region, eq, ours, theirs))
                else:
                    counts["newly rejected"] += 1
                    changed["newly rejected"].append((region, eq, ours, theirs))

    for name, count in counts.items():
        print(f"{count:6d}  {name}")

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        for name, rows in changed.items():
            f.write(f"===== {name} ({len(rows)} regions) =====\n\n")
            for region, eq, ours, theirs in rows:
                f.write(f"pr {region.pr_key}  file {region.file_path}\n")
                f.write(f"old names {list(eq.renames)}\n")
                f.write("OURS:\n" + short(ours) + "\nTHEIRS:\n" + short(theirs) + "\n\n")
    print(f"Changed regions written to {args.output}")


if __name__ == "__main__":
    main()