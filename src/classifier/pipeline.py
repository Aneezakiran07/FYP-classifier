# stages 0 to 5 orchestration and record writing
# this module is shared and changes need both owners to agree
# it is the only place that calls both rules and llm

import json
import os
import re
from collections import Counter
from datetime import datetime, timezone
from functools import lru_cache
from importlib import metadata
from pathlib import Path

from classifier.llm import classify_llm, prompt_builder, prompts, providers, route, run_logic_tests
from classifier.report import RUN_LOG, STATS, print_report, reset_stats
from classifier.rules.ast_gate import GATE_LABELS, apply_guards
from classifier.rules.patterns import ClassifyInput, classify_before_gate, classify_boundary_stage
from classifier.rules.validators import confirm_structural, validate_logic_test
from classifier.schema import (
    Region,
    Result,
    SOURCE_MODEL,
    SOURCE_RULE,
    STATUS_CAPPED,
    STATUS_CLASSIFIED,
    STATUS_LLM_ERROR,
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

# Once a single file within one pr_key has used this many model calls, any
# further regions in that file that need the model are capped
# A region that starts below the ceiling finishes, so a file can pass it slightly
PER_FILE_API_CALL_CAP = 50

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
IDENTITY_STAGE = 1
AST_GATE_STAGE = 2
LLM_STAGE = 4

# The reason recorded when the validator does not confirm the selected test
VALIDATOR_FAILED = "validator-failed"

# The reason recorded when no rule confirms a structural hint of the model
STRUCTURAL_NOT_CONFIRMED = "structural-not-confirmed"

# The only labels a confirmed structural hint can give at Stage 4
STRUCTURAL_LABELS = ("formatting", "documentation", "import-restructure", "rename")

# This many failures in a row means the model or the budget is gone, so the run stops
# and the regions it has not reached stay unwritten for a later resume
MAX_CONSECUTIVE_LLM_ERRORS = 10

# The logic label that stays unknown while the data has no surrounding lines
NEEDS_CONTEXT_TEST = "confluent-interference"
NO_CONTEXT_REASON = "no-context-lines"

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
    "model_calls": 0,
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
        provenance["model_name"] = providers.resolve_model(classify_llm.MODEL_NAME)
        provenance["router_prompt_hash"] = prompt_builder.system_prompt_hash("A")
        provenance["router_prompt_version"] = prompts.ROUTER_PROMPT_VERSION
        provenance["logic_prompt_hash"] = (
            prompt_builder.system_prompt_hash("B") if logic_prompt_ran else None
        )
        provenance["logic_prompt_version"] = prompts.LOGIC_PROMPT_VERSION if logic_prompt_ran else None
    return provenance


def find_stage(layer, detail):
    if layer == "pattern":
        return STAGE_BY_PATTERN[detail]
    if layer == "ast":
        return IDENTITY_STAGE if detail == "identical" else AST_GATE_STAGE
    return LLM_STAGE


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
        trace=result.get("trace", []),
        confirming_test=result.get("confirming_test") or detail,
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


def build_error_block(region, result, timestamp):
    # A failed model call decided nothing, so it has no label and no source
    values = {"base_available": bool(region.base_text), "model_calls": result.get("model_calls", 0)}
    return Result(
        status=STATUS_LLM_ERROR,
        stage=LLM_STAGE,
        reason=result["reason"],
        base_state=region.base_state,
        input_hash=region.input_hash,
        trace=result["trace"],
        provenance=build_provenance("llm", result["logic_prompt_ran"]),
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


def pattern_result(matched, has_base):
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


def unknown_from_model(reason, unknown_reason):
    # The pipeline says it does not know and hands the region to verification
    return {
        "label": "unknown", "reason": reason,
        "needs_verification": True, "verification_priority": "high",
        "unknown_reason": unknown_reason,
    }


def trace_entry(test, result, reason, **details):
    return {"stage": LLM_STAGE, "test": test, "result": result, "reason": reason, **details}


def logic_test_entries(answers, selected):
    # Tests before the selected one failed and tests after it were never used
    # The answer of the model is kept on every entry so nothing it said is lost
    entries = []
    selected_position = answers.index(selected) if selected is not None else len(answers)
    for position, answer in enumerate(answers):
        if position == selected_position:
            result, reason = "passed", "first test the model marked as met"
        elif position > selected_position:
            result, reason = "skipped", "an earlier test was selected"
        else:
            result, reason = "failed", "the model marked this test as not met"
        entries.append(trace_entry(answer.test_id, result, reason, met=answer.met, evidence=answer.evidence))
    return entries


def select_logic_label(stage_region, routed, answers, trace):
    # The pipeline picks the first met test and the model never names the label
    # A rule then checks the evidence and the region before the label is written
    selected = next((answer for answer in answers if answer.met), None)
    trace.extend(logic_test_entries(answers, selected))
    if selected is None:
        return unknown_from_model("the model marked no logic test as met", "no-test-met")
    if selected.test_id == NEEDS_CONTEXT_TEST:
        # The joint use cannot be checked without lines around the region
        trace.append(trace_entry("context-lines", "failed", NO_CONTEXT_REASON))
        return unknown_from_model("the joint use cannot be checked without context lines", NO_CONTEXT_REASON)
    if not validate_logic_test(stage_region, selected.test_id, selected.evidence):
        # A later met test does not take over because the first met test is the answer
        trace.append(trace_entry("validator", "failed", VALIDATOR_FAILED, test_id=selected.test_id))
        return unknown_from_model("the validator did not confirm the selected test", VALIDATOR_FAILED)
    trace.append(trace_entry("validator", "passed", "the evidence and the test check held",
                             test_id=selected.test_id))
    # The validator is a cheap text check so a person still reviews the label
    return {
        "label": selected.test_id, "reason": routed["reason"], "evidence": selected.evidence,
        "confirming_test": selected.test_id,
        "needs_verification": True, "verification_priority": "normal",
    }


def confirm_structural_hint(stage_region, eq, routed, trace):
    # A structural hint of the model becomes a label only when a rule confirms it
    # The label counts as a model decision because the rule only ran after the hint
    confirmed = confirm_structural(stage_region, eq)
    if confirmed is None:
        trace.append(trace_entry("confirm-structural", "failed", STRUCTURAL_NOT_CONFIRMED))
        return unknown_from_model("the model hinted structural and no check confirmed it", "ambiguous")
    label = strip_family(confirmed)
    if label not in STRUCTURAL_LABELS:
        # A rule that confirms a structural hint with another label is a bug in the rule
        raise ValueError(f"confirm_structural returned {confirmed!r}, which is not a structural label")
    trace.append(trace_entry("confirm-structural", "passed", "a rule confirmed the structural hint", label=label))
    return {
        "label": label, "reason": routed["reason"], "confirming_test": "confirm-structural",
        "needs_verification": True, "verification_priority": "normal",
    }


def run_stage_4(stage_region, eq, trace):
    routed = route(stage_region, eq)
    trace.append(trace_entry("router", "passed", routed["reason"], answer=routed["kind"]))
    if routed["kind"] == "structural":
        return confirm_structural_hint(stage_region, eq, routed, trace)
    if routed["kind"] == "unknown":
        return unknown_from_model(routed["reason"], "router-unknown")
    return select_logic_label(stage_region, routed, run_logic_tests(stage_region, eq), trace)


def classify_with_llm(file_path, ours_text, theirs_text, eq, region):
    # A failed call is recorded as llm-error with no label and never as unknown
    calls_before = STATS["model_calls"]
    stage_region = Region.from_raw(None, 0, {
        **region, "file_path": file_path, "ours_text": ours_text, "theirs_text": theirs_text,
    })
    trace = []
    try:
        result = run_stage_4(stage_region, eq, trace)
    except classify_llm.ModelCallFailed as e:
        trace.append(trace_entry("model-call", "failed", str(e)))
        result = {"status": STATUS_LLM_ERROR, "reason": e.code}
    result["trace"] = trace
    result["model_calls"] = STATS["model_calls"] - calls_before
    result["logic_prompt_ran"] = any(entry.get("answer") == "semantic" for entry in trace)
    return result


def classify_region(file_path, ours_text, theirs_text, base_text=None, region=None, allow_llm=True):
    # Runs the stages in order, patterns of stages 0 to 2, then the ast gate
    # with its guards, then the patterns of Stage 3, then the model
    # Returns the result fields plus the layer that decided and a detail
    # such as the pattern name
    # A None result means the region needed the model but the per file cap did not allow it
    has_base = bool(base_text)
    h = ClassifyInput(file_path, ours_text, theirs_text, base_text=base_text, region=region)
    matched = classify_before_gate(h)
    if matched is not None:
        return pattern_result(matched, has_base)

    eq = None
    if AST_DIFF_AVAILABLE:
        eq = apply_guards(
            compute_ast_equivalence(file_path, ours_text, theirs_text), ours_text, theirs_text
        )
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

    matched = classify_boundary_stage(h)
    if matched is not None:
        return pattern_result(matched, has_base)

    if not allow_llm:
        return None, None, None

    llm_result = classify_with_llm(
        file_path, ours_text, theirs_text, eq, {**(region or {}), "base_text": base_text}
    )
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


def process_region(pr_key, region_position, raw_region, outfile, calls_used_by_file,
                   finished_keys):
    region = Region.from_raw(pr_key, region_position, raw_region)
    if region.key in finished_keys:
        return

    timestamp = datetime.now(timezone.utc).isoformat()

    # Only model calls count toward the cap, so patterns and the ast gate
    # still run on a file that has already used up its share
    file_key = (pr_key, region.file_path)
    allow_llm = calls_used_by_file[file_key] < PER_FILE_API_CALL_CAP

    result, layer, detail = classify_region(
        region.file_path, region.ours_text, region.theirs_text, region.base_text,
        raw_region, allow_llm,
    )

    STATS["total"] += 1
    if result is None:
        STATS["capped"] += 1
        block = build_capped_block(region, timestamp)
        shown = f"{STATUS_CAPPED} (per file cap)"
    elif result.get("status") == STATUS_LLM_ERROR:
        STATS["llm_error"] += 1
        STATS["consecutive_llm_errors"] += 1
        block = build_error_block(region, result, timestamp)
        shown = f"{STATUS_LLM_ERROR} ({block['reason']})"
    else:
        block = build_classified_block(region, result, layer, detail, timestamp)
        shown = count_decision(block, layer, detail)
        if layer == "llm":
            STATS["consecutive_llm_errors"] = 0
    calls_used_by_file[file_key] += block["model_calls"]

    RUN_LOG.append({
        "key": (pr_key, region.file_path, region.conflict_index), "layer": layer,
        "label": block.get("label"), "subtype": block["logic_subtype"],
    })
    outfile.write(json.dumps(build_output_record(region, block)) + "\n")
    outfile.flush()

    print(f"{pr_key} {region.file_path} region {region.effective_index}: {shown}")
    finished_keys.add(region.key)


def is_llm_error(record):
    return record["classifier"]["status"] == STATUS_LLM_ERROR


def count_calls_by_file(records):
    # Rebuilds the call count of each file so the ceiling survives a resume
    counts = Counter()
    for (pr_key, file_path, _), record in records.items():
        counts[(pr_key, file_path)] += record["classifier"].get("model_calls", 0)
    return counts


def reason_to_stop(max_calls):
    if max_calls and STATS["model_calls"] >= max_calls:
        return f"reached the limit of {max_calls} model calls"
    if STATS["consecutive_llm_errors"] >= MAX_CONSECUTIVE_LLM_ERRORS:
        return f"{MAX_CONSECUTIVE_LLM_ERRORS} model failures in a row"
    return None


def process_input(infile, outfile, calls_used_by_file, finished_keys, max_calls):
    # Returns why the run stopped early, or None when every region was reached
    for line in infile:
        line = line.strip()
        if not line:
            continue
        record = json.loads(line)
        pr_key = record.get("pr_key")
        regions = record.get("regions", [])
        if len(regions) > LARGE_PR_KEY_REGION_WARNING_THRESHOLD:
            print(f"Warning, {pr_key} has {len(regions)} regions, this may take a while")

        for region_position, region in enumerate(regions):
            stop = reason_to_stop(max_calls)
            if stop:
                return stop
            process_region(pr_key, region_position, region, outfile,
                           calls_used_by_file, finished_keys)
    return None


def run_one(input_path, output_path, rerun=False, retry_errors=False, max_calls=None):
    # A normal run skips finished keys so it can resume after stopping
    # An llm-error counts as finished unless this is a retry run for those errors
    # A rerun processes every key in the input and overwrites only those keys
    reset_stats()
    compact_output(output_path)
    records = {} if rerun else read_records(output_path)
    if retry_errors:
        records = {key: record for key, record in records.items() if not is_llm_error(record)}
    finished_keys = set(records)
    calls_used_by_file = count_calls_by_file(records)
    if rerun:
        print("Rerun is on, every region in the input is classified again and overwritten")
    else:
        print(f"Found {len(finished_keys)} regions already finished, they will be skipped")

    with open(input_path, "r", encoding="utf-8") as infile, \
            open(output_path, "a", encoding="utf-8") as outfile:
        stop = process_input(infile, outfile, calls_used_by_file, finished_keys, max_calls)
    compact_output(output_path)
    if stop:
        print(f"Stopped early, {stop}. Run the same command again to resume")
    print_report()
