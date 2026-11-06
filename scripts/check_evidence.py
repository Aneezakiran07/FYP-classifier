# read only look at the evidence the model gave for the test it marked as met
# it checks whether each quoted piece appears in the region text, no model calls

import argparse
import json
import re
from collections import Counter

from classifier.schema import Region

QUOTED = re.compile(r"`([^`]+)`")
SIDE_LABEL = re.compile(r"^(?:OURS|THEIRS|BASE)\s*:\s*", re.IGNORECASE)


def squash(text):
    return " ".join((text or "").split())


def load_regions(input_path):
    # Regions are looked up by pull request, file path and conflict index
    regions = {}
    with open(input_path, encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            for position, raw in enumerate(record.get("regions", [])):
                region = Region.from_raw(record["pr_key"], position, raw)
                index = raw.get("conflict_index", position)
                regions[(record["pr_key"], region.file_path, index)] = region
    return regions


def first_met(trace):
    # The pipeline picks the first test the model marked as met
    met = [step for step in trace if step.get("met") is True]
    return (met[0], len(met)) if met else (None, 0)


def pieces_of(evidence):
    found = [SIDE_LABEL.sub("", piece).strip() for piece in QUOTED.findall(evidence or "")]
    if not found:
        found = [piece.strip() for piece in DOUBLE_QUOTED.findall(evidence or "")]
    return [piece for piece in found if piece]

AST_KIND = re.compile(r"^[a-z_]+_(?:added|removed|replaced|changed)(?::|$)")
DOUBLE_QUOTED = re.compile(r'"([^"]{3,})"')


def nospace(text):
    return "".join((text or "").split())


def where_found(piece, region):
    # Returns where the piece was found, or None
    if AST_KIND.match(piece):
        return "ast kind"
    target = nospace(piece)
    for name, text in (("ours", region.ours_text), ("theirs", region.theirs_text), ("base", region.base_text)):
        if target in nospace(text):
            return name
    return None

def main():
    parser = argparse.ArgumentParser(description="Check quoted evidence against the region text")
    parser.add_argument("--output-file", default="outputs/smoke/luna.jsonl")
    parser.add_argument("--input-file", default="outputs/smoke/input.jsonl")
    parser.add_argument("--show", type=int, default=15)
    args = parser.parse_args()

    regions = load_regions(args.input_file)
    per_test = Counter()
    missed = []
    unfound = 0
    no_quotes = []
    multi = 0
    total_met = 0

    with open(args.output_file, encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            step, met_count = first_met(record["classifier"].get("trace", []))
            if step is None:
                continue
            total_met += 1
            multi += 1 if met_count > 1 else 0
            key = (record["pr_key"], record["file_path"], record["conflict_index"])
            region = regions.get(key)
            if region is None:
                unfound += 1
                continue
            text_ours = squash(region.ours_text)
            text_theirs = squash(region.theirs_text)
            pieces = pieces_of(step.get("evidence"))
            if not pieces:
                no_quotes.append((step["test"], step.get("evidence")))
                continue
            for piece in pieces:
                per_test[(step["test"], "pieces")] += 1
                place = where_found(piece, region)
                if place:
                    per_test[(step["test"], "found")] += 1
                    per_test[("where", place)] += 1
                else:
                    missed.append((step["test"], piece, step.get("evidence")))

    print(f"Records where a test was met: {total_met}")
    print(f"  more than one test met: {multi}")
    print(f"  region not found in the input file: {unfound}")
    print(f"  met test with no quoted piece: {len(no_quotes)}")
    print()
    tests = sorted({test for test, kind in per_test if test != "where"})
    for test in tests:
        pieces_count = per_test[(test, "pieces")]
        found_count = per_test[(test, "found")]
        print(f"{test:28s} pieces {pieces_count:4d}  found in region {found_count:4d}")
    print()
    print(f"Pieces not found: {len(missed)}")
    for test, piece, evidence in missed[: args.show]:
        print(f"--- {test}\npiece: {piece[:200]}\nfull evidence: {(evidence or '')[:300]}\n")
    print("Met tests with no quotes, first few:")
    for test, evidence in no_quotes[: args.show]:
        print(f"--- {test}: {(evidence or '')[:200]}")

    print({place: per_test[("where", place)] for place in ("ours", "theirs", "base", "ast kind")})
if __name__ == "__main__":
    main()