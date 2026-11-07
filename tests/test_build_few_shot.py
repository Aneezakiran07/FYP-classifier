# Tests for the build_few_shot script, loaded from the scripts folder by its file path
# They check that only complete answers whose first met test is the label become examples
# They check that an example whose quoted evidence the prompt would cut off is skipped
# They check that several label files are read in order and the example shows the AST verdict after the guards

import importlib.util
import json
from pathlib import Path

import pytest

pytest.importorskip("tree_sitter")
pytest.importorskip("tree_sitter_typescript")

from classifier.llm.prompts import LOGIC_TESTS
from classifier.rules.ast_diff import compute_ast_equivalence

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build_few_shot.py"
spec = importlib.util.spec_from_file_location("build_few_shot", SCRIPT)
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


def answers(met_test, evidence="`x = 1`"):
    # Seven answers in the fixed order where only the named test is met
    return [{"test_id": test, "met": test == met_test,
             "evidence": evidence if test == met_test else "the condition does not hold"}
            for test in LOGIC_TESTS]


def write_jsonl(path, rows):
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_complete_answers_with_the_label_met_first_are_accepted():
    assert build.answers_problem(answers("assignment-override"), "assignment-override") is None


def test_an_empty_answer_is_refused():
    broken = answers("assignment-override")
    broken[0]["met"] = None
    assert build.answers_problem(broken, "assignment-override")


def test_answers_out_of_order_are_refused():
    swapped = answers("assignment-override")
    swapped[0], swapped[1] = swapped[1], swapped[0]
    assert build.answers_problem(swapped, "assignment-override")


def test_a_first_met_test_that_is_not_the_label_is_refused():
    both = answers("assignment-override")
    both[0]["met"] = True
    assert "first met test" in build.answers_problem(both, "assignment-override")


def test_a_quote_the_prompt_cuts_off_is_found():
    region = {"base_text": "", "ours_text": "a = 0\n" * 120 + "late = 1", "theirs_text": "late = 2"}
    assert build.hidden_quotes(answers("assignment-override", "`late = 1`"), region) == ["late = 1"]
    assert build.hidden_quotes(answers("assignment-override", "`late = 2`"), region) == []


def test_only_complete_labels_from_every_file_become_examples(tmp_path):
    regions = [
        {"file_path": "src/a.ts", "conflict_index": 0, "base_text": "x = 0", "ours_text": "x = 1", "theirs_text": "x = 2"},
        {"file_path": "src/a.ts", "conflict_index": 1, "base_text": "y = 0", "ours_text": "y = 1", "theirs_text": "y = 2"},
    ]
    write_jsonl(tmp_path / "input.jsonl", [{"pr_key": "o/r#1", "regions": regions}])
    empty = [{"test_id": test, "met": None, "evidence": ""} for test in LOGIC_TESTS]

    def label(index, test_answers):
        return {"pr_key": "o/r#1", "file_path": "src/a.ts", "conflict_index": index,
                "true_label": "assignment-override", "notes": "one target gets two values",
                "test_answers": test_answers}

    write_jsonl(tmp_path / "first.jsonl", [label(0, empty)])
    write_jsonl(tmp_path / "second.jsonl", [label(1, answers("assignment-override", "`y = 2`"))])
    out = tmp_path / "few_shot.json"
    build.main([str(tmp_path / "input.jsonl"), str(tmp_path / "first.jsonl"),
                str(tmp_path / "second.jsonl"), "--out", str(out)])

    examples = json.loads(out.read_text(encoding="utf-8"))
    assert [example["ours"] for example in examples] == ["y = 1"]


def test_the_example_shows_the_verdict_after_the_guards():
    # The parser calls this a rename, but the rename guard rejects it because neither name is declared here
    region = {"base_text": "", "ours_text": "  BILLING_ERROR_CODES,", "theirs_text": "  SSO_ERROR_CODES,"}
    assert compute_ast_equivalence("src/codes.ts", region["ours_text"], region["theirs_text"]).equivalence \
        == "identifier_rename_only"
    example = build.build_example({"file_path": "src/codes.ts"}, "assignment-override", region)
    assert example["ast_equivalence"]["equivalence"] == "content_changed"
