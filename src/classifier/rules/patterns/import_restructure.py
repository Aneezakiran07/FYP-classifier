# Stage 2 pattern that labels a region import-restructure when the same imports are only arranged differently
# The region must hold only JavaScript or TypeScript import or require statements, parsed into binding, form, original name and source
# These sets must match on both sides while statement order, merging or splitting may differ, and side effect imports must keep their order
# Duplicate bindings, import type statements, comments or any other line make it step aside for later stages

import re

from .base import ClassifyInput, DeterministicResult, PatternPlugin
from .import_path_only import (
    _ALIAS,
    _BARE,
    _IMPORT_STATEMENT,
    _NAMESPACE,
    _SIDE_EFFECT_IMPORT,
    _binding_to_source,
)

# Only JavaScript and TypeScript import syntax is understood here, so any
# other file type is left to later rules and the model.
JS_TS_EXTENSIONS = (".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx")

# A statement that has not closed after this many lines is not parsed.
MAX_STATEMENT_LINES = 40

_ES_START = re.compile(r"^\s*import\b")
_ES_TYPE_ONLY = re.compile(r"^\s*import\s+type\b")
_REQUIRE_START = re.compile(r"^\s*(?:(?:const|let|var)\b|require\s*\()")

# const x = require('y'), const {a, b: c} = require('y'), or a bare
# require('y') with no left-hand side.
_REQUIRE_STATEMENT = re.compile(
    r"""^(?:(?:const|let|var)\s+(?P<lhs>.+?)\s*=\s*)?
        require\s*\(\s*(?P<quote>['"])(?P<source>[^'"]+)(?P=quote)\s*\)\s*;?\s*$""",
    re.VERBOSE,
)

# "orig: alias" inside a require destructuring pattern.
_REQUIRE_ALIAS = re.compile(r"^\s*([A-Za-z_$][\w$]*)\s*:\s*([A-Za-z_$][\w$]*)\s*$")


def _forms(clause):
    # Returns an ordered list of (binding, form, original) for an ES import
    # bindings clause, or None when any part is not understood. The form
    # (default, named, namespace) and the original exported name are kept
    # because `import x from 'a'` and `import {x} from 'a'` bring in
    # different exports, and `{a as x}` differs from `{b as x}`. A pair set
    # that ignored them would over-fire.
    clause = clause.strip()
    result = []
    brace = re.search(r"\{(.*)\}", clause, re.S)
    head = clause[:brace.start()] if brace else clause
    head = head.strip().rstrip(",").strip()

    if head:
        namespace = _NAMESPACE.match(head)
        if namespace:
            result.append((namespace.group(1), "namespace", "*"))
        else:
            bare = _BARE.match(head)
            if not bare:
                return None
            result.append((bare.group(1), "default", "default"))

    if brace:
        if clause[brace.end():].strip():
            return None
        for part in brace.group(1).split(","):
            part = part.strip()
            if not part:
                continue
            alias = _ALIAS.match(part)
            if alias:
                result.append((alias.group(2), "named", alias.group(1)))
                continue
            bare = _BARE.match(part)
            if not bare:
                return None
            result.append((bare.group(1), "named", bare.group(1)))

    return result or None


def _parse_require(joined):
    match = _REQUIRE_STATEMENT.match(joined)
    if not match:
        return None
    source = match.group("source")
    lhs = match.group("lhs")
    if lhs is None:
        return {"kind": "side-effect", "source": source, "forms": []}

    lhs = lhs.strip()
    forms = []
    if lhs.startswith("{"):
        if not lhs.endswith("}"):
            return None
        for part in lhs[1:-1].split(","):
            if not part.strip():
                continue
            alias = _REQUIRE_ALIAS.match(part)
            if alias:
                forms.append((alias.group(2), "named", alias.group(1)))
                continue
            bare = _BARE.match(part)
            if not bare:
                return None
            forms.append((bare.group(1), "named", bare.group(1)))
    else:
        bare = _BARE.match(lhs)
        if not bare:
            return None
        forms.append((bare.group(1), "module", "*"))

    if not forms:
        return None
    return {"kind": "binding", "source": source, "forms": forms}


def _parse_import(joined):
    # `import type` statements are not handled, they never complete and
    # the whole region is skipped.
    if _ES_TYPE_ONLY.match(joined):
        return None

    side_effect = _SIDE_EFFECT_IMPORT.match(joined)
    if side_effect:
        return {"kind": "side-effect", "source": side_effect.group("source"), "forms": []}

    match = _IMPORT_STATEMENT.match(joined)
    if not match:
        return None

    clause = match.group("bindings")
    # Two statements on one line would otherwise be swallowed into one
    # bindings clause.
    if re.search(r"""['";]|\bimport\b""", clause):
        return None

    forms = _forms(clause)
    if not forms:
        return None

    # Cross-check against the shared helper. If it sees different binding
    # names than the local parse, something is off and the region is skipped.
    mapping = _binding_to_source(joined)
    names = [form[0] for form in forms]
    if set(mapping) != set(names) or len(names) != len(set(names)):
        return None
    source = match.group("source")
    if any(mapping[name] != source for name in names):
        return None

    return {"kind": "binding", "source": source, "forms": forms}


def _parse_statement(joined):
    if _ES_START.match(joined):
        return _parse_import(joined)
    return _parse_require(joined)


def _statements(text):
    # Splits a region into import or require statements, joining multi-line
    # statements. Returns None when anything else is present, including
    # comments, so the region is only ever a pure import region.
    statements = []
    buffer = []
    for line in (text or "").splitlines():
        if not buffer and not line.strip():
            continue
        if not buffer and not (_ES_START.match(line) or _REQUIRE_START.match(line)):
            return None
        buffer.append(line.strip())
        if len(buffer) > MAX_STATEMENT_LINES:
            return None
        parsed = _parse_statement(" ".join(buffer))
        if parsed is not None:
            statements.append(parsed)
            buffer = []
    if buffer:
        return None
    return statements or None


def _summarize(text):
    # Returns (pair set, ordered side-effect sources, arrangement) for one
    # side, or None when the side cannot be summarized safely.
    statements = _statements(text)
    if statements is None:
        return None

    pairs = []
    for statement in statements:
        for name, form, original in statement["forms"]:
            pairs.append((name, form, original, statement["source"]))

    # A repeated pair or a binding imported twice on one side is ambiguous.
    if len(pairs) != len(set(pairs)):
        return None
    names = [pair[0] for pair in pairs]
    if len(names) != len(set(names)):
        return None

    side_effects = [s["source"] for s in statements if s["kind"] == "side-effect"]
    arrangement = [(s["kind"], s["source"], tuple(s["forms"])) for s in statements]
    return set(pairs), side_effects, arrangement


class ImportRestructure(PatternPlugin):
    # Taxonomy rule 4 and rule 5 case 1: a region that consists only of
    # import or require statements, where the set of (binding, source)
    # pairs is equal on both sides and only the arrangement differs. The
    # arrangement can differ by statement order, merged or split
    # statements, or specifier order inside braces.
    #
    # Each pair also carries the import form and the original exported
    # name, so a default import never matches a named import and an alias
    # never matches a different original. Side-effect-only imports must
    # keep the same order among themselves, otherwise the region does not
    # qualify. Duplicate bindings, `import type` statements, inline type
    # specifiers, comments and any non-import line make the pattern
    # return False so the model handles the region.
    name = "ImportRestructure"
    priority = 45
    requires = "both"
    precedence_rule = 4

    def detect(self, h: ClassifyInput) -> bool:
        path = (h.file_path or "").lower()
        if not path.endswith(JS_TS_EXTENSIONS):
            return False
        if not (h.ours_text or "").strip() or not (h.theirs_text or "").strip():
            return False

        ours = _summarize(h.ours_text)
        theirs = _summarize(h.theirs_text)
        if ours is None or theirs is None:
            return False

        ours_pairs, ours_side_effects, ours_arrangement = ours
        theirs_pairs, theirs_side_effects, theirs_arrangement = theirs

        if ours_pairs != theirs_pairs:
            return False
        if ours_side_effects != theirs_side_effects:
            return False
        return ours_arrangement != theirs_arrangement

    def resolve(self, h: ClassifyInput) -> DeterministicResult:
        return DeterministicResult(
            label="structural/import-restructure",
            reason="same imported bindings and sources, arranged differently",
        )