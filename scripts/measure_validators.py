# read only measurement of the validators on the smoke test records
# it shows how many of the model answers each check lets through, no model calls

import argparse
import json
from collections import defaultdict

from check_evidence import first_met, load_regions

from classifier.rules.validators import CHECKS, evidence_is_real, validate_logic_test


def short(text, limit=300):
    text = text or ""
    return text if len(text) <= limit else text[:limit] + " ...cut"


def main():
    parser = argparse.ArgumentParser(description="Run the validators on the smoke test records")
    parser.add_argument("--output-file", default="outputs/smoke/luna.jsonl")
    parser.add_argument("--input-file", default="outputs/smoke/input.jsonl")
    parser.add_argument("--show", type=int, default=3)
    args = parser.parse_args()

    regions = load_regions(args.input_file)
    stats = defaultdict(lambda: {"records": 0, "evidence": 0, "check": 0, "both": 0})
    failures = defaultdict(list)

    with open(args.output_file, encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            step, _ = first_met(record["classifier"].get("trace", []))
            if step is None:
                continue
            key = (record["pr_key"], record["file_path"], record["conflict_index"])
            region = regions[key]
            test = step["test"]
            evidence = step.get("evidence")
            real = evidence_is_real(region, evidence)
            check = CHECKS[test](region) if test in CHECKS else False
            row = stats[test]
            row["records"] += 1
            row["evidence"] += int(real)
            row["check"] += int(check)
            row["both"] += int(validate_logic_test(region, test, evidence))
            if real and not check:
                failures[test].append((evidence, region))

    print(f"{'test':26s} {'records':>8s} {'evidence ok':>12s} {'check ok':>9s} {'both':>6s}")
    for test, row in sorted(stats.items()):
        print(f"{test:26s} {row['records']:8d} {row['evidence']:12d} {row['check']:9d} {row['both']:6d}")
    total = sum(row["records"] for row in stats.values())
    passed = sum(row["both"] for row in stats.values())
    print(f"\nPassed both checks: {passed} of {total}")

    print("\nRecords where the evidence was real but the test check failed:")
    for test, rows in failures.items():
        for evidence, region in rows[: args.show]:
            print(f"--- {test}")
            print("evidence:", short(evidence))
            print("OURS:", short(region.ours_text))
            print("THEIRS:", short(region.theirs_text))
            print()


if __name__ == "__main__":
    main()