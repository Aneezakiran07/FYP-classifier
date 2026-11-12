# Read only comparison of an old and a new validators module on the model answers saved in a run, with no model calls
# It keeps train and dev records only and refuses the test split, because validators are tuned on dev and the test split is scored once
# For each model record it repeats the first met test selection from the trace and runs validate_logic_test from both modules
# It prints how many answers pass with each version per test, lists newly passing and newly failing answers and marks dev hand labels

# read only, it never writes a file
# the old module is loaded from another source folder, such as the run folder that holds the run commit

import argparse
import importlib.util
import json
import os
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from classifier.llm.prompts import LOGIC_TESTS  # noqa: E402
from classifier.rules import validators as new_validators  # noqa: E402
from classifier.schema import Region  # noqa: E402

DEFAULT_DATASET = str(ROOT / "data" / "raw" / "final_dataset.jsonl")
DEFAULT_SPLIT_FILE = str(ROOT / "data" / "splits" / "split.jsonl")
DEFAULT_LABELS = [str(ROOT / "data" / "labels" / name) for name in
                  ("dev_labels.jsonl", "dev_labels_batch2.jsonl", "dev_labels_batch3.jsonl")]
ALLOWED_SPLITS = ("train", "dev")
# confluent interference never reaches the validator, the pipeline makes it unknown first
NO_VALIDATOR_TEST = "confluent-interference"


def load_old_validators(old_src):
    # Loads validators.py from another source folder as its own module so both versions can run side by side
    path = Path(old_src) / "classifier" / "rules" / "validators.py"
    if not path.exists():
        raise SystemExit(f"{path} does not exist, pass the src folder of the old code")
    spec = importlib.util.spec_from_file_location("old_validators", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_jsonl(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def allowed_pr_keys(split_file, splits):
    return {row["pr_key"] for row in read_jsonl(split_file) if row.get("split") in splits}


def record_key(record):
    return (record.get("pr_key"), record.get("file_path"), record.get("effective_index"))


def read_regions(dataset_path, wanted):
    regions = {}
    with open(dataset_path, "r", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            if row.get("pr_key") not in {key[0] for key in wanted}:
                continue
            for position, raw in enumerate(row.get("regions", [])):
                region = Region.from_raw(row.get("pr_key"), position, raw)
                if region.key in wanted:
                    regions[region.key] = region
    return regions


def read_hand_labels(paths):
    labels = {}
    for path in paths:
        if not os.path.exists(path):
            continue
        for row in read_jsonl(path):
            if row.get("true_label"):
                labels[(row["pr_key"], row["file_path"], row["conflict_index"])] = (row.get("number"), row["true_label"])
    return labels


def first_met_answer(record):
    # The first test the model marked as met, taken from the saved trace, or None
    block = record.get("classifier") or {}
    if block.get("source") != "model":
        return None
    trace = block.get("trace") or []
    router = next((entry for entry in trace if entry.get("test") == "router"), None)
    if router is None or router.get("answer") != "semantic":
        return None
    answers = [entry for entry in trace if entry.get("test") in LOGIC_TESTS]
    if [entry["test"] for entry in answers] != list(LOGIC_TESTS):
        return None
    return next((entry for entry in answers if entry.get("met")), None)


def compare(records, regions, old_module):
    # Returns counts per test and the answers whose result changed
    counts, changed = Counter(), []
    for record in records:
        answer = first_met_answer(record)
        if answer is None or answer["test"] == NO_VALIDATOR_TEST:
            continue
        region = regions.get(record_key(record))
        if region is None:
            continue
        old = old_module.validate_logic_test(region, answer["test"], answer.get("evidence"))
        new = new_validators.validate_logic_test(region, answer["test"], answer.get("evidence"))
        counts[(answer["test"], old, new)] += 1
        if old != new:
            changed.append((record_key(record), answer["test"], old, new, answer.get("evidence") or ""))
    return counts, changed


def short(text, limit):
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit] + "..."


def print_report(counts, changed, labels, show, limit):
    tests = sorted({test for test, _, _ in counts}, key=list(LOGIC_TESTS).index)
    print(f"{'test':26s} {'answers':>8s} {'old pass':>9s} {'new pass':>9s} {'newly pass':>11s} {'newly fail':>11s}")
    totals = Counter()
    for test in tests:
        row = {key: counts[(test, *key)] for key in ((True, True), (True, False), (False, True), (False, False))}
        answers = sum(row.values())
        old_pass, new_pass = row[(True, True)] + row[(True, False)], row[(True, True)] + row[(False, True)]
        print(f"{test:26s} {answers:8d} {old_pass:9d} {new_pass:9d} {row[(False, True)]:11d} {row[(True, False)]:11d}")
        totals.update({"answers": answers, "old": old_pass, "new": new_pass,
                       "up": row[(False, True)], "down": row[(True, False)]})
    print(f"{'all':26s} {totals['answers']:8d} {totals['old']:9d} {totals['new']:9d} {totals['up']:11d} {totals['down']:11d}")
    for title, wanted in (("Newly passing", True), ("Newly failing", False)):
        members = [item for item in changed if item[3] == wanted]
        print(f"\n{title}: {len(members)}")
        for key, test, _, _, evidence in members[:show]:
            mark = ""
            if key in labels:
                number, true_label = labels[key]
                mark = f"  [hand labeled region {number}: {true_label}]"
            print(f"  {key[0]} | {key[1]} | {key[2]} | {test}{mark}")
            print(f"      evidence: {short(evidence, limit)}")
    labeled = [item for item in changed if item[0] in labels]
    print(f"\nChanged answers with a dev hand label: {len(labeled)}")
    for key, test, old, new, _ in labeled:
        number, true_label = labels[key]
        verdict = "now passes" if new else "now fails"
        print(f"  region {number}: selected {test}, {verdict}, hand label {true_label}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Compare old and new validators on saved model answers, train and dev only")
    parser.add_argument("records_path", help="Output jsonl of a classifier run")
    parser.add_argument("--old-src", required=True, help="src folder of the old code, such as ../run-d16/src")
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--split-file", default=DEFAULT_SPLIT_FILE)
    parser.add_argument("--splits", default="train,dev", help="Comma separated, train and dev only")
    parser.add_argument("--labels", nargs="*", default=DEFAULT_LABELS, help="Dev hand label files")
    parser.add_argument("--show", type=int, default=10, help="Examples shown per list")
    parser.add_argument("--snippet", type=int, default=200, help="Characters of evidence shown")
    args = parser.parse_args(argv)

    splits = [name.strip() for name in args.splits.split(",") if name.strip()]
    if not splits or any(name not in ALLOWED_SPLITS for name in splits):
        parser.error("only train and dev are allowed, the test split is scored once and never used to tune validators")
    old_module = load_old_validators(args.old_src)
    keep = allowed_pr_keys(args.split_file, splits)
    records = [record for record in read_jsonl(args.records_path) if record.get("pr_key") in keep]
    regions = read_regions(args.dataset, {record_key(record) for record in records})
    counts, changed = compare(records, regions, old_module)
    print(f"Records in {', '.join(splits)}: {len(records)}, model answers with a met test checked: {sum(counts.values())}")
    print_report(counts, changed, read_hand_labels(args.labels), args.show, args.snippet)
    return counts, changed


if __name__ == "__main__":
    main()
