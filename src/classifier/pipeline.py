# stages 0 to 5 orchestration and record writing
# this module is shared and changes need both owners to agree
# it is the only place that calls both rules and llm

import json
import os
import re
from datetime import datetime, timezone
from functools import lru_cache
from importlib import metadata
from pathlib import Path

from classifier.llm import classify_llm, prompt_builder
from classifier.llm.classify_llm import classify_with_llm
from classifier.report import RUN_LOG, STATS, print_report, reset_stats
from classifier.rules.ast_gate import GATE_LABELS
from classifier.rules.patterns import ClassifyInput, classify_deterministic_named
from classifier.schema import (
    Region,
    Result,
    SOURCE_MODEL,
    SOURCE_RULE,
    STATUS_CAPPED,
    STATUS_CLASSIFIED,
    bare_label,
    strip_family,
)

try:
    from classifier.rules.ast_diff import compute_ast_equivalence
    AST_DIFF_AVAILABLE = True
except ImportError:
    AST_DIFF_AVAILABLE = False


# A pr_key with more than this many regions gets a warning printed so a
# case like a giant lockfile diff does not silently burn a lot of time
LARGE_PR_KEY_REGION_WARNING_THRESHOLD = 15

# Once a single file within one pr_key has sent this many regions to the
# model, any further regions in that file are capped instead, only model
# calls count toward this, patterns and the ast gate are free
PER_FILE_API_CALL_CAP = 15

# The reason used for a region that got capped instead of sent to the
# model, kept as a constant so the counting script can match exactly
CAPPED_REASON = "call-ceiling"

# The stage of the report that each existing pattern belongs to
STAGE_BY_PATTERN = {
    "OutOfScope": 0,
    "NoMarkers": 1,
    "SameChange": 1,
    "OneSideChange": 1,
    "WhitespaceOnly": 2,
    "CommentsOnly": 2,
    "ImportRestructure": 2,
    "ReorderOnly": 2,
    "ValueOnlyChange": 3,
    "Lockfile": 3,
    "PackageManifest": 3,
    "ConfigSchema": 3,
    "ImportPathOnly": 3,
    "DisjointEdits": 3,
}
AST_GATE_STAGE = 2
LLM_STAGE = 4

# The default value of each older field kept inside the classifier block
OLD_FIELD_DEFAULTS = {
    "secondary": None,
    "logic_subtype": None,
    "confidence": None,
    "evidence": None,
    "missing_context": None,
    "steps": [],
    "capped": False,
    "needs_verification": False,
    "verification_priority": "normal",
    "base_available": True,
    "graph_unavailable": True,
    "policy_resolved": False,
    "unknown_reason": None,
    "candidate_labels": None,
    "gate": None,
}


@lru_cache(maxsize=1)
def component_version():
    # The source file is read first because installed metadata can be out of date
    pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
    if pyproject.exists():
        match = re.search(r'^version = "(.+)"$', pyproject.read_text(encoding="utf-8"), re.M)
        if match:
            return match.group(1)
    return metadata.version("ast-git-resolver")


def build_provenance(layer, logic_prompt_ran=False):
    # A region decided by a rule carries no model name and no prompt hashes
    provenance = {"component_version": component_version()}
    if layer == "llm":
        provenance["model_name"] = classify_llm.MODEL_NAME
        provenance["router_prompt_hash"] = prompt_builder.system_prompt_hash("A")
        provenance["logic_prompt_hash"] = (
            prompt_builder.system_prompt_hash("B") if logic_prompt_ran else None
        )
    return provenance


def find_stage(layer, detail):
    if layer == "pattern":
        return STAGE_BY_PATTERN[detail]
    return AST_GATE_STAGE if layer == "ast" else LLM_STAGE


def old_fields(values, timestamp):
    # Keeps the older fields in the block and gives candidate labels bare names
    fields = {name: values.get(name, default) for name, default in OLD_FIELD_DEFAULTS.items()}
    if fields["candidate_labels"]:
        fields["candidate_labels"] = [strip_family(name) for name in fields["candidate_labels"]]
    fields["timestamp"] = timestamp
    return fields


def build_classified_block(region, result, layer, detail, timestamp):
    return Result(
        status=STATUS_CLASSIFIED,
        stage=find_stage(layer, detail),
        source=SOURCE_MODEL if layer == "llm" else SOURCE_RULE,
        label=bare_label(result["label"]),
        reason=result["reason"],
        base_state=region.base_state,
        input_hash=region.input_hash,
        provenance=build_provenance(layer, result.get("logic_prompt_ran", False)),
        extra=old_fields(result, timestamp),
    ).to_block()


def build_capped_block(region, timestamp):
    # A capped region never reached a rule that decided it or a model
    values = {"capped": True, "confidence": "low", "base_available": bool(region.base_text)}
    return Result(
        status=STATUS_CAPPED,
        stage=LLM_STAGE,
        reason=CAPPED_REASON,
        base_state=region.base_state,
        input_hash=region.input_hash,
        provenance={"component_version": component_version(), "model_name": None},
        extra=old_fields(values, timestamp),
    ).to_block()


def build_output_record(region, block):
    # One line per region, the join key sits outside the block of each stage
    return {
        "pr_key": region.pr_key,
        "file_path": region.file_path,
        "conflict_index": region.conflict_index,
        "effective_index": region.effective_index,
        "classifier": block,
    }


def read_records(output_path):
    # Reads the output into one record per key and the latest record wins
    # A broken line from an interrupted run is ignored so that region runs again
    records = {}
    if not os.path.exists(output_path):
        return records
    with open(output_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            key = (record.get("pr_key"), record.get("file_path"), record.get("effective_index"))
            records[key] = record
    return records


def compact_output(output_path):
    # Rewrites the output so a rerun leaves exactly one record per key
    # The new file replaces the old one in one step so a crash cannot lose records
    if not os.path.exists(output_path):
        return
    records = read_records(output_path)
    temporary_path = f"{output_path}.tmp"
    with open(temporary_path, "w", encoding="utf-8") as f:
        for record in records.values():
            f.write(json.dumps(record) + "\n")
    os.replace(temporary_path, output_path)


def classify_region(file_path, ours_text, theirs_text, base_text=None, region=None, allow_llm=True):
    # Three layers in order of cost. Text patterns first, then the ast gate,
    # then the model. Returns the result fields plus the layer that decided
    # and a detail such as the pattern name. A None result means the region
    # needed the model but the per file cap did not allow it.
    has_base = bool(base_text)
    h = ClassifyInput(file_path, ours_text, theirs_text, base_text=base_text, region=region)
    matched = classify_deterministic_named(h)
    if matched is not None:
        pattern_name, det = matched
        return {
            "label": det.label, "confidence": det.confidence,
            "reason": det.reason, "logic_subtype": det.logic_subtype,
            "base_available": has_base,
            "graph_unavailable": det.graph_unavailable,
            "policy_resolved": det.policy_resolved,
            "unknown_reason": det.unknown_reason,
            "candidate_labels": det.candidate_labels,
            "gate": None,
        }, "pattern", pattern_name

    eq = None
    if AST_DIFF_AVAILABLE:
        eq = compute_ast_equivalence(file_path, ours_text, theirs_text)
        if eq.equivalence in GATE_LABELS:
            label, reason = GATE_LABELS[eq.equivalence]
            evidence = f"ast equivalence {eq.equivalence}"
            if eq.renames:
                evidence += f" {json.dumps(eq.renames)}"
            return {
                "label": label, "confidence": "high", "reason": reason,
                "evidence": evidence,
                "base_available": has_base,
                "graph_unavailable": True,
                "policy_resolved": False,
                "gate": eq.equivalence,
            }, "ast", eq.equivalence

    if not allow_llm:
        return None, None, None

    llm_result = classify_with_llm(file_path, ours_text, theirs_text, eq, region)
    llm_result["base_available"] = has_base
    llm_result["graph_unavailable"] = True
    llm_result["policy_resolved"] = False
    llm_result["gate"] = eq.equivalence if eq is not None else None
    return llm_result, "llm", None


def count_decision(block, layer, detail):
    # Updates the run counters and returns the text shown for this region
    shown = block["label"]
    if layer == "pattern":
        STATS["deterministic"] += 1
        STATS["by_pattern"][detail] = STATS["by_pattern"].get(detail, 0) + 1
        shown += f" ({detail})"
    elif layer == "ast":
        STATS["ast"] += 1
        STATS["by_equivalence"][detail] = STATS["by_equivalence"].get(detail, 0) + 1
        shown += f" (ast {detail})"
    if block["needs_verification"]:
        STATS["needs_verification"] += 1
        shown += " needs_verification"
    return shown


def process_region(pr_key, region_position, raw_region, outfile, api_call_counts_by_file,
                   finished_keys):
    region = Region.from_raw(pr_key, region_position, raw_region)
    if region.key in finished_keys:
        return

    timestamp = datetime.now(timezone.utc).isoformat()

    # Only model calls count toward the cap, so patterns and the ast gate
    # still run on a file that has already used up its share
    calls_so_far_for_file = api_call_counts_by_file.get(region.file_path, 0)
    allow_llm = calls_so_far_for_file < PER_FILE_API_CALL_CAP

    result, layer, detail = classify_region(
        region.file_path, region.ours_text, region.theirs_text, region.base_text,
        raw_region, allow_llm,
    )

    STATS["total"] += 1
    if result is None:
        STATS["capped"] += 1
        block = build_capped_block(region, timestamp)
        shown = f"{STATUS_CAPPED} (per file cap)"
    else:
        block = build_classified_block(region, result, layer, detail, timestamp)
        shown = count_decision(block, layer, detail)
        if layer == "llm":
            api_call_counts_by_file[region.file_path] = calls_so_far_for_file + 1

    RUN_LOG.append({
        "key": (pr_key, region.file_path, region.conflict_index), "layer": layer,
        "label": block.get("label"), "subtype": block["logic_subtype"],
    })
    outfile.write(json.dumps(build_output_record(region, block)) + "\n")
    outfile.flush()

    print(f"{pr_key} {region.file_path} region {region.effective_index}: {shown}")
    finished_keys.add(region.key)


def run_one(input_path, output_path, rerun=False):
    # A normal run skips finished keys so it can resume after stopping
    # A rerun processes every key in the input and overwrites only those keys
    reset_stats()
    compact_output(output_path)
    finished_keys = set() if rerun else set(read_records(output_path))
    if rerun:
        print("Rerun is on, every region in the input is classified again and overwritten")
    else:
        print(f"Found {len(finished_keys)} regions already labeled, they will be skipped")

    with open(input_path, "r", encoding="utf-8") as infile, \
            open(output_path, "a", encoding="utf-8") as outfile:
        for line in infile:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            pr_key = record.get("pr_key")
            regions = record.get("regions", [])
            if len(regions) > LARGE_PR_KEY_REGION_WARNING_THRESHOLD:
                print(f"Warning, {pr_key} has {len(regions)} regions, this may take a while")

            # The per file cap starts fresh for every pr_key
            api_call_counts_by_file = {}
            for region_position, region in enumerate(regions):
                process_region(pr_key, region_position, region, outfile,
                               api_call_counts_by_file, finished_keys)
    compact_output(output_path)
    print_report()
