# Applies the current rules and validators to a finished run with no model calls and writes a new output file
# Every region first goes through Stages 0 to 3 again, and a region the rules now decide gets a fresh rule record
# A model record is then checked again from the answers saved in its trace, with the same selection and validator as the pipeline
# A rule record whose region now needs the model is left out, so a normal run on the new file classifies only that region

# read only for the input files, it writes only the output path it is given and refuses to overwrite the input
# the model answers are never changed, only the rule and validator decisions made from them
# a changed record keeps its original model name and prompt hashes and gains the commit that revalidated it

import argparse
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from classifier import pipeline  # noqa: E402
from classifier.llm.prompts import LOGIC_TESTS  # noqa: E402
from classifier.schema import STATUS_CLASSIFIED, Region, TestAnswer  # noqa: E402

DEFAULT_DATASET = str(ROOT / "data" / "raw" / "final_dataset.jsonl")


def read_records(path):
    # A broken last line from a run that is still writing is skipped and counted
    records, broken = [], 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                broken += 1
    return records, broken


def record_key(record):
    return (record.get("pr_key"), record.get("file_path"), record.get("effective_index"))


def read_regions(dataset_path, wanted):
    # Builds a Region for every key that has a record, using the same key as the pipeline
    regions = {}
    with open(dataset_path, "r", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            for position, raw in enumerate(row.get("regions", [])):
                region = Region.from_raw(row.get("pr_key"), position, raw)
                if region.key in wanted:
                    regions[region.key] = region
    return regions


def current_commit():
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True)
        return out.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def rule_block(region, timestamp):
    # The block the rules give today, or None when the region still needs the model
    result, layer, detail = pipeline.classify_region(
        region.file_path, region.ours_text, region.theirs_text, region.base_text, region.raw, False
    )
    if result is None:
        return None
    return pipeline.build_classified_block(region, result, layer, detail, timestamp)


def saved_answers(trace):
    answers = [TestAnswer(e["test"], e.get("met"), e.get("evidence")) for e in trace if e.get("test") in LOGIC_TESTS]
    return answers if [a.test_id for a in answers] == list(LOGIC_TESTS) else None


def recheck_model_block(region, old):
    # Repeats the Stage 4 decision from the saved router answer and test answers, or returns None to keep the old block
    trace = old.get("trace") or []
    router = next((e for e in trace if e.get("test") == "router"), None)
    if old.get("status") != STATUS_CLASSIFIED or old.get("source") != "model" or router is None:
        return None
    routed = {"kind": router.get("answer"), "reason": router.get("reason")}
    stage_region = Region.from_raw(None, 0, region.raw)
    new_trace = [router]
    if routed["kind"] == "semantic":
        answers = saved_answers(trace)
        if answers is None:
            return None
        result = pipeline.select_logic_label(stage_region, routed, answers, new_trace)
    elif routed["kind"] == "structural":
        eq = pipeline.apply_guards(
            pipeline.compute_ast_equivalence(region.file_path, region.ours_text, region.theirs_text),
            region.ours_text, region.theirs_text,
        )
        result = pipeline.confirm_structural_hint(stage_region, eq, routed, new_trace)
    else:
        return None
    result.update({
        "trace": new_trace, "logic_prompt_ran": routed["kind"] == "semantic",
        "model_calls": old.get("model_calls", 0), "base_available": old.get("base_available"),
        "graph_unavailable": True, "policy_resolved": False, "gate": old.get("gate"),
    })
    block = pipeline.build_classified_block(region, result, "llm", None, old.get("timestamp"))
    block["provenance"] = dict(old.get("provenance") or {})
    return block


def decision(block):
    # The fields that say what was decided, used to tell a real change from a rebuilt copy
    return (block.get("status"), block.get("label"), block.get("unknown_reason"), block.get("stage"),
            block.get("source"), block.get("confirming_test"))


def shown(block):
    label = block.get("label") or block.get("status")
    reason = block.get("unknown_reason")
    return f"{label} ({reason})" if reason else label


def revalidate_record(record, region, commit):
    # Returns the new record or None to leave it out, and a short word for the summary
    old = record["classifier"]
    if region is None:
        return record, "kept, region not in the dataset"
    if region.input_hash != old.get("input_hash"):
        return record, "kept, input hash differs"
    new = rule_block(region, old.get("timestamp"))
    if new is None:
        if old.get("source") == "rule":
            return None, "left out, now needs the model"
        new = recheck_model_block(region, old)
    if new is None or decision(new) == decision(old):
        return record, "unchanged"
    new.setdefault("provenance", {})["revalidated_commit"] = commit
    return {**record, "classifier": new}, "changed"


def revalidate(records, regions, commit):
    out, counts, changes = [], Counter(), Counter()
    for record in records:
        new, outcome = revalidate_record(record, regions.get(record_key(record)), commit)
        counts[outcome] += 1
        if outcome == "changed":
            changes[(shown(record["classifier"]), shown(new["classifier"]))] += 1
        if new is not None:
            out.append(new)
    return out, counts, changes


def main(argv=None):
    parser = argparse.ArgumentParser(description="Apply the current rules and validators to a finished run, no model calls")
    parser.add_argument("records_path", help="Output jsonl of a classifier run")
    parser.add_argument("output_path", help="New jsonl to write, never the input")
    parser.add_argument("--dataset", default=DEFAULT_DATASET, help="The dataset the run was made from")
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing output file")
    args = parser.parse_args(argv)

    if os.path.abspath(args.records_path) == os.path.abspath(args.output_path):
        raise SystemExit("The output must be a new file, not the run that is being checked")
    if os.path.exists(args.output_path) and not args.overwrite:
        raise SystemExit(f"{args.output_path} exists, pass --overwrite to replace it")

    records, broken = read_records(args.records_path)
    regions = read_regions(args.dataset, {record_key(r) for r in records})
    out, counts, changes = revalidate(records, regions, current_commit())
    with open(args.output_path, "w", encoding="utf-8") as f:
        for record in out:
            f.write(json.dumps(record) + "\n")

    print(f"Read {len(records)} records, skipped {broken} broken lines, wrote {len(out)} to {args.output_path}")
    for outcome, count in sorted(counts.items()):
        print(f"  {outcome}: {count}")
    if changes:
        print("Changes, old to new")
        for (old, new), count in changes.most_common():
            print(f"  {count:>5}  {old}  to  {new}")
    if counts["left out, now needs the model"]:
        print("Run the classifier on the dataset with the new file as output to classify the left out regions")
    return counts, changes


if __name__ == "__main__":
    main()
