# Tests for the revalidate script on made up records and regions, with no model and no real data
# They check that a validator change turns a model label into unknown and back, and keeps the model provenance
# Others check that a region the rules now decide gets a rule record, and that a rule record now needing the model is left out
# The last ones check that llm-error and changed inputs are kept as they are, and that the input file is never overwritten

import importlib.util
import json
from pathlib import Path

import pytest

from classifier import pipeline
from classifier.llm.prompts import LOGIC_TESTS
from classifier.schema import Region

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
spec = importlib.util.spec_from_file_location("revalidate", SCRIPTS / "revalidate.py")
revalidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(revalidate)

MODEL_RAW = {"file_path": "src/a.ts", "conflict_index": 0, "base_text": "const x = get(c);",
             "ours_text": "const x = load(a);", "theirs_text": "const x = fetch(b);"}
RULE_RAW = {"file_path": "src/a.ts", "conflict_index": 1, "base_text": "x = 0",
            "ours_text": "x = 1", "theirs_text": "x = 1"}


def region(raw, pr_key="o/r#1"):
    return Region.from_raw(pr_key, 0, raw)


def model_record(raw, label, met_test, unknown_reason=None, status="classified"):
    trace = [{"stage": 4, "test": "router", "result": "passed", "reason": "they differ", "answer": "semantic"}]
    trace += [{"stage": 4, "test": t, "result": "failed", "reason": "r", "met": t == met_test,
               "evidence": "OURS: `load(a)` THEIRS: `fetch(b)`"} for t in LOGIC_TESTS]
    block = {"status": status, "reason": "why", "stage": 4, "source": "model",
             "input_hash": region(raw).input_hash, "trace": trace, "unknown_reason": unknown_reason,
             "confirming_test": label if label in LOGIC_TESTS else None, "model_calls": 2, "timestamp": "t0",
             "provenance": {"component_version": "0.1.0", "model_name": "old-model", "logic_prompt_hash": "abc"}}
    if label is not None:
        block["label"] = label
    return {"pr_key": "o/r#1", "file_path": raw["file_path"], "conflict_index": raw["conflict_index"],
            "effective_index": raw["conflict_index"], "classifier": block}


def run_one(record, raw):
    return revalidate.revalidate_record(record, region(raw), "commit1")


def test_a_validator_that_now_fails_gives_unknown_and_keeps_the_model_provenance(monkeypatch):
    monkeypatch.setattr(pipeline, "validate_logic_test", lambda *a: False)
    new, outcome = run_one(model_record(MODEL_RAW, "assignment-override", "assignment-override"), MODEL_RAW)
    block = new["classifier"]
    assert outcome == "changed"
    assert (block["label"], block["unknown_reason"], block["source"]) == ("unknown", "validator-failed", "model")
    assert block["provenance"]["model_name"] == "old-model"
    assert block["provenance"]["revalidated_commit"] == "commit1"


def test_a_validator_that_now_passes_gives_the_selected_test_label(monkeypatch):
    monkeypatch.setattr(pipeline, "validate_logic_test", lambda *a: True)
    record = model_record(MODEL_RAW, "unknown", "assignment-override", unknown_reason="validator-failed")
    new, outcome = run_one(record, MODEL_RAW)
    assert outcome == "changed"
    assert new["classifier"]["label"] == "assignment-override"
    assert new["classifier"]["confirming_test"] == "assignment-override"


def test_the_same_decision_keeps_the_record_as_it_was(monkeypatch):
    monkeypatch.setattr(pipeline, "validate_logic_test", lambda *a: True)
    record = model_record(MODEL_RAW, "assignment-override", "assignment-override")
    new, outcome = run_one(record, MODEL_RAW)
    assert outcome == "unchanged" and new is record


def test_a_region_the_rules_now_decide_gets_a_rule_record():
    new, outcome = run_one(model_record(RULE_RAW, "assignment-override", "assignment-override"), RULE_RAW)
    assert outcome == "changed"
    assert (new["classifier"]["label"], new["classifier"]["source"]) == ("same-change", "rule")


def test_a_rule_record_that_now_needs_the_model_is_left_out():
    record = model_record(MODEL_RAW, "lockfile", None)
    record["classifier"]["source"] = "rule"
    new, outcome = run_one(record, MODEL_RAW)
    assert new is None and outcome == "left out, now needs the model"


def test_llm_error_and_a_changed_input_are_kept_as_they_are():
    error = model_record(MODEL_RAW, None, None, status="llm-error")
    assert run_one(error, MODEL_RAW) == (error, "unchanged")
    stale = model_record(MODEL_RAW, "assignment-override", "assignment-override")
    stale["classifier"]["input_hash"] = "different"
    assert run_one(stale, MODEL_RAW) == (stale, "kept, input hash differs")


def test_the_input_file_is_never_overwritten(tmp_path):
    path = tmp_path / "run.jsonl"
    path.write_text(json.dumps(model_record(MODEL_RAW, "assignment-override", "assignment-override")) + "\n")
    with pytest.raises(SystemExit):
        revalidate.main([str(path), str(path)])


def test_main_writes_a_new_file_from_the_dataset(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "validate_logic_test", lambda *a: False)
    dataset = tmp_path / "data.jsonl"
    dataset.write_text(json.dumps({"pr_key": "o/r#1", "regions": [MODEL_RAW]}) + "\n")
    run = tmp_path / "run.jsonl"
    run.write_text(json.dumps(model_record(MODEL_RAW, "assignment-override", "assignment-override")) + "\n")
    out = tmp_path / "new.jsonl"
    counts, _ = revalidate.main([str(run), str(out), "--dataset", str(dataset)])
    assert counts["changed"] == 1
    assert json.loads(out.read_text())["classifier"]["label"] == "unknown"
