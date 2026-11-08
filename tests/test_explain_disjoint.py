# Tests for the explain_disjoint script on a tiny made up funnel folder, with no model and no real data
# One checks that the A3 repro prints the deleted name and the check that stops the label
# Another checks that a region that is not in the input is refused
# The last one checks that an empty base is reported as a region DisjointEdits does not run on

import importlib.util
import json
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
spec = importlib.util.spec_from_file_location("explain_disjoint", SCRIPTS / "explain_disjoint.py")
explain_disjoint = importlib.util.module_from_spec(spec)
spec.loader.exec_module(explain_disjoint)

REGIONS = [
    {"conflict_index": 0, "file_path": "src/a.ts", "base_text": "const limit = 10;\nrun();\nshow(limit);",
     "ours_text": "run();\nshow(limit);", "theirs_text": "const limit = 10;\nrun();\nshow(limit, true);"},
    {"conflict_index": 1, "file_path": "src/a.ts", "base_text": "", "ours_text": "a", "theirs_text": "b"},
]


@pytest.fixture
def funnel(tmp_path):
    (tmp_path / "input.jsonl").write_text(json.dumps({"pr_key": "o/r#1", "regions": REGIONS}) + "\n")
    return tmp_path


def test_the_deleted_name_and_the_stopping_check_are_printed(funnel, capsys):
    explain_disjoint.main([str(funnel), "o/r#1", "src/a.ts", "0"])
    output = capsys.readouterr().out
    assert "deleted names: ['limit']" in output
    assert "3 theirs uses what ours deleted: ['limit']" in output
    assert "DisjointEdits fires: False" in output


def test_a_region_that_is_not_in_the_input_is_refused(funnel):
    with pytest.raises(SystemExit):
        explain_disjoint.main([str(funnel), "o/r#1", "src/a.ts", "9"])


def test_an_empty_base_is_reported(funnel, capsys):
    explain_disjoint.main([str(funnel), "o/r#1", "src/a.ts", "1"])
    assert "DisjointEdits does not run" in capsys.readouterr().out
