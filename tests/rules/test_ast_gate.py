# Tests for the AST gate, skipped when the tree sitter grammars are missing, where any model call is a failure
# They check the gate labels identical, whitespace, comment, formatting and rename verdicts without the model
# They check the rename map is reported, a content change is left for the model and an unsupported file type is not analyzed
# They check that identical text is identical and that the patterns still run before the gate

import pytest

pytest.importorskip("tree_sitter")
pytest.importorskip("tree_sitter_typescript")
pytest.importorskip("tree_sitter_python")

from classifier import pipeline, report
from classifier.llm import providers
from classifier.rules.ast_diff import compute_ast_equivalence


@pytest.fixture(autouse=True)
def no_model(monkeypatch):
    # Any attempt to reach the model in these tests is a failure
    def boom(*args, **kwargs):
        raise AssertionError("the model must not be called when the ast gate decides")
    monkeypatch.setattr(providers, "call_model", boom)
    report.reset_stats()


CASES = [
    # A fragment that does not parse and holds a regex or markup passes the pattern and reaches the gate
    ("whitespace_only", "mechanical/whitespace-only", "src/fragment.ts",
     "if (x) {\n const r = /a/;", "if (x) {\n  const r = /a/;"),
    ("whitespace_only", "mechanical/whitespace-only", "src/fragment.tsx",
     "<a>\n<b c='d'/>", "<a>\n  <b c='d'/>"),
    ("comments_only", "structural/documentation", "src/calc.ts",
     "const r = /'/; // it's old", "const r = /'/; // it's new"),
    ("identifier_rename_only", "structural/rename", "src/calc.ts",
     "const n = items.length; return n * price;", "const count = items.length; return count * price;"),
    ("formatting_only", "structural/formatting", "src/quote.ts",
     "const a = 'x';", 'const a = "x"'),
]


@pytest.mark.parametrize("equivalence,label,path,ours,theirs", CASES)
def test_gate_decides_without_the_model(equivalence, label, path, ours, theirs):
    assert compute_ast_equivalence(path, ours, theirs).equivalence == equivalence
    result, layer, detail = pipeline.classify_region(path, ours, theirs)
    assert layer == "ast"
    assert detail == equivalence
    assert result["label"] == label
    assert result["confidence"] == "high"


@pytest.mark.parametrize("path,ours,theirs", [
    ("src/math.ts", "const total = a+b;", "const total  =  a + b;"),
    ("src/send.ts", "send(user, message, retries);", "send(\n  user,\n  message,\n  retries\n);"),
])
def test_the_whitespace_pattern_decides_what_it_can_parse_before_the_gate(path, ours, theirs):
    # Both belong to Stage 2 and the gate agrees, so the label is the same either way
    assert compute_ast_equivalence(path, ours, theirs).equivalence == "whitespace_only"
    result, layer, detail = pipeline.classify_region(path, ours, theirs)
    assert (layer, detail) == ("pattern", "WhitespaceOnly")
    assert result["label"] == "mechanical/whitespace-only"


def test_rename_map_is_reported():
    eq = compute_ast_equivalence("a.js", "const n = 1; f(n);", "const count = 1; f(count);")
    assert eq.renames == {"n": "count"}


def test_content_change_is_left_for_the_model(monkeypatch):
    eq = compute_ast_equivalence("gate.ts", "if (age > 18) { allow(); }", "if (age >= 18) { allow(); }")
    assert eq.equivalence == "content_changed"
    assert eq.changed_nodes == ["operator_changed:>\u2192>="]
    # With the model blocked from running, the cap path returns None instead
    result, layer, detail = pipeline.classify_region(
        "gate.ts", "if (age > 18) { allow(); }", "if (age >= 18) { allow(); }", allow_llm=False
    )
    assert result is None and layer is None


def test_unsupported_file_type_is_not_analyzed():
    eq = compute_ast_equivalence("notes.md", "one thing", "another thing")
    assert eq.equivalence == "not_analyzed"
    assert eq.parse_error == "no_parser_available"


def test_identical_text_is_identical():
    assert compute_ast_equivalence("a.py", "", "").equivalence == "identical"


def test_patterns_still_run_before_the_gate():
    result, layer, detail = pipeline.classify_region("package-lock.json", "a", "b")
    assert layer == "pattern" and detail == "Lockfile"


def test_a_template_string_with_a_substitution_is_not_a_plain_string():
    # A1 from the review, a plain string keeps the placeholder as text while a template string inserts the value
    ours, theirs = 'const s = "Hi ${name}";', "const s = `Hi ${name}`;"
    assert compute_ast_equivalence("src/a.ts", ours, theirs).equivalence == "content_changed"
    result, layer, detail = pipeline.classify_region("src/a.ts", ours, theirs, allow_llm=False)
    assert result is None and layer is None


def test_a_template_string_with_no_substitution_is_still_formatting():
    # Without a placeholder the template string holds the same text as the plain string
    assert compute_ast_equivalence("src/a.ts", 'const s = "Hi";', "const s = `Hi`;").equivalence == "formatting_only"


def test_a_semicolon_before_a_parenthesis_line_is_kept():
    # A2 from the review, without the semicolon theirs calls y with the next line as its argument
    ours, theirs = "x = y;\n(z || w).run();", "x = y\n(z || w).run();"
    assert compute_ast_equivalence("src/a.ts", ours, theirs).equivalence == "content_changed"
    result, layer, detail = pipeline.classify_region("src/a.ts", ours, theirs, allow_llm=False)
    assert result is None and layer is None


@pytest.mark.parametrize("next_line", ["[a, b].forEach(run);", "`x`.trim();"])
def test_a_semicolon_before_a_bracket_or_template_line_is_kept(next_line):
    # A next line that starts with a bracket or a backtick also continues the line above
    ours, theirs = "x = y;\n" + next_line, "x = y\n" + next_line
    assert compute_ast_equivalence("src/a.ts", ours, theirs).equivalence == "content_changed"


def test_a_semicolon_before_an_ordinary_line_is_still_formatting():
    # A next line that starts with a name cannot join the line above
    ours, theirs = "x = y;\nz.run();", "x = y\nz.run();"
    assert compute_ast_equivalence("src/a.ts", ours, theirs).equivalence == "formatting_only"
