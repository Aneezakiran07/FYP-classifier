import json

from classifier import cli, pipeline
from classifier.llm import providers


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


def install_fakes(monkeypatch):
    # Model good is right on both model-classified regions, model bad
    # always answers other at low confidence. With the v3 escape hatch,
    # other and low confidence both become unknown, so bad cannot match
    # either ground truth label.
    monkeypatch.setattr(providers, "check_available",
                        lambda m: (False, "no api key found for deepseek") if m == "deepseek-r1" else (True, ""))

    def call(model, system, user):
        if '"kind"' in system:
            return json.dumps({"kind": "semantic", "reason": "value differs"})
        if model == "good":
            subtype = ("logic/assignment-override" if "src/one.ts" in user
                       else "logic/business-logic-conflict")
            return json.dumps({"subtype": subtype, "confidence": "high", "evidence": "x"})
        return json.dumps({"subtype": "other", "confidence": "low", "evidence": "x"})
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
    # good matches both labeled model regions, bad matches neither because
    # its answer becomes unknown under the v3 escape hatch
    assert good[1:5] == ["1/3", "2/3", "2/2", "100%"]
    assert bad[3:5] == ["0/2", "0%"]


REPORT_FIELDS = ["status", "reason", "stage", "source", "base_state", "input_hash", "trace",
                 "confirming_test", "changed_names", "joint_use_lines", "provenance"]
OLD_FIELDS = ["secondary", "logic_subtype", "confidence", "evidence", "missing_context", "steps",
              "capped", "needs_verification", "verification_priority", "base_available",
              "graph_unavailable", "policy_resolved", "unknown_reason", "candidate_labels",
              "gate", "timestamp"]


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
    # Both model-classified regions from "bad" now route to verification
    # because other at low confidence becomes unknown under the v3 rule.
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