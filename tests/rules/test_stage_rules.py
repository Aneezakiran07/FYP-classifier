import pytest

pytest.importorskip("tree_sitter")
pytest.importorskip("tree_sitter_typescript")

from classifier import pipeline, report
from classifier.llm import providers


@pytest.fixture(autouse=True)
def no_model(monkeypatch):
    # Any attempt to reach the model in these tests is a failure
    def boom(*args, **kwargs):
        raise AssertionError("the model must not be called by the rule stages")
    monkeypatch.setattr(providers, "call_model", boom)
    report.reset_stats()


def decide(path, ours, theirs, base=None, region=None):
    return pipeline.classify_region(path, ours, theirs, base, region, False)


@pytest.mark.parametrize("ours,theirs", [
    ("function f() { return\n x; }", "function f() { return x; }"),
    ("// @ts-ignore\nfoo();", "// @ts-expect-error\nfoo();"),
    ("// eslint-disable-next-line no-console\nfoo();", "// eslint-disable-next-line no-alert\nfoo();"),
])
def test_a_verdict_that_fails_a_guard_is_not_labeled(ours, theirs):
    result, layer, _ = decide("src/a.ts", ours, theirs)
    assert result is None and layer is None


def test_a_failed_guard_tells_the_model_the_content_changed(monkeypatch):
    seen = {}

    def fake_llm(file_path, ours_text, theirs_text, eq, region):
        seen["verdict"] = eq.equivalence
        return {"label": "unknown", "confidence": "low", "reason": "fake"}
    monkeypatch.setattr(pipeline, "classify_with_llm", fake_llm)
    pipeline.classify_region("src/a.ts", "// @ts-ignore\nfoo();", "// @ts-expect-error\nfoo();")
    assert seen["verdict"] == "content_changed"


def test_one_side_change_runs_before_value_only_change():
    result, _, detail = decide("src/a.ts", 'const retry = "a";', "const retry = 'b';", "const retry = 'a';")
    assert detail == "OneSideChange" and result["label"] == "mechanical/one-side-change"


def test_value_only_change_still_fires_when_both_sides_changed():
    _, _, detail = decide("src/a.ts", "const retry = 1;", "const retry = 2;", "const retry = 0;")
    assert detail == "ValueOnlyChange"


def test_the_gate_runs_before_the_boundary_stage():
    ours = "const a = 1;\nconst z = 2;"
    theirs = "const x = 1;\nconst b = 2;"
    base = "const x = 1;\nconst z = 2;"
    result, layer, _ = decide("src/a.ts", ours, theirs, base)
    assert layer == "ast" and result["label"] == "structural/rename"


def test_a_file_with_no_parser_is_not_called_whitespace_by_the_gate():
    # A YAML indentation change must reach the config check
    _, _, detail = decide("ci/a.yml", "a:\n  b: 1", "a:\n    b: 1")
    assert detail == "ConfigSchema"


@pytest.mark.parametrize("path", [
    "src/a.js", "src/a.jsx", "src/a.mjs", "src/a.css", "src/a.py", "src/a.go", "img/a.png", "a.mts",
])
def test_files_outside_the_scope_are_unknown(path):
    result, _, detail = decide(path, "a", "b")
    assert detail == "OutOfScope"
    assert result["label"] == "unknown" and result["unknown_reason"] == "out-of-scope"


@pytest.mark.parametrize("path,expected", [
    ("package-lock.json", "Lockfile"),
    ("bun.lock", "Lockfile"),
    ("bun.lockb", "Lockfile"),
    ("sub/Cargo.lock", "Lockfile"),
    ("package.json", "PackageManifest"),
    ("tsconfig.json", "ConfigSchema"),
    (".eslintrc.cjs", "ConfigSchema"),
])
def test_dependency_and_config_files_stay_in_scope(path, expected):
    _, _, detail = decide(path, "a: 1", "a: 2")
    assert detail == expected


@pytest.mark.parametrize("path", ["src/a.ts", "src/a.tsx", "next.config.mjs", "tailwind.config.js"])
def test_typescript_and_javascript_config_stay_in_scope(path):
    result, layer, _ = decide(path, "a = 1", "a = 2")
    assert result is None and layer is None


@pytest.mark.parametrize("path", ["docs/a.md", "docs/a.mdx", "docs/a.rst", "docs/a.txt"])
def test_prose_stays_in_scope(path):
    _, _, detail = decide(path, "one", "two")
    assert detail == "CommentsOnly"


@pytest.mark.parametrize("ours,theirs", [
    ("const n = items.length; return n * price;", "const count = items.length; return count * price;"),
    ("function total(a: number) { return a; }", "function total(b: number) { return b; }"),
    ("const f = (a: number) => a + 1;", "const f = (b: number) => b + 1;"),
    ("items.map(item => item.id);", "items.map(row => row.id);"),
])
def test_a_local_rename_is_labeled_rename(ours, theirs):
    result, layer, _ = decide("src/a.ts", ours, theirs)
    assert layer == "ast" and result["label"] == "structural/rename"


@pytest.mark.parametrize("ours,theirs", [
    ("const x = isAdmin(user);", "const x = isOwner(user);"),
    ("return user.name;", "return user.title;"),
    ("send(first, message);", "send(first, note);"),
    ("const q = 1;\nuse(q, old);", "const r = 1;\nuse(r, fresh);"),
])
def test_swapping_a_name_that_is_not_declared_here_is_not_a_rename(ours, theirs):
    result, layer, _ = decide("src/a.ts", ours, theirs)
    assert result is None and layer is None


@pytest.mark.parametrize("conflict_type", ["deleted_by_us", "deleted_by_them"])
def test_whole_file_deletion_is_business_logic(conflict_type):
    region = {"no_markers": True, "conflict_type": conflict_type}
    result, _, detail = decide("src/a.ts", "", "", None, region)
    assert detail == "NoMarkers" and result["label"] == "logic/business-logic-conflict"


@pytest.mark.parametrize("conflict_type", [
    "both_added", "added_by_us", "added_by_them", "both_modified_no_markers", "unknown",
])
def test_other_no_marker_regions_are_unknown_with_a_reason(conflict_type):
    region = {"no_markers": True, "conflict_type": conflict_type}
    result, _, detail = decide("src/a.ts", "", "", None, region)
    assert detail == "NoMarkers" and result["label"] == "unknown"
    assert conflict_type in result["reason"] and result["unknown_reason"] == "no-markers"


def test_scope_runs_before_the_no_marker_check():
    region = {"no_markers": True, "conflict_type": "deleted_by_us"}
    _, _, detail = decide("src/a.css", "", "", None, region)
    assert detail == "OutOfScope"
