# stages 0 to 5 orchestration and record writing
# this module is shared and changes need both owners to agree
# it is the only place that calls both rules and llm

import json
import os
from datetime import datetime, timezone

from classifier.llm import classify_llm
from classifier.llm.classify_llm import classify_with_llm
from classifier.report import RUN_LOG, STATS, print_report, reset_stats
from classifier.rules.ast_gate import GATE_LABELS
from classifier.rules.patterns import ClassifyInput, classify_deterministic_named

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

# The label and reason used for a region that got capped instead of sent
# to the model, kept as constants so the counting script can match exactly
CAPPED_LABEL = "not-reviewed"
CAPPED_REASON = "high-volume file, not individually reviewed beyond first 15 regions"

def build_output_record(
    pr_key,
    conflict_index,
    effective_index,
    file_path,
    attempt_number,
    timestamp,
    label,
    confidence,
    reason,
    capped=False,
    secondary=None,
    logic_subtype=None,
    evidence=None,
    missing_context=None,
    steps=None,
    needs_verification=False,
    verification_priority="normal",
    base_available=True,
    graph_unavailable=True,
    policy_resolved=False,
    unknown_reason=None,
    candidate_labels=None,
    gate=None,
):
    # This builds one output line in a single place so every code path
    # writes the same set of fields. The v2 schema is preserved exactly,
    # followed by the two verification fields added in v2, followed by the
    # six fields added in v3.
    return {
        "pr_key": pr_key,
        "conflict_index": conflict_index,
        "effective_index": effective_index,
        "file_path": file_path,
        "label": label,
        "secondary": secondary,
        "logic_subtype": logic_subtype,
        "confidence": confidence,
        "evidence": evidence,
        "missing_context": missing_context,
        "steps": steps if steps is not None else [],
        "reason": reason,
        "capped": capped,
        "attempt_number": attempt_number,
        "model": classify_llm.MODEL_NAME,
        "timestamp": timestamp,
        "needs_verification": needs_verification,
        "verification_priority": verification_priority,
        "base_available": base_available,
        "graph_unavailable": graph_unavailable,
        "policy_resolved": policy_resolved,
        "unknown_reason": unknown_reason,
        "candidate_labels": candidate_labels,
        "gate": gate,
    }

def read_jsonl_counts(output_path):
    # Shared reader for the two resume helpers below
    result = {}
    if not os.path.exists(output_path):
        return result
    with open(output_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            conflict_index = record.get("conflict_index")
            effective_index = (
                conflict_index if conflict_index is not None else record.get("effective_index")
            )
            key = (record.get("pr_key"), record.get("file_path"), effective_index)
            result[key] = result.get(key, 0) + 1
    return result

def load_already_labeled(output_path):
    # Which regions are done, this is what makes the script resumable
    return set(read_jsonl_counts(output_path))

def load_attempt_counts(output_path):
    # How many prior entries exist per region, used to number repeated runs
    return read_jsonl_counts(output_path)

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

def process_region(pr_key, region_position, region, outfile, api_call_counts_by_file,
                   already_labeled, attempt_counts, rows_mode):
    conflict_index = region.get("conflict_index")
    file_path = region.get("file_path")
    # A no_markers deletion region has no conflict_index of its own, so its
    # position in the regions list is used instead, this keeps two deletions
    # in the same pr_key from colliding onto the same key
    effective_index = (
        conflict_index if conflict_index is not None else f"no_markers_{region_position}"
    )
    key = (pr_key, file_path, effective_index)

    # Rows mode always runs fresh, normal mode skips what is already done
    if not rows_mode and key in already_labeled:
        return

    attempt_number = attempt_counts.get(key, 0) + 1
    timestamp = datetime.now(timezone.utc).isoformat()
    ours_text = region.get("ours_text") or ""
    theirs_text = region.get("theirs_text") or ""

    # Only model calls count toward the cap, so patterns and the ast gate
    # still run on a file that has already used up its share
    calls_so_far_for_file = api_call_counts_by_file.get(file_path, 0)
    allow_llm = calls_so_far_for_file < PER_FILE_API_CALL_CAP

    result, layer, detail = classify_region(
        file_path, ours_text, theirs_text, region.get("base_text"), region, allow_llm
    )

    STATS["total"] += 1
    if result is None:
        STATS["capped"] += 1
        output_record = build_output_record(
            pr_key, conflict_index, effective_index, file_path, attempt_number, timestamp,
            label=CAPPED_LABEL, confidence="low", reason=CAPPED_REASON, capped=True,
        )
        shown = f"{CAPPED_LABEL} (per file cap)"
    else:
        output_record = build_output_record(
            pr_key, conflict_index, effective_index, file_path, attempt_number, timestamp,
            **result,
        )
        shown = result["label"]
        if layer == "pattern":
            STATS["deterministic"] += 1
            STATS["by_pattern"][detail] = STATS["by_pattern"].get(detail, 0) + 1
            shown += f" ({detail})"
        elif layer == "ast":
            STATS["ast"] += 1
            STATS["by_equivalence"][detail] = STATS["by_equivalence"].get(detail, 0) + 1
            shown += f" (ast {detail})"
        else:
            api_call_counts_by_file[file_path] = calls_so_far_for_file + 1
        if output_record["needs_verification"]:
            STATS["needs_verification"] += 1
            shown += " needs_verification"

    RUN_LOG.append({
        "key": (pr_key, file_path, conflict_index), "layer": layer,
        "label": output_record["label"], "subtype": output_record["logic_subtype"],
    })
    outfile.write(json.dumps(output_record) + "\n")
    outfile.flush()

    if rows_mode:
        print(f"{pr_key} {file_path} region {effective_index} attempt {attempt_number}: {shown}")
    else:
        print(f"{pr_key} {file_path} region {effective_index}: {shown}")
    already_labeled.add(key)
    attempt_counts[key] = attempt_number

def run_one(input_path, output_path, rows_mode, row_start, row_end):
    reset_stats()
    if rows_mode:
        print(f"Rows mode is on, selecting lines {row_start} to {row_end}, always running fresh calls and appending, existing output is not skipped")
        already_labeled = set()
    else:
        already_labeled = load_already_labeled(output_path)
        print(f"Found {len(already_labeled)} regions already labeled, they will be skipped")
    attempt_counts = load_attempt_counts(output_path)

    with open(input_path, "r", encoding="utf-8") as infile, \
            open(output_path, "a", encoding="utf-8") as outfile:
        for line_number, line in enumerate(infile, start=1):
            if rows_mode:
                if line_number < row_start:
                    continue
                if line_number > row_end:
                    break
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
                               api_call_counts_by_file, already_labeled,
                               attempt_counts, rows_mode)
    print_report()
