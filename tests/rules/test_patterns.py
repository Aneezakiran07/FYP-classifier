import os
import sys

# Lets pytest find the patterns package no matter where it is launched from
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from classifier.rules.patterns import (
    PATTERNS,
    ClassifyInput,
    classify_deterministic,
    classify_deterministic_named,
)
from classifier.rules.patterns.no_markers import NoMarkers
from classifier.rules.patterns.same_change import SameChange
from classifier.rules.patterns.whitespace_only import WhitespaceOnly
from classifier.rules.patterns.comments_only import CommentsOnly
from classifier.rules.patterns.lockfile import Lockfile
from classifier.rules.patterns.package_manifest import PackageManifest
from classifier.rules.patterns.config_schema import ConfigSchema
from classifier.rules.patterns.one_side_change import OneSideChange
from classifier.rules.patterns.disjoint_edits import DisjointEdits
from classifier.rules.patterns.import_path_only import ImportPathOnly
from classifier.rules.patterns.reorder_only import ReorderOnly


def make(ours, theirs, path="src/app.ts", base=None, region=None):
    # Small helper so each test states only what it cares about
    return ClassifyInput(path, ours, theirs, base_text=base, region=region)


# NoMarkers

def test_no_markers_positive():
    h = make("", "", region={"no_markers": True, "conflict_type": "deleted_by_us"})
    assert NoMarkers().detect(h)
    result = NoMarkers().resolve(h)
    assert result.label == "logic/business-logic-conflict"


def test_no_markers_negative():
    assert not NoMarkers().detect(make("a", "b", region={"conflict_index": 0}))
    assert not NoMarkers().detect(make("a", "b", region=None))
    assert not NoMarkers().detect(make("a", "b", region={"no_markers": False}))


# SameChange

def test_same_change_positive():
    h = make("const a = 1;", "const a = 1;")
    assert SameChange().detect(h)
    assert SameChange().resolve(h).label == "mechanical/same-change"


def test_same_change_negative():
    assert not SameChange().detect(make("const a = 1;", "const a = 2;"))
    assert not SameChange().detect(make("", ""))
    assert not SameChange().detect(make("   ", "\n"))
    # Outer whitespace differences are NOT same-change under taxonomy rule 1
    assert not SameChange().detect(make("const a = 1;\n", "  const a = 1;"))


# WhitespaceOnly

def test_whitespace_only_positive():
    h = make("a  =  b;", "a = b;")
    assert WhitespaceOnly().detect(h)
    assert WhitespaceOnly().resolve(h).label == "mechanical/whitespace-only"


def test_whitespace_only_negative():
    # Removing a space entirely joins tokens so it is not a collapse
    assert not WhitespaceOnly().detect(make("a b", "ab"))
    # Byte identical text is not a whitespace difference
    assert not WhitespaceOnly().detect(make("a = b;", "a = b;"))


def test_whitespace_only_excludes_indentation_significant_files():
    # Taxonomy rule 3: Python, YAML, Makefile are excluded
    assert not WhitespaceOnly().detect(make("x = 1\ny = 2", "x = 1\n    y = 2", path="src/calc.py"))
    assert not WhitespaceOnly().detect(make("a: 1", "a:  1", path="ci/config.yml"))
    assert not WhitespaceOnly().detect(make("a: 1", "a:  1", path="Makefile"))


def test_whitespace_only_excludes_string_literal_contents():
    # Taxonomy rule 3: whitespace inside a string counts as a difference
    assert not WhitespaceOnly().detect(make('const u = "a  b";', 'const u = "a b";'))


# CommentsOnly

def test_comments_only_positive():
    h = make("x = 1; // old note", "x = 1; // new note")
    assert CommentsOnly().detect(h)
    assert CommentsOnly().resolve(h).label == "structural/documentation"
    block = make("/* one */ run();", "/* two */ run();")
    assert CommentsOnly().detect(block)


def test_comments_only_negative():
    # A double slash inside a string is code, not a comment
    assert not CommentsOnly().detect(
        make('const u = "http://a.com";', 'const u = "http://b.com";')
    )
    # Real code differs next to an identical comment
    assert not CommentsOnly().detect(make("x = 1; // note", "x = 2; // note"))
    # Floor division in python must not look like a comment
    assert not CommentsOnly().detect(make("a // b", "a // c", path="src/calc.py"))


def test_comments_only_skips_directives():
    # Taxonomy rule 14: directive comments count as code
    assert not CommentsOnly().detect(
        make("// @ts-ignore\nfoo();", "foo();")
    )
    assert not CommentsOnly().detect(
        make("/* eslint-disable */\nfoo();", "foo();")
    )


def test_comments_only_fires_on_prose_files():
    # Taxonomy rule 14: .md/.txt/.rst are documentation by definition
    assert CommentsOnly().detect(make("one thing", "another thing", path="docs/readme.md"))


# Lockfile

def test_lockfile_positive():
    h = make('"express": "^4.17.1",', '"express": "^4.18.2",', path="package-lock.json")
    assert Lockfile().detect(h)
    result = Lockfile().resolve(h)
    assert result.label == "dependency/lockfile"


def test_lockfile_negative():
    assert not Lockfile().detect(make("a", "b", path="src/app.ts"))
    # No size cap in v3, taxonomy does not mention one
    big = "\n".join(f"line {i}" for i in range(21))
    assert Lockfile().detect(make(big, "x", path="yarn.lock"))
    # Only exact basenames count
    assert Lockfile().detect(make("a", "b", path="Cargo.lock"))
    assert not Lockfile().detect(make("a", "b", path="my-pnpm-lock.yaml"))
    assert not Lockfile().detect(make("a", "b", path="nested/package-lock.json.bak"))


# PackageManifest

def test_package_manifest_positive():
    h = make('"react": "^18.0.0"', '"react": "^18.2.0"', path="package.json")
    assert PackageManifest().detect(h)
    assert PackageManifest().resolve(h).label == "dependency/package"
    # Monorepo workspace package.json fires too
    assert PackageManifest().detect(make("a", "b", path="packages/foo/package.json"))


def test_package_manifest_negative():
    assert not PackageManifest().detect(make("a", "b", path="src/app.ts"))
    assert not PackageManifest().detect(make("a", "b", path="package-lock.json"))


# ConfigSchema

def test_config_schema_positive():
    cases = [
        "tsconfig.json", "tsconfig.build.json", "jsconfig.json",
        ".eslintrc", ".eslintrc.json", ".eslintrc.cjs",
        ".prettierrc", ".prettierrc.yaml",
        ".babelrc", ".env", ".env.local", ".env.production",
        "docker-compose.yml", "netlify.toml",
    ]
    for path in cases:
        assert ConfigSchema().detect(make("a: 1", "a: 2", path=path)), path


def test_config_schema_negative():
    # Executable config is treated as code, not config-schema
    assert not ConfigSchema().detect(make("a", "b", path="vite.config.ts"))
    assert not ConfigSchema().detect(make("a", "b", path="eslint.config.js"))
    assert not ConfigSchema().detect(make("a", "b", path="next.config.mjs"))
    # tsconfig without a .json extension does not match
    assert not ConfigSchema().detect(make("a", "b", path="tsconfig"))


# OneSideChange

def test_one_side_change_positive():
    h = make("a = 1", "a = 2", base="a = 1")
    assert OneSideChange().detect(h)
    result = OneSideChange().resolve(h)
    assert result.label == "mechanical/one-side-change"
    assert result.logic_subtype is None
    assert result.confidence == "high"


def test_one_side_change_fires_on_reformatted_side():
    # Taxonomy rule 2: a side that was only reformatted counts as untouched
    h = make("a = 1\n", "a = 2", base="a = 1")
    assert OneSideChange().detect(h)


def test_one_side_change_negative():
    # Both sides changed
    assert not OneSideChange().detect(make("a = 2", "a = 3", base="a = 1"))
    # Neither side changed
    assert not OneSideChange().detect(make("a = 1", "a = 1", base="a = 1"))
    # No base available
    assert not OneSideChange().detect(make("a = 1", "a = 2", base=None))


# DisjointEdits

def test_disjoint_edits_positive():
    # Two sides editing different parts of the same base region
    base = "a = 1\nb = 2\nc = 3"
    ours = "a = 10\nb = 2\nc = 3"
    theirs = "a = 1\nb = 2\nc = 30"
    assert DisjointEdits().detect(make(ours, theirs, base=base))
    result = DisjointEdits().resolve(make(ours, theirs, base=base))
    assert result.label == "mechanical/disjoint-edits"


def test_disjoint_edits_negative():
    # No base, pattern cannot fire
    assert not DisjointEdits().detect(make("a = 1", "a = 2", base=None))
    # Overlapping changes
    base = "a = 1\nb = 2"
    assert not DisjointEdits().detect(make("a = 10\nb = 20", "a = 99\nb = 20", base=base))
    # One side references a name the other side declares
    base = "x = 0"
    ours = "y = 1\nx = y"
    theirs = "y = 2\nx = 0"
    assert not DisjointEdits().detect(make(ours, theirs, base=base))


# ImportPathOnly

def test_import_path_only_positive():
    h = make(
        "import { load } from './utils/loader';",
        "import { load } from './core/loader';",
    )
    assert ImportPathOnly().detect(h)
    assert ImportPathOnly().resolve(h).label == "dependency/import-path"


def test_import_path_only_negative():
    # One code line differs along with the import
    ours = "import a from './a';\nconst x = 1;"
    theirs = "import a from './b';\nconst x = 2;"
    assert not ImportPathOnly().detect(make(ours, theirs))
    assert not ImportPathOnly().detect(make("import a from './a';", "import a from './a';"))


def test_import_path_only_skips_restructure_and_new_bindings():
    # Same binding set, extra binding added: this is not import-path, not
    # the same binding with a different source
    ours = "import { a } from './x';"
    theirs = "import { a, b } from './x';"
    assert not ImportPathOnly().detect(make(ours, theirs))
    # Different bindings on each side, not the same binding
    ours = "import { a } from './x';"
    theirs = "import { b } from './x';"
    assert not ImportPathOnly().detect(make(ours, theirs))


# ReorderOnly

def test_reorder_only_positive():
    # Interface members reordered
    ours = "interface A {\n  a: number;\n  b: string;\n}"
    theirs = "interface A {\n  b: string;\n  a: number;\n}"
    assert ReorderOnly().detect(make(ours, theirs, path="src/types.ts"))
    assert ReorderOnly().resolve(make(ours, theirs, path="src/types.ts")).label == "mechanical/reorder-only"


def test_reorder_only_negative():
    # Statement sequences are never reorderable
    assert not ReorderOnly().detect(make("a\nb\nc", "c\nb\na", path="src/app.ts"))
    # Different line counts
    assert not ReorderOnly().detect(make("a\nb", "a\nb\nc", path="src/app.ts"))
    # Identical sides
    assert not ReorderOnly().detect(make("a\nb", "a\nb", path="src/app.ts"))
    # Duplicate keys disqualify
    ours = "interface A {\n  a: number;\n  a: string;\n  b: boolean;\n}"
    theirs = "interface A {\n  b: boolean;\n  a: number;\n  a: string;\n}"
    assert not ReorderOnly().detect(make(ours, theirs, path="src/types.ts"))


# Registry

def test_registry_holds_every_pattern_in_stage_order():
    assert [p.name for p in PATTERNS] == [
        "OutOfScope",
        "NoMarkers", "SameChange", "OneSideChange",
        "WhitespaceOnly", "CommentsOnly", "ImportRestructure", "ReorderOnly",
        "Lockfile", "PackageManifest", "ConfigSchema", "ValueOnlyChange", "ImportPathOnly", "DisjointEdits",
    ]
    priorities = [p.priority for p in PATTERNS]
    assert priorities == sorted(priorities)
    assert len(set(priorities)) == len(PATTERNS)


def test_registry_overlap_is_settled_by_priority():
    # Byte identical goes to SameChange
    name, _ = classify_deterministic_named(make("a = 1", "a = 1"))
    assert name == "SameChange"
    # Outer whitespace differences reach WhitespaceOnly instead
    name, _ = classify_deterministic_named(make("a = 1", "a = 1\n"))
    assert name == "WhitespaceOnly"
    # No markers wins over everything
    name, _ = classify_deterministic_named(make("a", "a", region={"no_markers": True}))
    assert name == "NoMarkers"


def test_registry_lockfile_beats_config_schema_for_package_json():
    # package.json is a package manifest, not a config schema, even though
    # it ends in .json
    name, _ = classify_deterministic_named(
        make('{"a": 1}', '{"a": 2}', path="package.json")
    )
    assert name == "PackageManifest"
    name, _ = classify_deterministic_named(
        make('{"a": 1}', '{"a": 2}', path="package-lock.json")
    )
    assert name == "Lockfile"


def test_registry_diff3_only_runs_with_base():
    assert classify_deterministic_named(make("a = 1", "a = 2", base=None)) is None
    name, _ = classify_deterministic_named(make("a = 1", "a = 2", base="a = 1"))
    assert name == "OneSideChange"
    # An empty base counts as no base
    assert classify_deterministic(make("a = 1", "a = 2", base="")) is None


def test_registry_returns_none_when_nothing_matches():
    assert classify_deterministic(make("total = a + b", "total = a - b")) is None


def test_registry_skips_a_broken_pattern():
    class Broken(SameChange):
        name = "Broken"
        priority = 1

        def detect(self, h):
            raise RuntimeError("boom")

    PATTERNS.append(Broken())
    try:
        name, _ = classify_deterministic_named(make("a = 1", "a = 1"))
        assert name == "SameChange"
    finally:
        PATTERNS.pop()