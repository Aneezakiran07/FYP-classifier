# Tests for the evaluate script on made up records and labels, with no model and no real data
# They check that capped and llm-error are counted apart and never scored, and that rules and model are scored apart
# Others check that few shot examples and test split labels are left out, and the model filter and precision and recall
# The last ones check that a label outside the taxonomy and a label given twice are refused

import importlib.util
import json
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
spec = importlib.util.spec_from_file_location("evaluate", SCRIPTS / "evaluate.py")
evaluate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluate)


def record(pr, index, label, source="rule", stage=3, status="classified", model=None, reason=None):
    provenance = {"component_version": "0.1.0"}
    if model:
        provenance["model_name"] = model
    return {"pr_key": pr, "file_path": "src/a.ts", "conflict_index": index,
            "classifier": {"label": label, "status": status, "source": source, "stage": stage,
                           "unknown_reason": reason, "provenance": provenance}}


def label(pr, index, true_label, notes="n"):
    return {"pr_key": pr, "file_path": "src/a.ts", "conflict_index": index, "true_label": true_label, "notes": notes}


def write(tmp_path, name, rows):
    path = tmp_path / name
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return str(path)


def run(tmp_path, records, labels, *extra, split=None, few_shot=None):
    args = [write(tmp_path, "records.jsonl", records), "--labels", write(tmp_path, "labels.jsonl", labels),
            "--split-file", write(tmp_path, "split.jsonl", split or [{"pr_key": "none", "split": "dev"}]),
            "--few-shot", str(tmp_path / "missing.json")]
    if few_shot is not None:
        (tmp_path / "few_shot.json").write_text(json.dumps(few_shot), encoding="utf-8")
        args[-1] = str(tmp_path / "few_shot.json")
    return evaluate.main(args + list(extra))


def part(result, name):
    return next(row for row in result["accuracy"] if row["part"] == name)


def test_capped_and_llm_error_are_counted_but_never_scored(tmp_path):
    records = [record("o/r#1", 0, "lockfile"),
               record("o/r#1", 1, None, source="model", stage=4, status="capped"),
               record("o/r#1", 2, None, source="model", stage=4, status="llm-error")]
    labels = [label("o/r#1", 0, "lockfile"), label("o/r#1", 1, "assignment-override"),
              label("o/r#1", 2, "unknown")]
    result = run(tmp_path, records, labels)
    assert (result["capped"], result["llm_error"], result["classified"]) == (1, 1, 1)
    assert part(result, "all") == {"part": "all", "correct": 1, "scored": 1}
    assert result["true_unknown"] == 0


def test_rules_and_model_are_scored_apart(tmp_path):
    records = [record("o/r#1", 0, "lockfile"), record("o/r#1", 1, "package"),
               record("o/r#1", 2, "assignment-override", source="model", stage=4, model="m1"),
               record("o/r#1", 3, "unknown", source="model", stage=4, model="m1", reason="no-test-met")]
    labels = [label("o/r#1", 0, "lockfile"), label("o/r#1", 1, "config-schema"),
              label("o/r#1", 2, "assignment-override"), label("o/r#1", 3, "unknown")]
    result = run(tmp_path, records, labels)
    assert part(result, "rules")["correct"] == 1 and part(result, "rules")["scored"] == 2
    assert part(result, "model")["correct"] == 2 and part(result, "model")["scored"] == 2
    assert result["predicted_unknown_reasons"] == {"no-test-met": 1}
    assert len(result["misses"]) == 1


def test_precision_and_recall_per_label(tmp_path):
    records = [record("o/r#1", 0, "lockfile"), record("o/r#1", 1, "lockfile"), record("o/r#1", 2, "package")]
    labels = [label("o/r#1", 0, "lockfile"), label("o/r#1", 1, "package"), label("o/r#1", 2, "package")]
    rows = {row["label"]: row for row in run(tmp_path, records, labels)["per_label"]}
    assert rows["lockfile"]["precision"] == 0.5 and rows["lockfile"]["recall"] == 1.0
    assert rows["package"]["precision"] == 1.0 and rows["package"]["recall"] == 0.5


def test_few_shot_examples_are_left_out(tmp_path):
    records = [record("o/r#1", 0, "assignment-override", source="model", stage=4, model="m1")]
    labels = [label("o/r#1", 0, "assignment-override", notes="both assign x")]
    few_shot = [{"file_path": "src/a.ts", "true_label": "assignment-override", "notes": "both assign x"}]
    result = run(tmp_path, records, labels, few_shot=few_shot)
    assert result["left_out"] == {"used as a few shot example": 1}
    assert result["considered"] == 0


def test_test_split_labels_need_the_final_flag(tmp_path):
    records = [record("o/r#9", 0, "lockfile")]
    labels = [label("o/r#9", 0, "lockfile")]
    split = [{"pr_key": "o/r#9", "split": "test"}]
    assert run(tmp_path, records, labels, split=split)["considered"] == 0
    assert run(tmp_path, records, labels, "--final", split=split)["considered"] == 1


def test_model_filter_keeps_rules_and_drops_other_models(tmp_path):
    records = [record("o/r#1", 0, "lockfile"),
               record("o/r#1", 1, "assignment-override", source="model", stage=4, model="m1"),
               record("o/r#1", 2, "assignment-override", source="model", stage=4, model="m2")]
    labels = [label("o/r#1", 0, "lockfile"), label("o/r#1", 1, "assignment-override"),
              label("o/r#1", 2, "assignment-override")]
    result = run(tmp_path, records, labels, "--model", "m1")
    assert result["left_out"] == {"decided by another model": 1}
    assert result["models"] == {"m1": 1}


def test_a_label_outside_the_taxonomy_is_refused(tmp_path):
    with pytest.raises(SystemExit):
        run(tmp_path, [record("o/r#1", 0, "lockfile")], [label("o/r#1", 0, "not-a-label")])


def test_a_region_labeled_twice_is_refused(tmp_path):
    labels = [label("o/r#1", 0, "lockfile"), label("o/r#1", 0, "package")]
    with pytest.raises(SystemExit):
        run(tmp_path, [record("o/r#1", 0, "lockfile")], labels)
