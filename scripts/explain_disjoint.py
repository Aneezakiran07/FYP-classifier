# Read only helper that prints one region in full and every name set the DisjointEdits rule computes for it
# It finds the region by pr_key, file_path and conflict index in the input.jsonl of a funnel folder
# explain shows the changed base lines, the declared, referenced and deleted names of each side and which check stops the label
# It is for reading DisjointEdits decisions by hand and never writes a file

import argparse
import json
import os

from classifier.rules.patterns.base import ClassifyInput
from classifier.rules.patterns.disjoint_edits import (
    _JSX_EXTENSIONS,
    DisjointEdits,
    _changed_line_indices,
    _changed_line_text,
    _declared_names,
    _deleted_names,
    _identifiers,
    _locally_declared,
    _removed_base_lines,
    _split_lines,
)


def find_region(input_path, pr_key, file_path, index):
    with open(input_path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("pr_key") != pr_key:
                continue
            for raw in record.get("regions", []):
                if raw.get("file_path") == file_path and raw.get("conflict_index") == index:
                    return raw
    return None


def show_text(title, text):
    print(f"----- {title} -----")
    print("(missing)" if text is None else text if text else "(empty)")


def side_sets(base_lines, side_lines, jsx):
    changed = _changed_line_text(base_lines, side_lines)
    return {
        "touched base lines": sorted(_changed_line_indices(base_lines, side_lines)),
        "declared on changed lines": sorted(_declared_names(changed, jsx)),
        "referenced on changed lines": sorted(_identifiers(changed)),
        "declared on deleted or replaced base lines": sorted(_declared_names(_removed_base_lines(base_lines, side_lines), jsx)),
        "still declared locally": sorted(_locally_declared(side_lines, jsx)),
        "deleted names": sorted(_deleted_names(base_lines, side_lines, jsx)),
    }


def explain(raw):
    base, ours, theirs = raw.get("base_text"), raw.get("ours_text") or "", raw.get("theirs_text") or ""
    for title, text in (("BASE", base), ("OURS", ours), ("THEIRS", theirs)):
        show_text(title, text)
    if not base:
        print("\nNo base or an empty base, DisjointEdits does not run")
        return
    base_lines = _split_lines(base)
    jsx = (raw.get("file_path") or "").lower().endswith(_JSX_EXTENSIONS)
    sets = {"ours": side_sets(base_lines, _split_lines(ours), jsx),
            "theirs": side_sets(base_lines, _split_lines(theirs), jsx)}
    for side, values in sets.items():
        print(f"\n===== {side} =====")
        for name, value in values.items():
            print(f"  {name}: {value}")
    o, t = sets["ours"], sets["theirs"]
    print("\n===== checks =====")
    print(f"  1 overlapping base lines: {sorted(set(o['touched base lines']) & set(t['touched base lines']))}")
    print(f"  2 declared by both: {sorted(set(o['declared on changed lines']) & set(t['declared on changed lines']))}")
    print(f"  3 ours uses what theirs declares: {sorted(set(o['referenced on changed lines']) & set(t['declared on changed lines']))}")
    print(f"  3 theirs uses what ours declares: {sorted(set(t['referenced on changed lines']) & set(o['declared on changed lines']))}")
    print(f"  3 ours uses what theirs deleted: {sorted(set(o['referenced on changed lines']) & set(t['deleted names']))}")
    print(f"  3 theirs uses what ours deleted: {sorted(set(t['referenced on changed lines']) & set(o['deleted names']))}")
    h = ClassifyInput(raw.get("file_path"), ours, theirs, base_text=base)
    print(f"\nDisjointEdits fires: {DisjointEdits().detect(h)}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Print one region and the DisjointEdits name sets, read only")
    parser.add_argument("funnel_dir", help="Funnel folder whose input.jsonl holds the region")
    parser.add_argument("pr_key")
    parser.add_argument("file_path")
    parser.add_argument("conflict_index", type=int)
    args = parser.parse_args(argv)
    raw = find_region(os.path.join(args.funnel_dir, "input.jsonl"), args.pr_key, args.file_path, args.conflict_index)
    if raw is None:
        parser.error("no region with that pr_key, file_path and conflict index")
    explain(raw)


if __name__ == "__main__":
    main()
