# Tests for the compare_funnels script on two tiny made up funnel folders, with no model and no real data
# One checks that changed regions are grouped by old and new label and that a missing record counts as Reached Stage 4
# Others check that each batch 1 fix explains its own change and that a change no fix explains is flagged
# The last ones check that hand labels are matched, files are never written and different inputs are refused

import importlib.util
import json
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
spec = importlib.util.spec_from_file_location("compare_funnels", SCRIPTS / "compare_funnels.py")
compare_funnels = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compare_funnels)

REGIONS = [
    {"conflict_index": 0, "file_path": "src/a.ts", "base_text": "x", "ours_text": "s = \"${a}\"", "theirs_text": "s = `${a}`"},
    {"conflict_index": 1, "file_path": "src/a.ts", "base_text": "x", "ours_text": "a", "theirs_text": "b"},
    {"conflict_index": 2, "file_path": "src/a.ts", "base_text": "", "ours_text": "", "theirs_text": "c"},
    {"conflict_index": 3, "file_path": "src/sdk.gen.ts", "base_text": "x", "ours_text": "a", "theirs_text": "b"},
    {"conflict_index": 4, "file_path": "src/b.ts", "base_text": "x", "ours_text": "a", "theirs_text": "b"},
    {"conflict_index": 5, "file_path": "src/c.ts", "base_text": "x", "ours_text": "a", "theirs_text": "b"},
]


def block(label, rule, unknown_reason=None):
    return {"status": "classified", "label": label, "confirming_test": rule, "unknown_reason": unknown_reason}


def write_run(folder, blocks):
    # One input file and one rules file, a None block means the region reached Stage 4
    folder.mkdir()
    (folder / "input.jsonl").write_text(json.dumps({"pr_key": "o/r#1", "regions": REGIONS}) + "\n")
    lines = []
    for region, value in zip(REGIONS, blocks):
        if value is not None:
            lines.append(json.dumps({"pr_key": "o/r#1", "file_path": region["file_path"],
                                     "effective_index": region["conflict_index"], "classifier": value}))
    (folder / "rules.jsonl").write_text("\n".join(lines) + "\n")


@pytest.fixture
def runs(tmp_path):
    write_run(tmp_path / "base", [
        block("formatting", "formatting_only"),
        block("disjoint-edits", "DisjointEdits"),
        None,
        None,
        block("same-change", "SameChange"),
        block("rename", "identifier_rename_only"),
    ])
    write_run(tmp_path / "new", [
        None,
        None,
        block("one-side-change", "OneSideChange"),
        block("unknown", "OutOfScope", "out-of-scope"),
        block("disjoint-edits", "DisjointEdits"),
        block("rename", "identifier_rename_only"),
    ])
    return tmp_path


def test_changes_are_grouped_and_each_fix_explains_its_own(runs, capsys):
    groups = compare_funnels.main([str(runs / "base"), str(runs / "new"), "--labels"])
    marker = {(old, new): [reason for _, reason in members] for (population, old, new), members in groups.items()}
    assert marker == {
        ("formatting", "Reached Stage 4"): ["A1"],
        ("disjoint-edits", "Reached Stage 4"): ["A3"],
        ("Reached Stage 4", "one-side-change"): ["B1"],
        ("Reached Stage 4", "unknown (out-of-scope)"): ["C2"],
        ("same-change", "disjoint-edits"): ["UNEXPLAINED"],
    }
    output = capsys.readouterr().out
    assert "not explained by any batch 1 fix" in output
    assert "Regions no batch 1 fix explains: 1" in output


def test_hand_labels_are_matched_by_conflict_index(runs, capsys):
    labels = runs / "labels.jsonl"
    labels.write_text(json.dumps({"number": 7, "pr_key": "o/r#1", "file_path": "src/sdk.gen.ts",
                                  "conflict_index": 3, "true_label": "unknown"}) + "\n")
    compare_funnels.main([str(runs / "base"), str(runs / "new"), "--labels", str(labels)])
    assert "labels.jsonl region 7, true label unknown" in capsys.readouterr().out


def test_nothing_is_written(runs):
    before = {path: path.stat().st_mtime_ns for path in runs.rglob("*")}
    compare_funnels.main([str(runs / "base"), str(runs / "new"), "--labels"])
    assert {path: path.stat().st_mtime_ns for path in runs.rglob("*")} == before


def test_runs_over_different_inputs_are_refused(runs):
    (runs / "new" / "input.jsonl").write_text(json.dumps({"pr_key": "o/r#2", "regions": REGIONS[:1]}) + "\n")
    with pytest.raises(SystemExit):
        compare_funnels.main([str(runs / "base"), str(runs / "new"), "--labels"])
