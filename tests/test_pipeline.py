# End to end tests for pipeline.py and cli.py with a fake model, so no real API call is made
# They cover the output record, rule and model provenance, resume, rerun, the models flag and the accuracy table
# They cover Stage 4 where the first met test wins, the trace, the validator, structural hints, router unknown and confluent interference as unknown
# They cover capped and llm-error records, the per file call ceiling, retries, retry errors, max calls and stopping after failures in a row

import json

import pytest

from classifier import cli, pipeline
from classifier.llm import prompts, providers


def write_inputs(tmp_path):
    regions = [
        {"conflict_index": 0, "ours_text": "a", "theirs_text": "b", "file_path": "package-lock.json"},
        {"conflict_index": 1, "ours_text": "x = 1", "theirs_text": "x = 2", "file_path": "src/one.ts"},
        {"conflict_index": 2, "ours_text": "y = 1", "theirs_text": "y = 5", "file_path": "src/two.ts"},
    ]
    (tmp_path / "in.jsonl").write_text(json.dumps({"pr_key": "o/r#1", "regions": regions}) + "\n")
    labels = [
        {"pr_key": "o/r#1", "file_path": "package-lock.json", "conflict_index": 0,
         "true_label": "dependency/lockfile", "notes": ""},
        {"pr_key": "o/r#1", "file_path": "src/one.ts", "conflict_index": 1,
         "true_label": "logic/assignment-override", "notes": ""},
        {"pr_key": "o/r#1", "file_path": "src/two.ts", "conflict_index": 2,
         "true_label": "logic/business-logic-conflict", "notes": ""},
    ]
    (tmp_path / "sample_labels.jsonl").write_text("\n".join(json.dumps(x) for x in labels) + "\n")


# The evidence quotes the default region in the same form the real model uses
REAL_EVIDENCE = "`OURS: x = 1`"


def logic_reply(met=(), evidence=REAL_EVIDENCE):
    return json.dumps({"tests": [{"test_id": test_id, "met": test_id in met, "evidence": evidence}
                                 for test_id in prompts.LOGIC_TESTS]})


def first_ours_line(user):
    # The first line of our side as the prompt shows it to the model
    return user.split("OURS:\n", 1)[1].splitlines()[0]


def install_fakes(monkeypatch):
    # Model good is right on both model classified regions
    # Model bad marks no test as met, so it cannot match either true label
    monkeypatch.setattr(providers, "check_available",
                        lambda m: (False, "no api key found for deepseek") if m == "deepseek-r1" else (True, ""))

    def call(model, system, user):
        if '"kind"' in system:
            return json.dumps({"kind": "semantic", "reason": "value differs"})
        if model == "good":
            test_id = "assignment-override" if "src/one.ts" in user else "business-logic-conflict"
            return logic_reply(met=[test_id], evidence=f"`OURS: {first_ours_line(user)}`")
        return logic_reply()
    monkeypatch.setattr(providers, "call_model", call)


def test_models_flag_writes_one_file_per_model_and_a_table(tmp_path, monkeypatch, capsys):
    write_inputs(tmp_path)
    install_fakes(monkeypatch)
    out = tmp_path / "out.jsonl"
    cli.main([str(tmp_path / "in.jsonl"), str(out), "--models", "good,bad,deepseek-r1", "--delay", "0"])
    text = capsys.readouterr().out

    assert (tmp_path / "out.good.jsonl").exists()
    assert (tmp_path / "out.bad.jsonl").exists()
    assert not (tmp_path / "out.deepseek-r1.jsonl").exists()
    assert "Warning, skipping deepseek-r1" in text

    header = [l for l in text.splitlines() if l.startswith("model")][0]
    for column in ("deterministic", "llm_called", "agreed_with_gt", "accuracy"):
        assert column in header
    good = [l for l in text.splitlines() if l.startswith("good")][0].split()
    bad = [l for l in text.splitlines() if l.startswith("bad")][0].split()
    # good matches both labeled model regions and bad matches neither
    assert good[1:5] == ["1/3", "2/3", "2/2", "100%"]
    assert bad[3:5] == ["0/2", "0%"]


REPORT_FIELDS = ["status", "reason", "stage", "source", "base_state", "input_hash", "trace",
                 "confirming_test", "changed_names", "joint_use_lines", "provenance"]
OLD_FIELDS = ["secondary", "logic_subtype", "confidence", "evidence", "missing_context", "steps",
              "capped", "needs_verification", "verification_priority", "base_available",
              "graph_unavailable", "policy_resolved", "unknown_reason", "candidate_labels",
              "gate", "model_calls", "timestamp"]


def read_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def test_output_record_holds_the_join_key_and_the_classifier_block(tmp_path, monkeypatch):
    write_inputs(tmp_path)
    install_fakes(monkeypatch)
    cli.main([str(tmp_path / "in.jsonl"), str(tmp_path / "out.jsonl"), "--models", "bad", "--delay", "0"])
    rows = read_rows(tmp_path / "out.bad.jsonl")
    for row in rows:
        assert list(row) == ["pr_key", "file_path", "conflict_index", "effective_index", "classifier"]
        assert list(row["classifier"]) == ["label"] + REPORT_FIELDS + OLD_FIELDS
        assert row["classifier"]["status"] == "classified"
    # Both model classified regions from bad become unknown with no test met
    flagged = [r["classifier"] for r in rows if r["classifier"]["needs_verification"]]
    assert len(flagged) == 2 and all(b["verification_priority"] == "high" for b in flagged)


def test_rule_block_has_no_model_name_and_model_block_does(tmp_path, monkeypatch):
    write_inputs(tmp_path)
    install_fakes(monkeypatch)
    out = tmp_path / "out.jsonl"
    cli.main([str(tmp_path / "in.jsonl"), str(out), "--model", "good", "--delay", "0"])
    rule, model, _ = [row["classifier"] for row in read_rows(out)]

    assert rule["label"] == "lockfile"
    assert (rule["stage"], rule["source"]) == (3, "rule")
    assert list(rule["provenance"]) == ["component_version"]

    assert model["label"] == "assignment-override"
    assert (model["stage"], model["source"]) == (4, "model")
    assert model["provenance"]["model_name"] == "good"
    assert len(model["provenance"]["router_prompt_hash"]) == 64
    assert len(model["provenance"]["logic_prompt_hash"]) == 64
    assert model["provenance"]["router_prompt_version"] == prompts.ROUTER_PROMPT_VERSION
    assert model["provenance"]["logic_prompt_version"] == prompts.LOGIC_PROMPT_VERSION
    assert model["provenance"]["component_version"] == "0.1.0"
    assert (model["base_state"], len(model["input_hash"])) == ("missing", 64)


def test_capped_region_is_recorded_with_no_label(tmp_path, monkeypatch):
    regions = [{"conflict_index": i, "ours_text": f"x = {i}", "theirs_text": f"x = {i + 9}",
                "file_path": "src/one.ts"} for i in range(2)]
    (tmp_path / "in.jsonl").write_text(json.dumps({"pr_key": "o/r#1", "regions": regions}) + "\n")
    install_fakes(monkeypatch)
    monkeypatch.setattr(pipeline, "PER_FILE_API_CALL_CAP", 1)
    out = tmp_path / "out.jsonl"
    cli.main([str(tmp_path / "in.jsonl"), str(out), "--model", "good", "--delay", "0"])
    capped = read_rows(out)[1]["classifier"]
    assert "label" not in capped
    assert capped["status"] == "capped" and capped["capped"] is True
    assert capped["reason"] == "call-ceiling"
    assert capped["source"] is None and capped["stage"] == 4
    assert capped["provenance"] == {"component_version": "0.1.0", "model_name": None}


def test_router_only_region_has_no_logic_prompt_hash(tmp_path, monkeypatch):
    write_inputs(tmp_path)
    install_fakes(monkeypatch)
    # The fake model answers unknown at the router so the logic prompt never runs
    monkeypatch.setattr(providers, "call_model",
                        lambda model, system, user: json.dumps({"kind": "unknown", "reason": "not sure"}))
    out = tmp_path / "out.jsonl"
    cli.main([str(tmp_path / "in.jsonl"), str(out), "--model", "good", "--delay", "0"])
    block = read_rows(out)[1]["classifier"]
    assert block["source"] == "model"
    assert len(block["provenance"]["router_prompt_hash"]) == 64
    assert block["provenance"]["logic_prompt_hash"] is None
    assert block["provenance"]["logic_prompt_version"] is None


def test_rerun_overwrites_only_the_keys_in_its_input(tmp_path, monkeypatch):
    write_inputs(tmp_path)
    install_fakes(monkeypatch)
    out = tmp_path / "out.jsonl"
    cli.main([str(tmp_path / "in.jsonl"), str(out), "--model", "good", "--delay", "0"])
    before = read_rows(out)

    one_region = json.loads((tmp_path / "in.jsonl").read_text())
    one_region["regions"] = one_region["regions"][1:2]
    (tmp_path / "part.jsonl").write_text(json.dumps(one_region) + "\n")
    cli.main([str(tmp_path / "part.jsonl"), str(out), "--model", "bad", "--delay", "0", "--rerun"])
    after = read_rows(out)

    assert len(after) == 3
    assert after[0] == before[0] and after[2] == before[2]
    assert after[1]["file_path"] == "src/one.ts"
    assert after[1]["classifier"]["provenance"]["model_name"] == "bad"


def test_resume_ignores_a_line_broken_by_a_crash(tmp_path, monkeypatch):
    write_inputs(tmp_path)
    install_fakes(monkeypatch)
    out = tmp_path / "out.jsonl"
    args = [str(tmp_path / "in.jsonl"), str(out), "--model", "good", "--delay", "0"]
    cli.main(args)
    rows = out.read_text().splitlines()
    out.write_text("\n".join(rows[:2]) + "\n" + rows[2][:20])
    cli.main(args)
    keys = [(r["pr_key"], r["file_path"], r["effective_index"]) for r in read_rows(out)]
    assert len(keys) == len(set(keys)) == 3


def test_single_model_run_keeps_the_output_path(tmp_path, monkeypatch, capsys):
    write_inputs(tmp_path)
    install_fakes(monkeypatch)
    out = tmp_path / "single.jsonl"
    cli.main([str(tmp_path / "in.jsonl"), str(out), "--model", "good", "--delay", "0"])
    assert out.exists()
    text = capsys.readouterr().out
    assert "deterministic matched: 1 (33.3%)" in text
    assert "LLM called:           2 (66.7%)" in text
    assert "prompt A: 2, prompt B: 2 (0 were structural)" in text


def test_resume_skips_finished_regions(tmp_path, monkeypatch, capsys):
    write_inputs(tmp_path)
    install_fakes(monkeypatch)
    args = [str(tmp_path / "in.jsonl"), str(tmp_path / "out.jsonl"), "--model", "good", "--delay", "0"]
    cli.main(args)
    cli.main(args)
    assert len((tmp_path / "out.jsonl").read_text().splitlines()) == 3

def one_region_block(tmp_path, monkeypatch, call, region=None):
    # Runs one TypeScript region through the pipeline with a fake model
    install_fakes(monkeypatch)
    monkeypatch.setattr(providers, "call_model", call)
    raw_region = {"conflict_index": 0, "ours_text": "x = 1", "theirs_text": "x = 2", "file_path": "src/one.ts"}
    raw_region.update(region or {})
    (tmp_path / "in.jsonl").write_text(json.dumps({"pr_key": "o/r#1", "regions": [raw_region]}) + "\n")
    out = tmp_path / "out.jsonl"
    cli.main([str(tmp_path / "in.jsonl"), str(out), "--model", "good", "--delay", "0"])
    return read_rows(out)[0]["classifier"]


def semantic_then(reply):
    def call(model, system, user):
        return json.dumps({"kind": "semantic", "reason": "value differs"}) if '"kind"' in system else reply
    return call


def trace_results(block):
    return {entry["test"]: entry["result"] for entry in block["trace"]}


# One side guards the call and the other does not, so the control flow check holds
CONTROL_FLOW_REGION = {"ours_text": "if (ready) {\n  start()\n}", "theirs_text": "start()"}
CONTROL_FLOW_EVIDENCE = "`OURS: if (ready) {`"


def test_the_pipeline_selects_the_first_met_test(tmp_path, monkeypatch):
    reply = logic_reply(met=["execution-perturbation", "assignment-override", "business-logic-conflict"],
                        evidence=CONTROL_FLOW_EVIDENCE)
    block = one_region_block(tmp_path, monkeypatch, semantic_then(reply), CONTROL_FLOW_REGION)
    assert block["label"] == "execution-perturbation"
    assert (block["stage"], block["source"], block["status"]) == (4, "model", "classified")
    assert block["evidence"] == CONTROL_FLOW_EVIDENCE and block["reason"] == "value differs"


def test_the_trace_shows_every_test_and_the_validator(tmp_path, monkeypatch):
    reply = logic_reply(met=["execution-perturbation", "assignment-override"], evidence=CONTROL_FLOW_EVIDENCE)
    block = one_region_block(tmp_path, monkeypatch, semantic_then(reply), CONTROL_FLOW_REGION)
    assert trace_results(block) == {
        "router": "passed",
        "null-safety-conflict": "failed",
        "type-incompatibility": "failed",
        "execution-perturbation": "passed",
        "overlap-contamination": "skipped",
        "assignment-override": "skipped",
        "confluent-interference": "skipped",
        "business-logic-conflict": "skipped",
        "validator": "passed",
    }
    # A later test the model marked as met keeps its answer in the trace
    later = [entry for entry in block["trace"] if entry["test"] == "assignment-override"][0]
    assert later["met"] is True and later["evidence"] == CONTROL_FLOW_EVIDENCE
    assert block["trace"][-1]["test_id"] == "execution-perturbation"
    assert all(entry["reason"] for entry in block["trace"])


def test_a_confirmed_label_stays_flagged_for_verification(tmp_path, monkeypatch):
    block = one_region_block(tmp_path, monkeypatch, semantic_then(logic_reply(met=["assignment-override"])))
    assert block["label"] == "assignment-override"
    assert block["needs_verification"] is True and block["verification_priority"] == "normal"
    assert block["trace"][-1]["test"] == "validator" and block["trace"][-1]["result"] == "passed"


def test_evidence_that_is_not_in_the_region_fails_the_validator(tmp_path, monkeypatch):
    reply = logic_reply(met=["assignment-override"], evidence="`OURS: y = 7`")
    block = one_region_block(tmp_path, monkeypatch, semantic_then(reply))
    assert block["label"] == "unknown" and block["unknown_reason"] == pipeline.VALIDATOR_FAILED
    assert block["reason"] and block["status"] == "classified"
    assert (block["stage"], block["source"]) == (4, "model")
    assert block["needs_verification"] is True and block["verification_priority"] == "high"
    assert block["confirming_test"] is None
    assert trace_results(block)["validator"] == "failed"
    assert block["trace"][-1]["reason"] == pipeline.VALIDATOR_FAILED


def test_a_test_check_that_fails_on_the_region_fails_the_validator(tmp_path, monkeypatch):
    # The evidence is real but the region has no control flow change
    reply = logic_reply(met=["execution-perturbation", "assignment-override"])
    block = one_region_block(tmp_path, monkeypatch, semantic_then(reply))
    assert block["label"] == "unknown" and block["unknown_reason"] == pipeline.VALIDATOR_FAILED
    # A later met test does not take over after the validator fails
    assert trace_results(block)["assignment-override"] == "skipped"
    assert block["trace"][-1]["test_id"] == "execution-perturbation"


def test_no_test_met_is_unknown_with_a_reason(tmp_path, monkeypatch):
    block = one_region_block(tmp_path, monkeypatch, semantic_then(logic_reply()))
    assert block["label"] == "unknown" and block["unknown_reason"] == "no-test-met"
    assert block["reason"] and block["status"] == "classified"
    assert "validator" not in trace_results(block)


def test_a_structural_hint_is_never_a_label_and_skips_the_logic_prompt(tmp_path, monkeypatch):
    calls = []

    def call(model, system, user):
        calls.append(system)
        return json.dumps({"kind": "structural", "reason": "moved"})
    block = one_region_block(tmp_path, monkeypatch, call)
    assert len(calls) == 1
    assert block["label"] == "unknown" and block["unknown_reason"] == "ambiguous"
    assert block["candidate_labels"] is None
    assert block["provenance"]["logic_prompt_hash"] is None
    assert trace_results(block)["confirm-structural"] == "failed"
    assert block["trace"][-1]["reason"] == pipeline.STRUCTURAL_NOT_CONFIRMED


def structural_reply(model, system, user):
    return json.dumps({"kind": "structural", "reason": "moved"})


def test_a_structural_hint_confirmed_by_a_rule_is_a_model_label(tmp_path, monkeypatch):
    # The rule answers with the old family prefix and the pipeline writes the bare name
    monkeypatch.setattr(pipeline, "confirm_structural", lambda region, verdict: "structural/rename")
    block = one_region_block(tmp_path, monkeypatch, structural_reply)
    assert block["label"] == "rename" and block["reason"] == "moved"
    assert (block["stage"], block["source"], block["status"]) == (4, "model", "classified")
    assert block["confirming_test"] == "confirm-structural"
    assert block["needs_verification"] is True and block["verification_priority"] == "normal"
    assert trace_results(block)["confirm-structural"] == "passed"
    assert block["trace"][-1]["label"] == "rename"
    assert block["provenance"]["logic_prompt_hash"] is None


def test_a_rule_that_confirms_a_hint_with_a_logic_label_stops_the_run(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "confirm_structural", lambda region, verdict: "assignment-override")
    with pytest.raises(ValueError):
        one_region_block(tmp_path, monkeypatch, structural_reply)


def test_a_router_unknown_keeps_the_reason_of_the_model(tmp_path, monkeypatch):
    block = one_region_block(tmp_path, monkeypatch,
                             lambda m, s, u: json.dumps({"kind": "unknown", "reason": "too little text"}))
    assert block["label"] == "unknown" and block["reason"] == "too little text"
    assert block["unknown_reason"] == "router-unknown"


def test_the_model_sees_the_base_of_the_region(tmp_path, monkeypatch):
    seen = []

    def call(model, system, user):
        seen.append(user)
        return json.dumps({"kind": "unknown", "reason": "not sure"})
    one_region_block(tmp_path, monkeypatch, call, {"base_text": "x = 0"})
    assert "BASE:\nx = 0" in seen[0]


def test_a_failed_call_after_the_router_is_llm_error_with_no_label(tmp_path, monkeypatch):
    block = one_region_block(tmp_path, monkeypatch, semantic_then("garbage"))
    assert "label" not in block
    assert (block["status"], block["reason"]) == ("llm-error", "invalid-answer")
    assert (block["stage"], block["source"]) == (4, None)
    assert trace_results(block) == {"router": "passed", "model-call": "failed"}
    assert block["provenance"]["model_name"] == "good"
    assert len(block["provenance"]["logic_prompt_hash"]) == 64
    # One router reply plus the logic reply and its single retry
    assert block["model_calls"] == 3


def test_a_router_failure_has_no_logic_prompt_hash(tmp_path, monkeypatch):
    block = one_region_block(tmp_path, monkeypatch, lambda m, s, u: "garbage")
    assert block["status"] == "llm-error" and block["provenance"]["logic_prompt_hash"] is None


def fail_with(error):
    def call(model, system, user):
        raise error
    return call


def test_truncated_output_is_llm_error_with_its_own_reason(tmp_path, monkeypatch):
    block = one_region_block(tmp_path, monkeypatch, fail_with(providers.TruncatedOutput("good ran out of length")))
    assert (block["status"], block["reason"]) == ("llm-error", "truncated-output")


def test_a_selected_confluent_test_is_unknown_and_later_tests_do_not_take_over(tmp_path, monkeypatch):
    reply = logic_reply(met=["confluent-interference", "business-logic-conflict"])
    block = one_region_block(tmp_path, monkeypatch, semantic_then(reply))
    assert block["label"] == "unknown" and block["unknown_reason"] == "no-context-lines"
    assert trace_results(block)["confluent-interference"] == "passed"
    assert trace_results(block)["context-lines"] == "failed"
    assert block["confirming_test"] is None


def test_confirming_test_names_what_decided_the_label(tmp_path, monkeypatch):
    block = one_region_block(tmp_path, monkeypatch, semantic_then(logic_reply(met=["assignment-override"])))
    assert block["confirming_test"] == "assignment-override"
    write_inputs(tmp_path)
    cli.main([str(tmp_path / "in.jsonl"), str(tmp_path / "all.jsonl"), "--model", "good", "--delay", "0"])
    assert read_rows(tmp_path / "all.jsonl")[0]["classifier"]["confirming_test"] == "Lockfile"
    assert read_rows(tmp_path / "all.jsonl")[0]["classifier"]["joint_use_lines"] == []


def regions_in_one_file(tmp_path, count):
    regions = [{"conflict_index": i, "ours_text": f"x = {i}", "theirs_text": f"x = {i + 9}",
                "file_path": "src/one.ts"} for i in range(count)]
    (tmp_path / "in.jsonl").write_text(json.dumps({"pr_key": "o/r#1", "regions": regions}) + "\n")
    return [str(tmp_path / "in.jsonl"), str(tmp_path / "out.jsonl"), "--model", "good", "--delay", "0"]


def test_the_ceiling_counts_calls_not_regions(tmp_path, monkeypatch):
    args = regions_in_one_file(tmp_path, 3)
    install_fakes(monkeypatch)
    # A semantic region uses two calls, so two regions reach this ceiling of four
    monkeypatch.setattr(pipeline, "PER_FILE_API_CALL_CAP", 4)
    cli.main(args)
    statuses = [row["classifier"]["status"] for row in read_rows(tmp_path / "out.jsonl")]
    assert statuses == ["classified", "classified", "capped"]


def test_the_ceiling_survives_a_resume(tmp_path, monkeypatch):
    args = regions_in_one_file(tmp_path, 3)
    install_fakes(monkeypatch)
    monkeypatch.setattr(pipeline, "PER_FILE_API_CALL_CAP", 4)
    cli.main(args)
    rows = (tmp_path / "out.jsonl").read_text().splitlines()
    (tmp_path / "out.jsonl").write_text("\n".join(rows[:2]) + "\n")
    cli.main(args)
    assert read_rows(tmp_path / "out.jsonl")[2]["classifier"]["status"] == "capped"


def test_the_ceiling_is_per_file_within_a_pull_request(tmp_path, monkeypatch):
    regions = [{"conflict_index": i, "ours_text": f"x = {i}", "theirs_text": f"x = {i + 9}",
                "file_path": f"src/{name}.ts"} for i, name in enumerate(["one", "two"])]
    (tmp_path / "in.jsonl").write_text(json.dumps({"pr_key": "o/r#1", "regions": regions}) + "\n")
    install_fakes(monkeypatch)
    monkeypatch.setattr(pipeline, "PER_FILE_API_CALL_CAP", 2)
    cli.main([str(tmp_path / "in.jsonl"), str(tmp_path / "out.jsonl"), "--model", "good", "--delay", "0"])
    assert [row["classifier"]["status"] for row in read_rows(tmp_path / "out.jsonl")] == ["classified"] * 2


def test_a_transport_outage_is_llm_error_and_never_capped(tmp_path, monkeypatch):
    args = regions_in_one_file(tmp_path, 3) + ["--max-retries", "2"]
    install_fakes(monkeypatch)
    monkeypatch.setattr(pipeline, "PER_FILE_API_CALL_CAP", 1)
    monkeypatch.setattr(providers, "call_model", fail_with(ConnectionError("down")))
    cli.main(args)
    blocks = [row["classifier"] for row in read_rows(tmp_path / "out.jsonl")]
    assert [b["reason"] for b in blocks] == ["transport-error"] * 3
    assert all("label" not in b and b["model_calls"] == 0 for b in blocks)


def test_llm_error_is_skipped_on_resume_and_retried_only_with_the_flag(tmp_path, monkeypatch):
    args = regions_in_one_file(tmp_path, 1) + ["--max-retries", "1"]
    install_fakes(monkeypatch)
    healthy = providers.call_model
    monkeypatch.setattr(providers, "call_model", fail_with(RuntimeError("down")))
    cli.main(args)
    assert read_rows(tmp_path / "out.jsonl")[0]["classifier"]["status"] == "llm-error"

    monkeypatch.setattr(providers, "call_model", healthy)
    cli.main(args)
    assert read_rows(tmp_path / "out.jsonl")[0]["classifier"]["status"] == "llm-error"

    cli.main(args + ["--retry-errors"])
    rows = read_rows(tmp_path / "out.jsonl")
    assert len(rows) == 1 and rows[0]["classifier"]["status"] == "classified"


def test_retry_errors_leaves_finished_regions_alone(tmp_path, monkeypatch):
    write_inputs(tmp_path)
    install_fakes(monkeypatch)
    out = tmp_path / "out.jsonl"
    args = [str(tmp_path / "in.jsonl"), str(out), "--model", "good", "--delay", "0"]
    cli.main(args)
    before = read_rows(out)
    cli.main(args + ["--retry-errors"])
    assert read_rows(out) == before


@pytest.mark.parametrize("extra", [["--models", "good"], ["--rerun"]])
def test_retry_errors_refuses_other_run_modes(tmp_path, extra):
    args = [str(tmp_path / "in.jsonl"), str(tmp_path / "out.jsonl"), "--retry-errors"] + extra
    with pytest.raises(SystemExit):
        cli.main(args)


def test_max_retries_must_be_at_least_one(tmp_path):
    with pytest.raises(SystemExit):
        cli.main([str(tmp_path / "in.jsonl"), str(tmp_path / "out.jsonl"), "--max-retries", "0"])


def test_a_missing_key_stops_before_any_record_is_written(tmp_path, monkeypatch):
    write_inputs(tmp_path)
    monkeypatch.setattr(providers, "check_available", lambda m: (False, "no api key found"))
    with pytest.raises(SystemExit):
        cli.main([str(tmp_path / "in.jsonl"), str(tmp_path / "out.jsonl"), "--model", "good"])
    assert not (tmp_path / "out.jsonl").exists()


def test_llm_error_is_not_scored_as_wrong(tmp_path, monkeypatch, capsys):
    write_inputs(tmp_path)
    install_fakes(monkeypatch)
    monkeypatch.setattr(providers, "call_model", fail_with(providers.TruncatedOutput("cut")))
    cli.main([str(tmp_path / "in.jsonl"), str(tmp_path / "out.jsonl"), "--models", "good", "--delay", "0"])
    good = [l for l in capsys.readouterr().out.splitlines() if l.startswith("good")][0].split()
    assert good[3:5] == ["0/0", "n/a"]


def test_max_calls_stops_the_run_and_a_second_run_resumes(tmp_path, monkeypatch, capsys):
    args = regions_in_one_file(tmp_path, 4) + ["--max-calls", "3"]
    install_fakes(monkeypatch)
    cli.main(args)
    # The second region starts below the limit and finishes, so a run can pass it slightly
    assert len(read_rows(tmp_path / "out.jsonl")) == 2
    assert "reached the limit of 3 model calls" in capsys.readouterr().out
    cli.main(args)
    assert len(read_rows(tmp_path / "out.jsonl")) == 4


def test_failures_in_a_row_stop_the_run_with_the_rest_unwritten(tmp_path, monkeypatch, capsys):
    args = regions_in_one_file(tmp_path, 6) + ["--max-retries", "1"]
    install_fakes(monkeypatch)
    monkeypatch.setattr(pipeline, "MAX_CONSECUTIVE_LLM_ERRORS", 2)
    monkeypatch.setattr(providers, "call_model", fail_with(RuntimeError("down")))
    cli.main(args)
    assert len(read_rows(tmp_path / "out.jsonl")) == 2
    assert "2 model failures in a row" in capsys.readouterr().out


def test_a_good_answer_resets_the_failures_in_a_row(tmp_path, monkeypatch):
    args = regions_in_one_file(tmp_path, 5) + ["--max-retries", "1"]
    install_fakes(monkeypatch)
    monkeypatch.setattr(pipeline, "MAX_CONSECUTIVE_LLM_ERRORS", 2)
    calls = []

    def flaky(model, system, user):
        calls.append(1)
        if len(calls) % 3 == 1:
            raise RuntimeError("down")
        return json.dumps({"kind": "unknown", "reason": "not sure"})
    monkeypatch.setattr(providers, "call_model", flaky)
    cli.main(args)
    assert len(read_rows(tmp_path / "out.jsonl")) == 5


def test_token_usage_is_counted_and_printed(tmp_path, monkeypatch, capsys):
    args = regions_in_one_file(tmp_path, 1)
    install_fakes(monkeypatch)

    def call(model, system, user):
        providers.USAGE["input"] += 10
        providers.USAGE["output"] += 2
        return json.dumps({"kind": "unknown", "reason": "not sure"})
    monkeypatch.setattr(providers, "call_model", call)
    cli.main(args)
    assert "tokens for good: 10 input, 2 output" in capsys.readouterr().out


def test_provenance_records_the_real_model_and_not_the_alias(tmp_path, monkeypatch):
    args = regions_in_one_file(tmp_path, 1)
    args[args.index("good")] = "hackclub-classify"
    install_fakes(monkeypatch)
    cli.main(args)
    block = read_rows(tmp_path / "out.jsonl")[0]["classifier"]
    assert block["provenance"]["model_name"] == "hackclub/openai/gpt-6-luna"


def never_call(model, system, user):
    raise AssertionError("the model must not be called with --no-llm")


def test_no_llm_writes_only_rule_records_and_calls_no_model(tmp_path, monkeypatch, capsys):
    write_inputs(tmp_path)
    install_fakes(monkeypatch)
    monkeypatch.setattr(providers, "call_model", never_call)
    # No key is needed because no model is called
    monkeypatch.setattr(providers, "check_available", lambda m: (False, "no api key found"))
    out = tmp_path / "out.jsonl"
    cli.main([str(tmp_path / "in.jsonl"), str(out), "--no-llm"])
    rows = read_rows(out)
    assert [row["file_path"] for row in rows] == ["package-lock.json"]
    assert rows[0]["classifier"]["source"] == "rule"
    text = capsys.readouterr().out
    assert "reached Stage 4 with the model off, no record written: 2" in text
    assert "capped:" not in text


def test_a_normal_run_after_no_llm_classifies_only_the_stage_4_regions(tmp_path, monkeypatch):
    write_inputs(tmp_path)
    install_fakes(monkeypatch)
    out = tmp_path / "out.jsonl"
    cli.main([str(tmp_path / "in.jsonl"), str(out), "--no-llm"])
    rule_record = read_rows(out)[0]
    cli.main([str(tmp_path / "in.jsonl"), str(out), "--model", "good", "--delay", "0"])
    rows = read_rows(out)
    assert len(rows) == 3 and rows[0] == rule_record
    assert [row["classifier"]["source"] for row in rows] == ["rule", "model", "model"]


@pytest.mark.parametrize("extra", [["--models", "good"], ["--retry-errors"], ["--max-calls", "5"], ["--rerun"]])
def test_no_llm_refuses_options_that_need_a_model_or_mix_old_records(tmp_path, extra):
    args = [str(tmp_path / "in.jsonl"), str(tmp_path / "out.jsonl"), "--no-llm"] + extra
    with pytest.raises(SystemExit):
        cli.main(args)
