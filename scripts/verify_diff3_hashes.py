"""Checks the ours and theirs text of the diff3 dataset against the AgenticFlict hashes.

AgenticFlict was built with Git's default conflict style and the diff3 dataset with the diff3
style, so the same conflict can have different region boundaries in the two. The script counts
how many regions it can still match by SHA-256 hash, in four steps that each build on the last.

1. The stored hashes match under the same pr_key, file_path and conflict_index.
2. The stored hashes match a region of the same file under another conflict_index.
3. git merge-file rebuilds the default style regions from the region's base, ours and theirs text,
   and every rebuilt region matches a hash of the same file.
4. Several diff3 regions that Git joins into one default style region are put together by line
   position, and the few unknown lines between them are filled from lines with no letters or
   digits seen in the dataset. Both the ours and theirs hash must match.

It also explains the AgenticFlict regions that have no diff3 region with the same identifier.
The script only reads its inputs. Git merge-file runs on copies in a system temp folder.

Usage:
    python scripts/verify_diff3_hashes.py AGENTICFLICT_REGIONS_CSV DATASET_JSONL [DATASET_JSONL ...]
"""
import argparse
import collections
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

csv.field_size_limit(10**9)

NL = '\n'
GAP = '\x00'
MARKER = 31
LANES = 8
GAP_SEARCH_WIDTH = {1: None, 2: 200, 3: 60}


def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def split_lines(text):
    return [] if text == '' else text.split(NL)


def add_side_coordinates(regions):
    # turns conflicted file line numbers into line numbers on the ours side and the theirs side
    regions.sort(key=lambda r: r['idx'])
    dropped_ours = dropped_theirs = 0
    for r in regions:
        total = r['end'] - r['start'] + 1
        r['os'] = r['start'] - dropped_ours
        r['ts'] = r['start'] - dropped_theirs
        r['oe'] = r['os'] + r['on']
        r['te'] = r['ts'] + r['tn']
        dropped_ours += total - r['on']
        dropped_theirs += total - r['tn']


def spans_overlap(s1, e1, s2, e2):
    # treats an empty span as a point so an empty side still meets its neighbour
    if s1 == e1 or s2 == e2:
        return s2 <= s1 <= e2 or s1 <= s2 <= e1
    return max(s1, s2) < min(e1, e2)


def regions_touch(a, b):
    return spans_overlap(a['os'], a['oe'], b['os'], b['oe']) or spans_overlap(a['ts'], a['te'], b['ts'], b['te'])


def load_agenticflict(path):
    files = collections.defaultdict(list)
    with open(path, encoding='utf-8', newline='') as f:
        for r in csv.DictReader(f):
            files[(r['pr_key'], r['file_path'])].append(dict(
                idx=int(r['conflict_index']), start=int(r['start_line']), end=int(r['end_line']),
                on=int(r['ours_lines']), tn=int(r['theirs_lines']),
                ho=r['ours_sha256'], ht=r['theirs_sha256']))
    return files


def load_dataset(paths):
    # keeps marker regions only and collects lines with no letters or digits for the gap search
    files = collections.defaultdict(list)
    pr_keys = set()
    no_alnum = collections.Counter()
    for path in paths:
        with open(path, encoding='utf-8') as f:
            for line in f:
                pr = json.loads(line)
                pr_keys.add(pr['pr_key'])
                for g in pr.get('regions', []):
                    if 'ours_text' not in g:
                        continue
                    ours, theirs = split_lines(g['ours_text']), split_lines(g['theirs_text'])
                    base = g.get('base_text')
                    for text_line in ours + theirs + split_lines(base or ''):
                        if not re.search(r'[A-Za-z0-9]', text_line):
                            no_alnum[text_line] += 1
                    files[(pr['pr_key'], g['file_path'])].append(dict(
                        idx=g['conflict_index'], start=g['start_line'], end=g['end_line'],
                        on=len(ours), tn=len(theirs), o=ours, t=theirs,
                        ours_text=g['ours_text'], theirs_text=g['theirs_text'], base_text=base,
                        ho=g['ours_sha256'], ht=g['theirs_sha256']))
    vocab = [text_line.encode('utf-8') for text_line, _ in no_alnum.most_common()]
    return files, pr_keys, vocab


def parse_conflicts(output):
    # reads the ours and theirs blocks out of git merge-file output and hashes them
    found, current, side = [], None, None
    for text_line in output.split(NL):
        if text_line.startswith('<' * MARKER):
            current, side = {'o': [], 't': []}, 'o'
        elif current is not None and side == 'o' and text_line.startswith('=' * MARKER):
            side = 't'
        elif current is not None and text_line.startswith('>' * MARKER):
            found.append((sha(NL.join(current['o'])), sha(NL.join(current['t']))))
            current = None
        elif current is not None:
            current[side].append(text_line)
    return found


def remerge_default_style(region, folder):
    # runs git merge-file in the default conflict style on the region's three texts
    paths = []
    for name, text in (('ours', region['ours_text']), ('base', region['base_text']), ('theirs', region['theirs_text'])):
        path = os.path.join(folder, name)
        with open(path, 'wb') as f:
            f.write(('' if text == '' else text + NL).encode('utf-8'))
        paths.append(path)
    done = subprocess.run(
        ['git', '-c', 'merge.conflictstyle=merge', 'merge-file', '-p', f'--marker-size={MARKER}'] + paths,
        capture_output=True)
    if done.returncode < 0:
        return None
    return parse_conflicts(done.stdout.decode('utf-8', 'replace'))


def remerge_all(jobs):
    # gives each worker its own folder so the temporary files never collide
    root = tempfile.mkdtemp(prefix='verify_diff3_')
    try:
        lanes = [jobs[i::LANES] for i in range(LANES)]
        folders = [os.path.join(root, str(i)) for i in range(LANES)]
        for folder in folders:
            os.makedirs(folder)

        def run_lane(lane_and_folder):
            lane, folder = lane_and_folder
            return [(key, region, remerge_default_style(region, folder)) for key, region in lane]

        results = []
        with ThreadPoolExecutor(LANES) as pool:
            for part in pool.map(run_lane, zip(lanes, folders)):
                results.extend(part)
        return results
    finally:
        shutil.rmtree(root, ignore_errors=True)


def side_lines(group, start, end, side):
    # places the known diff3 text on side line numbers and leaves the rest unknown
    known = {}
    for r in group:
        first = r['os'] if side == 'o' else r['ts']
        for i, text_line in enumerate(r[side]):
            known[first + i] = text_line
    return [known.get(i) for i in range(start, end)]


def known_parts(lines):
    # splits the region text into the known parts that sit between unknown lines
    text = NL.join(GAP if x is None else x for x in lines)
    return [part.encode('utf-8') for part in text.split(GAP)]


def search_gap(parts, target, words):
    # hashes the known parts once and adds each guessed gap line on top
    gaps = len(parts) - 1

    def walk(state, i, chosen):
        if i == gaps:
            return chosen if state.hexdigest() == target else None
        for w in words:
            nxt = state.copy()
            nxt.update(w + parts[i + 1])
            found = walk(nxt, i + 1, chosen + [w])
            if found:
                return found
        return None

    return walk(hashlib.sha256(parts[0]), 0, [])


def fill_joined_region(ours_lines, theirs_lines, af_region, vocab):
    # returns the outcome of filling the unknown gap lines against both hashes
    gaps = sum(x is None for x in ours_lines)
    if gaps != sum(x is None for x in theirs_lines):
        return 'gap size differs between sides'
    if gaps == 0:
        same = sha(NL.join(ours_lines)) == af_region['ho'] and sha(NL.join(theirs_lines)) == af_region['ht']
        return 'verified, no gap' if same else 'no gap, hash differs'
    if gaps > 3:
        return 'gap longer than 3 lines'
    width = GAP_SEARCH_WIDTH[gaps]
    words = vocab if width is None else vocab[:width]
    found = search_gap(known_parts(ours_lines), af_region['ho'], words)
    if not found:
        return f'gap of {gaps} not found'
    theirs_parts = known_parts(theirs_lines)
    state = hashlib.sha256(theirs_parts[0])
    for w, part in zip(found, theirs_parts[1:]):
        state.update(w + part)
    return f'verified, gap of {gaps}' if state.hexdigest() == af_region['ht'] else f'gap of {gaps}, theirs differs'


def print_counts(title, counts, total):
    print(title)
    for name, value in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f'  {name:42s} {value:7d}  {100 * value / total:5.1f}%')


def report_steps(outcome, title):
    # prints the outcome table and the running share verified after each step
    total = max(1, len(outcome))
    counts = collections.Counter(outcome.values())
    print_counts(f'outcome per diff3 region, {title}, {len(outcome)} regions', counts, total)
    running = 0
    print(f'hash verified so far, {title}')
    for step in ('step 1, same identifier', 'step 2, other conflict index', 'step 3, re-merged', 'step 4, joined region'):
        running += counts[step]
        print(f'  after {step:38s} {running:7d}  {100 * running / total:5.1f}%')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('agenticflict_regions_csv')
    parser.add_argument('dataset_jsonl', nargs='+')
    args = parser.parse_args()

    af = load_agenticflict(args.agenticflict_regions_csv)
    ds, pr_keys, vocab = load_dataset(args.dataset_jsonl)
    for regions in list(ds.values()) + [af[k] for k in af if k[0] in pr_keys]:
        add_side_coordinates(regions)
    total = sum(len(v) for v in ds.values())
    print(f'marker regions {total}, pull requests {len(pr_keys)}')

    outcome = {}
    to_remerge = []
    for key, regions in ds.items():
        theirs = af.get(key, [])
        by_idx = {a['idx']: a for a in theirs}
        pairs = {(a['ho'], a['ht']) for a in theirs}
        for r in regions:
            rid = (key, r['idx'])
            same = by_idx.get(r['idx'])
            if same and (same['ho'], same['ht']) == (r['ho'], r['ht']):
                outcome[rid] = 'step 1, same identifier'
            elif (r['ho'], r['ht']) in pairs:
                outcome[rid] = 'step 2, other conflict index'
            elif r['base_text'] is None:
                outcome[rid] = 'left, no base to re-merge'
            else:
                to_remerge.append((key, r))

    for key, r, rebuilt in remerge_all(to_remerge):
        pairs = {(a['ho'], a['ht']) for a in af.get(key, [])}
        rid = (key, r['idx'])
        if rebuilt is None:
            outcome[rid] = 'left, git merge-file failed'
        elif not rebuilt:
            outcome[rid] = 'left, re-merge gives no conflict'
        elif all(p in pairs for p in rebuilt):
            outcome[rid] = 'step 3, re-merged'
        elif any(p in pairs for p in rebuilt):
            outcome[rid] = 'left, re-merge partly matches'
        else:
            outcome[rid] = 'unmatched'

    for key, regions in ds.items():
        for a in af.get(key, []):
            group = [r for r in regions if regions_touch(r, a)]
            ids = [(key, r['idx']) for r in group]
            if len(group) < 2 or not any(outcome.get(i) == 'unmatched' for i in ids):
                continue
            ours_lines = side_lines(group, a['os'], a['os'] + a['on'], 'o')
            theirs_lines = side_lines(group, a['ts'], a['ts'] + a['tn'], 't')
            result = fill_joined_region(ours_lines, theirs_lines, a, vocab)
            label = 'step 4, joined region' if result.startswith('verified') else f'left, joined region, {result}'
            for i in ids:
                if outcome.get(i) == 'unmatched':
                    outcome[i] = label
    for rid, value in outcome.items():
        if value == 'unmatched':
            outcome[rid] = 'left, no joined region found'

    report_steps(outcome, 'all marker regions')
    ts_only = {rid: v for rid, v in outcome.items() if rid[0][1].endswith(('.ts', '.tsx'))}
    report_steps(ts_only, 'marker regions in .ts and .tsx files')

    unpaired = collections.Counter()
    for key, theirs in af.items():
        if key[0] not in pr_keys:
            continue
        mine = ds.get(key, [])
        ids = {r['idx'] for r in mine}
        for a in theirs:
            if a['idx'] in ids:
                continue
            if not mine:
                unpaired['file has no diff3 marker region'] += 1
            elif any(regions_touch(r, a) for r in mine):
                unpaired['overlaps a diff3 region by position'] += 1
            else:
                unpaired['no diff3 region at that position'] += 1
    print_counts('agenticflict regions with no diff3 region under the same identifier', unpaired,
                 max(1, sum(unpaired.values())))
    return 0


if __name__ == '__main__':
    sys.exit(main())
