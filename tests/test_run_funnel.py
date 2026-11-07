import importlib.util
import json
from pathlib import Path

import pytest

from classifier.llm import providers

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
spec = importlib.util.spec_from_file_location("run_funnel", SCRIPTS / "run_funnel.py")
run_funnel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_funnel)


def write_dataset(tmp_path):
    # One pull request per split so the filter can be checked
    train = [
        {"conflict_index": 0, "ours_text": "a", "theirs_text": "b", "file_path": "package-lock.json"},
        {"conflict_index": 1, "ours_text": "x = 1", "theirs_text": "x = 1", "file_path": "src/one.ts"},
        {"conflict_index": 2, "ours_text": "x = 1", "theirs_text": "x = 2", "file_path": "src/one.ts"},
        {"no_markers": True, "conflict_type": "deleted_by_us", "file_path": "src/gone.ts"},
    ]
    dev = [{"conflict_index": 0, "ours_text": "y = 1", "theirs_text": "y = 5", "file_path": "src/two.ts"}]
    test = [{"conflict_index": 0, "ours_text": "z = 1", "theirs_text": "z = 5", "file_path": "src/three.ts"}]
    records = [{"pr_key": "o/r#1", "regions": train}, {"pr_key": "o/r#2", "regions": dev},
               {"pr_key": "o/r#3", "regions": test}]
    (tmp_path / "data.jsonl").write_text("\n".join(json.dumps(r) for r in records) + "\n")
    split = [{"pr_key": "o/r#1", "split": "train"}, {"pr_key": "o/r#2", "split": "dev"},
             {"pr_key": "o/r#3", "split": "test"}]
    (tmp_path / "split.jsonl").write_text("\n".join(json.dumps(r) for r in split) + "\n")


def funnel_args(tmp_path, *extra):
    return ["--dataset", str(tmp_path / "data.jsonl"), "--split-file", str(tmp_path / "split.jsonl"),
            "--output-dir", str(tmp_path / "funnel"), *extra]


@pytest.fixture(autouse=True)
def no_model(monkeypatch):
    def never_call(model, system, user):
        raise AssertionError("the funnel must not call a model")
    monkeypatch.setattr(providers, "call_model", never_call)


def read_summary(tmp_path):
    return json.loads((tmp_path / "funnel" / "summary.json").read_text())


def test_the_funnel_counts_each_stage_and_what_reaches_stage_4(tmp_path, capsys):
    write_dataset(tmp_path)
    run_funnel.main(funnel_args(tmp_path))
    summary = read_summary(tmp_path)
    assert summary["pull_requests"] == 2
    assert (summary["marker_regions"], summary["typescript_regions"], summary["no_marker_records"]) == (4, 3, 1)
    assert summary["by_stage"] == {"Stage 0 scope": 0, "Stage 1 identity": 1, "Stage 2 shape": 0,
                                   "Stage 3 boundary": 1, "Reached Stage 4": 2}
    assert summary["by_stage_typescript"]["Reached Stage 4"] == 2
    rules = {(row["rule"], row["label"]) for row in summary["by_rule"]}
    assert rules == {("SameChange", "same-change"), ("Lockfile", "lockfile")}
    assert summary["no_marker_labels"] == {"business-logic-conflict": 1}
    assert "Reached Stage 4" in capsys.readouterr().out


def test_the_test_split_is_left_out_unless_asked_for(tmp_path):
    write_dataset(tmp_path)
    run_funnel.main(funnel_args(tmp_path))
    assert "o/r#3" not in (tmp_path / "funnel" / "input.jsonl").read_text()
    with pytest.raises(SystemExit):
        run_funnel.main(funnel_args(tmp_path, "--splits", "test", "--overwrite"))
    run_funnel.main(funnel_args(tmp_path, "--splits", "test", "--include-test", "--overwrite"))
    assert read_summary(tmp_path)["marker_regions"] == 1


def test_an_earlier_funnel_is_not_overwritten_without_the_flag(tmp_path):
    write_dataset(tmp_path)
    run_funnel.main(funnel_args(tmp_path))
    with pytest.raises(SystemExit):
        run_funnel.main(funnel_args(tmp_path))
    run_funnel.main(funnel_args(tmp_path, "--overwrite"))
    records = (tmp_path / "funnel" / "rules.jsonl").read_text().splitlines()
    assert len(records) == 3


def test_an_unknown_split_name_is_refused(tmp_path):
    write_dataset(tmp_path)
    with pytest.raises(SystemExit):
        run_funnel.main(funnel_args(tmp_path, "--splits", "train,valid"))
