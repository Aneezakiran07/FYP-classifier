# rules only funnel that runs stages 0 to 3 with the model off and counts what each stage decides
# it makes no model calls and the regions that reach Stage 4 get no record
# it reads train and dev by default and the test split only when asked for the final numbers

import argparse
import contextlib
import json
import os
from collections import Counter

from classifier import pipeline
from classifier.schema import BASE_NO_MARKERS, Region

DEFAULT_DATASET = "data/raw/final_dataset.jsonl"
DEFAULT_SPLIT_FILE = "data/splits/split.jsonl"
DEFAULT_OUTPUT_DIR = "outputs/funnel"
SPLITS = ("train", "dev", "test")
TYPESCRIPT = (".ts", ".tsx")
STAGE_NAMES = {0: "Stage 0 scope", 1: "Stage 1 identity", 2: "Stage 2 shape", 3: "Stage 3 boundary"}
REACHED_STAGE_4 = "Reached Stage 4"


def parse_splits(text, include_test):
    # The test split is read only when the flag says this run is for the final numbers
    splits = [name.strip() for name in text.split(",") if name.strip()]
    unknown = [name for name in splits if name not in SPLITS]
    if unknown or not splits:
        raise ValueError(f"splits must be some of {', '.join(SPLITS)}, got {text!r}")
    if "test" in splits and not include_test:
        raise ValueError("the test split is used only once for the final numbers, add --include-test for that run")
    return splits


def keys_in_splits(split_file, splits):
    with open(split_file, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    return {row["pr_key"] for row in rows if row["split"] in splits}


def write_input(dataset, keys, input_path):
    # Copies the pull requests of the chosen splits so the normal pipeline can read them
    pull_requests = 0
    with open(dataset, encoding="utf-8") as source, open(input_path, "w", encoding="utf-8") as target:
        for line in source:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("pr_key") in keys:
                target.write(json.dumps(record) + "\n")
                pull_requests += 1
    return pull_requests


def read_regions(input_path):
    regions = []
    with open(input_path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            for position, raw in enumerate(record.get("regions", [])):
                regions.append(Region.from_raw(record.get("pr_key"), position, raw))
    return regions


def where_decided(region, records):
    # Returns the stage name, the deciding rule and the label of one region
    record = records.get(region.key)
    if record is None:
        return REACHED_STAGE_4, None, None
    block = record["classifier"]
    return STAGE_NAMES[block["stage"]], block["confirming_test"], block["label"]


def build_funnel(regions, records):
    # Marker regions and no marker records are counted apart, as the report asks
    funnel = {
        "marker_regions": 0, "typescript_regions": 0, "no_marker_records": 0,
        "duplicate_keys": len(regions) - len({region.key for region in regions}),
        "by_stage": Counter(), "by_stage_typescript": Counter(),
        "by_rule": Counter(), "by_rule_typescript": Counter(), "no_marker_labels": Counter(),
    }
    for region in regions:
        stage, rule, label = where_decided(region, records)
        if region.base_state == BASE_NO_MARKERS:
            funnel["no_marker_records"] += 1
            funnel["no_marker_labels"][label or REACHED_STAGE_4] += 1
            continue
        is_typescript = (region.file_path or "").endswith(TYPESCRIPT)
        funnel["marker_regions"] += 1
        funnel["by_stage"][stage] += 1
        if rule is not None:
            funnel["by_rule"][(stage, rule, label)] += 1
        if is_typescript:
            funnel["typescript_regions"] += 1
            funnel["by_stage_typescript"][stage] += 1
            if rule is not None:
                funnel["by_rule_typescript"][(stage, rule, label)] += 1
    return funnel


def share(count, total):
    return f"{count} ({100.0 * count / total:.1f}%)" if total else f"{count} (n/a)"


def stage_order():
    return list(STAGE_NAMES.values()) + [REACHED_STAGE_4]


def print_funnel(funnel, description):
    marker, typescript = funnel["marker_regions"], funnel["typescript_regions"]
    print(f"Population: {description}")
    print(f"Pull requests: {funnel['pull_requests']}, marker regions: {marker} "
          f"({typescript} in .ts or .tsx), no marker records: {funnel['no_marker_records']}")
    if funnel["duplicate_keys"]:
        print(f"Warning, {funnel['duplicate_keys']} regions repeat a key and were counted with the first one")

    print(f"\n{'Marker regions by stage':28s} {'all':>18s} {'.ts and .tsx':>18s}")
    for stage in stage_order():
        print(f"{stage:28s} {share(funnel['by_stage'][stage], marker):>18s} "
              f"{share(funnel['by_stage_typescript'][stage], typescript):>18s}")

    print(f"\n{'Decided by':40s} {'label':26s} {'all':>7s} {'.ts .tsx':>9s}")
    for stage in stage_order()[:-1]:
        rows = sorted((key for key in funnel["by_rule"] if key[0] == stage), key=lambda key: -funnel["by_rule"][key])
        if rows:
            print(stage)
        for key in rows:
            _, rule, label = key
            print(f"  {rule:38s} {label:26s} {funnel['by_rule'][key]:7d} {funnel['by_rule_typescript'][key]:9d}")

    print("\nNo marker records by label, not part of the region numbers above")
    for label, count in funnel["no_marker_labels"].most_common():
        print(f"  {label:38s} {count:7d}")


def summary_json(funnel, description):
    # The counters as plain JSON so the numbers can be copied into the report
    return {
        "population": description,
        "pull_requests": funnel["pull_requests"],
        "marker_regions": funnel["marker_regions"],
        "typescript_regions": funnel["typescript_regions"],
        "no_marker_records": funnel["no_marker_records"],
        "duplicate_keys": funnel["duplicate_keys"],
        "by_stage": {stage: funnel["by_stage"][stage] for stage in stage_order()},
        "by_stage_typescript": {stage: funnel["by_stage_typescript"][stage] for stage in stage_order()},
        "by_rule": [{"stage": s, "rule": r, "label": l, "all": n, "typescript": funnel["by_rule_typescript"][(s, r, l)]}
                    for (s, r, l), n in sorted(funnel["by_rule"].items())],
        "no_marker_labels": dict(funnel["no_marker_labels"]),
    }


def prepare_output(output_dir, overwrite):
    # The funnel counts from a fresh file so old model records cannot mix in
    os.makedirs(output_dir, exist_ok=True)
    paths = {name: os.path.join(output_dir, name)
             for name in ("input.jsonl", "rules.jsonl", "run.log", "summary.json")}
    if os.path.exists(paths["rules.jsonl"]):
        if not overwrite:
            raise FileExistsError(f"{paths['rules.jsonl']} exists, add --overwrite or pick another --output-dir")
        os.remove(paths["rules.jsonl"])
    return paths


def run_funnel(dataset, split_file, splits, output_dir, overwrite=False):
    paths = prepare_output(output_dir, overwrite)
    pull_requests = write_input(dataset, keys_in_splits(split_file, splits), paths["input.jsonl"])
    # The pipeline prints one line per region, so that goes to a log file
    with open(paths["run.log"], "w", encoding="utf-8") as log, contextlib.redirect_stdout(log):
        pipeline.run_one(paths["input.jsonl"], paths["rules.jsonl"], use_llm=False)
    funnel = build_funnel(read_regions(paths["input.jsonl"]), pipeline.read_records(paths["rules.jsonl"]))
    funnel["pull_requests"] = pull_requests
    description = f"{dataset}, splits {' and '.join(splits)}"
    with open(paths["summary.json"], "w", encoding="utf-8") as f:
        json.dump(summary_json(funnel, description), f, indent=2)
    return funnel, description, paths


def main(argv=None):
    parser = argparse.ArgumentParser(description="Count what the rule stages decide, with no model calls")
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--split-file", default=DEFAULT_SPLIT_FILE)
    parser.add_argument("--splits", default="train,dev", help="Comma separated, defaults to train,dev")
    parser.add_argument("--include-test", action="store_true",
                        help="Allow the test split, only for the one run that gives the final numbers")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--overwrite", action="store_true", help="Replace the records of an earlier funnel run")
    args = parser.parse_args(argv)
    try:
        splits = parse_splits(args.splits, args.include_test)
        funnel, description, paths = run_funnel(args.dataset, args.split_file, splits, args.output_dir, args.overwrite)
    except (ValueError, FileExistsError) as e:
        parser.error(str(e))
    print_funnel(funnel, description)
    print(f"\nRecords: {paths['rules.jsonl']}, summary: {paths['summary.json']}, log: {paths['run.log']}")
    print("A normal run with the same input and output classifies only the regions that reached Stage 4")


if __name__ == "__main__":
    main()
