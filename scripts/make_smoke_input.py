# Builds a small smoke test input of regions that would reach the model, with no model calls
# keys_in_split reads the pull requests of one split, train or dev only, never test
# reaches_model runs the rule stages with the model off and find_candidates keeps every region the rules could not decide
# main samples a seeded random set, writes it in the dataset shape grouped by pull request, and prints the size of the sample

# picks a random set of regions that reach the model from one split, with no model calls
# the output has the same shape as the dataset so the normal command can run on it

import argparse
import json
import random
from collections import defaultdict

from classifier import pipeline
from classifier.schema import Region

DEFAULT_DATASET = "data/raw/final_dataset.jsonl"
DEFAULT_SPLIT_FILE = "data/splits/split.jsonl"
DEFAULT_SEED = 20261105


def keys_in_split(split_file, split_name):
    with open(split_file, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    return {row["pr_key"] for row in rows if row["split"] == split_name}


def reaches_model(pr_key, position, raw):
    region = Region.from_raw(pr_key, position, raw)
    result, _, _ = pipeline.classify_region(
        region.file_path, region.ours_text, region.theirs_text, region.base_text, raw, False
    )
    return result is None


def find_candidates(dataset, keys):
    # Keeps the list position so the picked regions can be written in their original order
    candidates = []
    with open(dataset, encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            if record.get("pr_key") not in keys:
                continue
            for position, raw in enumerate(record.get("regions", [])):
                if reaches_model(record["pr_key"], position, raw):
                    candidates.append((record["pr_key"], position, raw))
    return candidates


def main():
    parser = argparse.ArgumentParser(description="Write a small input of regions that reach the model")
    parser.add_argument("output_path")
    parser.add_argument("--split", default="dev", choices=["train", "dev"])
    parser.add_argument("--regions", type=int, default=100)
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--split-file", default=DEFAULT_SPLIT_FILE)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()

    candidates = find_candidates(args.dataset, keys_in_split(args.split_file, args.split))
    picked = random.Random(args.seed).sample(candidates, min(args.regions, len(candidates)))
    regions_by_pr = defaultdict(list)
    for pr_key, position, raw in sorted(picked, key=lambda item: (item[0], item[1])):
        regions_by_pr[pr_key].append(raw)
    with open(args.output_path, "w", encoding="utf-8") as f:
        for pr_key, regions in regions_by_pr.items():
            f.write(json.dumps({"pr_key": pr_key, "regions": regions}) + "\n")
    print(f"{args.split} has {len(candidates)} regions that reach the model")
    print(f"Wrote {len(picked)} regions from {len(regions_by_pr)} pull requests to {args.output_path}")
    total_chars = sum(len(raw.get("ours_text") or "") + len(raw.get("theirs_text") or "")
                      + len(raw.get("base_text") or "") for _, _, raw in picked)
    print(f"Region text in the sample is {total_chars} characters")


if __name__ == "__main__":
    main()
