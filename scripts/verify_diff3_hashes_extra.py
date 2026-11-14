"""Two extra checks on the hash verification of the diff3 dataset, used in docs/hash_verification.md.

1. Reliability of the re-merge. The regions whose stored hashes already match AgenticFlict under
   the same identifier are known to hold the right text. The script re-merges them in the default
   style the same way step 3 of verify_diff3_hashes.py does and counts how often it still fails.
2. Sameness of the unpaired regions. For the AgenticFlict regions that have no diff3 region with
   the same identifier, it counts how many have a hash pair that some diff3 region, or a region
   rebuilt in steps 3 and 4, reproduces exactly, and how many only overlap by position.

The script only reads its inputs. It reuses the functions of verify_diff3_hashes.py.

Usage:
    python scripts/verify_diff3_hashes_extra.py AGENTICFLICT_REGIONS_CSV DATASET_JSONL [DATASET_JSONL ...]
"""
import argparse
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verify_diff3_hashes as v  # noqa: E402


def split_by_first_steps(ds, af):
    # sorts regions into those step one verifies and those that go to the re-merge
    proven = collections.defaultdict(set)
    step_one, to_remerge = [], []
    for key, regions in ds.items():
        theirs = af.get(key, [])
        by_idx = {a['idx']: a for a in theirs}
        pairs = {(a['ho'], a['ht']) for a in theirs}
        for r in regions:
            pair = (r['ho'], r['ht'])
            same = by_idx.get(r['idx'])
            if same and (same['ho'], same['ht']) == pair:
                proven[key].add(pair)
                if r['base_text'] is not None:
                    step_one.append((key, r))
            elif pair in pairs:
                proven[key].add(pair)
            elif r['base_text'] is not None:
                to_remerge.append((key, r))
    return proven, step_one, to_remerge


def remerge_reliability(step_one, af):
    # re-merges regions with known right text and counts how the re-merge ends
    counts = collections.Counter()
    for key, r, rebuilt in v.remerge_all(step_one):
        pairs = {(a['ho'], a['ht']) for a in af.get(key, [])}
        if rebuilt and all(p in pairs for p in rebuilt):
            counts['re-merge matches'] += 1
        elif rebuilt and any(p in pairs for p in rebuilt):
            counts['re-merge partly matches'] += 1
        elif not rebuilt:
            counts['re-merge gives no conflict'] += 1
        else:
            counts['re-merge does not match'] += 1
    return counts


def add_rebuilt_pairs(proven, to_remerge, ds, af, vocab):
    # adds the hash pairs that steps three and four reproduce
    left = set()
    for key, r, rebuilt in v.remerge_all(to_remerge):
        pairs = {(a['ho'], a['ht']) for a in af.get(key, [])}
        hits = [p for p in (rebuilt or []) if p in pairs]
        proven[key].update(hits)
        if not rebuilt or len(hits) < len(rebuilt):
            left.add((key, r['idx']))
    for key, regions in ds.items():
        for a in af.get(key, []):
            group = [r for r in regions if v.regions_touch(r, a)]
            if len(group) < 2 or not any((key, r['idx']) in left for r in group):
                continue
            ours = v.side_lines(group, a['os'], a['os'] + a['on'], 'o')
            theirs = v.side_lines(group, a['ts'], a['ts'] + a['tn'], 't')
            if v.fill_joined_region(ours, theirs, a, vocab).startswith('verified'):
                proven[key].add((a['ho'], a['ht']))


def unpaired_sameness(proven, ds, af, pr_keys):
    # sorts the agenticflict regions with no same identifier diff3 region by the evidence for them
    counts = collections.Counter()
    for key, theirs in af.items():
        if key[0] not in pr_keys:
            continue
        mine = ds.get(key, [])
        ids = {r['idx'] for r in mine}
        for a in theirs:
            if a['idx'] in ids:
                continue
            if (a['ho'], a['ht']) in proven[key]:
                counts['proven by hash'] += 1
            elif any(v.regions_touch(r, a) for r in mine):
                counts['overlap only'] += 1
            else:
                counts['no diff3 region at that position'] += 1
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('agenticflict_regions_csv')
    parser.add_argument('dataset_jsonl', nargs='+')
    args = parser.parse_args()

    af = v.load_agenticflict(args.agenticflict_regions_csv)
    ds, pr_keys, vocab = v.load_dataset(args.dataset_jsonl)
    for regions in list(ds.values()) + [af[k] for k in af if k[0] in pr_keys]:
        v.add_side_coordinates(regions)

    proven, step_one, to_remerge = split_by_first_steps(ds, af)
    counts = remerge_reliability(step_one, af)
    v.print_counts(f're-merge on {len(step_one)} regions that step one already verified', counts, max(1, len(step_one)))

    add_rebuilt_pairs(proven, to_remerge, ds, af, vocab)
    counts = unpaired_sameness(proven, ds, af, pr_keys)
    v.print_counts('agenticflict regions with no diff3 region under the same identifier', counts,
                   max(1, sum(counts.values())))
    return 0


if __name__ == '__main__':
    sys.exit(main())
