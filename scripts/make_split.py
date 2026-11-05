# splits the pull requests of the final dataset into train, dev and test
# the split is by pr_key and never by region, so one pull request stays in one set
# the same seed always gives the same split, so both of us get identical sets

import argparse
import json
import random
from collections import Counter, defaultdict

DEFAULT_INDEX = "data/raw/final_dataset_index.jsonl"
DEFAULT_OUT = "data/splits/split.jsonl"
DEFAULT_SEED = 20261105
DEV_SHARE = 0.15
TEST_SHARE = 0.15


def split_group(keys, seed):
    # Sorting first means the order of the input file cannot change the split
    shuffled = sorted(keys)
    random.Random(seed).shuffle(shuffled)
    dev_count = round(len(shuffled) * DEV_SHARE)
    test_count = round(len(shuffled) * TEST_SHARE)
    assigned = {key: "dev" for key in shuffled[:dev_count]}
    assigned.update({key: "test" for key in shuffled[dev_count:dev_count + test_count]})
    assigned.update({key: "train" for key in shuffled[dev_count + test_count:]})
    return assigned


def split_rows(rows, seed=DEFAULT_SEED):
    # Each file count bucket is split on its own so every set keeps the same mix
    keys_by_bucket = defaultdict(list)
    for row in rows:
        keys_by_bucket[row["bucket"]].append(row["pr_key"])
    assigned = {}
    for bucket, keys in keys_by_bucket.items():
        assigned.update(split_group(keys, seed))
    return [{"pr_key": row["pr_key"], "bucket": row["bucket"], "split": assigned[row["pr_key"]]}
            for row in rows]


def main():
    parser = argparse.ArgumentParser(description="Split pull requests into train, dev and test")
    parser.add_argument("--index", default=DEFAULT_INDEX)
    parser.add_argument("--out", default=DEFAULT_OUT)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()

    with open(args.index, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    split = split_rows(rows, args.seed)
    with open(args.out, "w", encoding="utf-8") as f:
        for row in split:
            f.write(json.dumps(row) + "\n")
    print(f"Wrote {len(split)} pull requests to {args.out} with seed {args.seed}")
    for pair, count in sorted(Counter((row["split"], row["bucket"]) for row in split).items()):
        print(f"{pair[0]} {pair[1]}: {count}")


if __name__ == "__main__":
    main()
