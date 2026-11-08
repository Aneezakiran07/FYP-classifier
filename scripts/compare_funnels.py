# Read only comparison of two rules only funnel runs that lists every region whose label changed
# It joins the two rules.jsonl files on pr_key, file_path and effective_index, and a region with no record counts as Reached Stage 4
# group_changes groups the changed regions by old and new label and explain_change names the batch 1 fix of D14 that can cause each one
# print_report shows each group with counts, example keys, snippets and dev hand labels, and flags every change no fix explains

# read only comparison of two funnel outputs, it never writes a file
# marker regions and no marker records are shown apart as the report asks

import argparse
import json
import os
from collections import Counter, defaultdict

from classifier.pipeline import read_records
from classifier.rules.patterns.out_of_scope import is_generated_path
from classifier.schema import BASE_EMPTY, BASE_NO_MARKERS, BASE_PRESENT, Region

REACHED_STAGE_4 = "Reached Stage 4"
UNEXPLAINED = "UNEXPLAINED"
DEFAULT_LABEL_FILES = ("data/labels/dev_labels.jsonl", "data/labels/dev_labels_batch2.jsonl")
TEMPLATE_SUBSTITUTION = "${"
LINE_STARTS_A2 = ("(", "[", "`")


def read_regions(input_path):
    # Every region of the funnel input, keyed the same way as the records
    regions = {}
    with open(input_path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            for position, raw in enumerate(record.get("regions", [])):
                region = Region.from_raw(record.get("pr_key"), position, raw)
                regions.setdefault(region.key, region)
    return regions


def read_hand_labels(paths):
    # Hand labels use the conflict index, which is the effective index of a marker region
    labels = {}
    for path in paths:
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                row = json.loads(line)
                if row.get("true_label"):
                    key = (row["pr_key"], row["file_path"], row["conflict_index"])
                    labels[key] = (os.path.basename(path), row.get("number"), row["true_label"])
    return labels


def outcome(record):
    # The label and the deciding rule of one region, a missing record means Stage 4
    if record is None:
        return REACHED_STAGE_4, None
    block = record["classifier"]
    if block.get("status") != "classified":
        return block.get("status"), block.get("confirming_test")
    label = block.get("label")
    if label == "unknown" and block.get("unknown_reason"):
        label = f"unknown ({block['unknown_reason']})"
    return label, block.get("confirming_test")


def has_template_substitution(region):
    return any("`" in text and TEMPLATE_SUBSTITUTION in text for text in (region.ours_text, region.theirs_text))


def has_line_that_continues(region):
    # A line starting with a parenthesis, a bracket or a backtick joins the line above without a semicolon
    for text in (region.ours_text, region.theirs_text):
        for line in text.splitlines()[1:]:
            if line.lstrip().startswith(LINE_STARTS_A2):
                return True
    return False


def explain_change(region, old, new):
    # Names the batch 1 fix that can cause this change, or UNEXPLAINED
    old_label, old_rule = old
    new_label, _ = new
    if new_label == "unknown (out-of-scope)" and is_generated_path(region.file_path):
        return "C2"
    if new_label == "one-side-change" and region.base_state == BASE_EMPTY:
        return "B1" if old_label == REACHED_STAGE_4 else "B1, taken from another rule"
    if old_label == "disjoint-edits" and new_label == REACHED_STAGE_4 and region.base_state == BASE_PRESENT:
        return "A3"
    if old_label == "formatting" and old_rule == "formatting_only":
        fixes = [name for name, found in (("A1", has_template_substitution(region)),
                                          ("A2", has_line_that_continues(region))) if found]
        return " or ".join(fixes) if fixes else UNEXPLAINED
    return UNEXPLAINED


def snippet(text, limit):
    text = " ".join((text or "").split())
    return text if len(text) <= limit else text[:limit] + "..."


def group_changes(regions, base_records, new_records):
    # Changed regions grouped by population, then old and new label
    groups = defaultdict(list)
    rule_only = Counter()
    for key, region in regions.items():
        old = outcome(base_records.get(key))
        new = outcome(new_records.get(key))
        population = "no marker records" if region.base_state == BASE_NO_MARKERS else "marker regions"
        if old[0] == new[0]:
            if old[1] != new[1]:
                rule_only[(population, old[0], old[1], new[1])] += 1
            continue
        groups[(population, old[0], new[0])].append((region, explain_change(region, old, new)))
    return groups, rule_only


def print_group(old_label, new_label, members, labels, examples, limit):
    reasons = Counter(reason for _, reason in members)
    typescript = sum(1 for region, _ in members if (region.file_path or "").endswith((".ts", ".tsx")))
    flag = "  <<< not explained by any batch 1 fix" if UNEXPLAINED in reasons else ""
    print(f"\n{old_label}  to  {new_label}: {len(members)} regions, {typescript} in .ts or .tsx{flag}")
    print("  explained by: " + ", ".join(f"{reason} {count}" for reason, count in reasons.most_common()))
    labeled = [(region, labels[region.key]) for region, _ in members if region.key in labels]
    for region, (source, number, true_label) in labeled:
        print(f"  hand labeled: {source} region {number}, true label {true_label}, {region.file_path}")
    shown = sorted(members, key=lambda member: member[1] != UNEXPLAINED)[:examples]
    for region, reason in shown:
        pr_key, file_path, index = region.key
        print(f"  [{reason}] {pr_key} | {file_path} | {index} | base {region.base_state}")
        if region.base_state == BASE_PRESENT:
            print(f"      base:   {snippet(region.base_text, limit)}")
        print(f"      ours:   {snippet(region.ours_text, limit)}")
        print(f"      theirs: {snippet(region.theirs_text, limit)}")


def print_report(base_dir, new_dir, regions, groups, rule_only, labels, examples, limit):
    changed = sum(len(members) for members in groups.values())
    print(f"Base run: {base_dir}")
    print(f"New run:  {new_dir}")
    print(f"Regions compared: {len(regions)}, label changed: {changed}")
    unexplained = 0
    for population in ("marker regions", "no marker records"):
        keys = sorted((key for key in groups if key[0] == population), key=lambda key: -len(groups[key]))
        print(f"\n=== {population}, {sum(len(groups[key]) for key in keys)} changed")
        for key in keys:
            print_group(key[1], key[2], groups[key], labels, examples, limit)
            unexplained += sum(1 for _, reason in groups[key] if reason == UNEXPLAINED)
    if rule_only:
        print("\n=== same label, different deciding rule")
        for (population, label, old_rule, new_rule), count in rule_only.most_common():
            print(f"  {population}: {label}, {old_rule} to {new_rule}: {count}")
    print("\n=== totals by fix")
    totals = Counter(reason for members in groups.values() for _, reason in members)
    for reason, count in totals.most_common():
        print(f"  {reason}: {count}")
    print(f"\nRegions no batch 1 fix explains: {unexplained}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="List every region whose label differs between two funnel runs, read only")
    parser.add_argument("base_dir", help="Funnel folder of the earlier run, such as outputs/funnel_base")
    parser.add_argument("new_dir", help="Funnel folder of the new run")
    parser.add_argument("--labels", nargs="*", default=list(DEFAULT_LABEL_FILES), help="Dev hand label files")
    parser.add_argument("--examples", type=int, default=3, help="Example regions shown per group")
    parser.add_argument("--snippet", type=int, default=160, help="Characters shown per side")
    args = parser.parse_args(argv)

    base_input = os.path.join(args.base_dir, "input.jsonl")
    new_input = os.path.join(args.new_dir, "input.jsonl")
    regions = read_regions(new_input)
    if set(read_regions(base_input)) != set(regions):
        parser.error("the two runs read different regions, so their records cannot be compared")
    base_records = read_records(os.path.join(args.base_dir, "rules.jsonl"))
    new_records = read_records(os.path.join(args.new_dir, "rules.jsonl"))
    groups, rule_only = group_changes(regions, base_records, new_records)
    print_report(args.base_dir, args.new_dir, regions, groups, rule_only,
                 read_hand_labels(args.labels), args.examples, args.snippet)
    return groups


if __name__ == "__main__":
    main()
