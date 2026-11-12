# Tests for the compare_validators script on a tiny made up run, with no model and no real data
# One checks that a model answer the new validators accept and an old stand in rejects is listed as newly passing
# Another checks that records from the test split are never read
# The last one checks that asking for the test split is refused

import importlib.util
import json
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
spec = importlib.util.spec_from_file_location("compare_validators", SCRIPTS / "compare_validators.py")
compare_validators = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compare_validators)

TESTS = ["null-safety-conflict", "type-incompatibility", "execution-perturbation", "overlap-contamination",
         "assignment-override", "confluent-interference", "business-logic-conflict"]
REGION = {"conflict_index": 0, "file_path": "src/a.ts", "base_text": "x = 1",
          "ours_text": "return res.status(200).json(data);", "theirs_text": "return res.status(500).json(err);"}


def trace():
    entries = [{"test": "router", "answer": "semantic", "reason": "behavior differs"}]
    for test in TESTS:
        met = test == "business-logic-conflict"
        entries.append({"test": test, "met": met, "evidence": "OURS: `return res.status(200)...`" if met else ""})
    return entries


def write_run(tmp_path, pr_split):
    rows = [{"pr_key": key, "regions": [REGION]} for key in pr_split]
    (tmp_path / "data.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    (tmp_path / "split.jsonl").write_text("\n".join(json.dumps({"pr_key": k, "split": s}) for k, s in pr_split.items()) + "\n")
    records = [{"pr_key": key, "file_path": "src/a.ts", "effective_index": 0,
                "classifier": {"source": "model", "status": "classified", "trace": trace()}} for key in pr_split]
    (tmp_path / "run.jsonl").write_text("\n".join(json.dumps(r) for r in records) + "\n")
    old_src = tmp_path / "old" / "classifier" / "rules"
    old_src.mkdir(parents=True)
    (old_src / "validators.py").write_text("def validate_logic_test(region, test_id, evidence):\n    return False\n")


def args(tmp_path, *extra):
    return [str(tmp_path / "run.jsonl"), "--old-src", str(tmp_path / "old"), "--dataset", str(tmp_path / "data.jsonl"),
            "--split-file", str(tmp_path / "split.jsonl"), "--labels", *extra]


def test_an_answer_only_the_new_validators_accept_is_newly_passing(tmp_path, capsys):
    write_run(tmp_path, {"o/r#1": "dev"})
    counts, changed = compare_validators.main(args(tmp_path))
    assert counts[("business-logic-conflict", False, True)] == 1
    assert [item[0] for item in changed] == [("o/r#1", "src/a.ts", 0)]
    assert "Newly passing: 1" in capsys.readouterr().out


def test_records_from_the_test_split_are_never_read(tmp_path):
    write_run(tmp_path, {"o/r#1": "dev", "o/r#2": "test"})
    _, changed = compare_validators.main(args(tmp_path))
    assert [item[0][0] for item in changed] == ["o/r#1"]


def test_asking_for_the_test_split_is_refused(tmp_path):
    write_run(tmp_path, {"o/r#1": "dev"})
    with pytest.raises(SystemExit):
        compare_validators.main(args(tmp_path) + ["--splits", "dev,test"])
