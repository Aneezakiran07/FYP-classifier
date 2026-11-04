import json

from classifier import cli
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


def test_output_schema_carries_the_two_verification_and_six_v3_fields(tmp_path, monkeypatch):
    write_inputs(tmp_path)
    install_fakes(monkeypatch)
    cli.main([str(tmp_path / "in.jsonl"), str(tmp_path / "out.jsonl"), "--models", "bad", "--delay", "0"])
    rows = [json.loads(l) for l in (tmp_path / "out.bad.jsonl").read_text().splitlines()]
    v2_keys = ["pr_key", "conflict_index", "effective_index", "file_path", "label", "secondary",
               "logic_subtype", "confidence", "evidence", "missing_context", "steps", "reason",
               "capped", "attempt_number", "model", "timestamp"]
    v2_extra = ["needs_verification", "verification_priority"]
    v3_extra = ["base_available", "graph_unavailable", "policy_resolved",
                "unknown_reason", "candidate_labels", "gate"]
    for row in rows:
        assert list(row) == v2_keys + v2_extra + v3_extra
    # Both model-classified regions from "bad" now route to verification
    # because other at low confidence becomes unknown under the v3 rule.
    flagged = [r for r in rows if r["needs_verification"]]
    assert len(flagged) == 2 and all(r["verification_priority"] == "high" for r in flagged)


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