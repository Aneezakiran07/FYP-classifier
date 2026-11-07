# Stage 3 pattern that labels a region import-path when the same binding is imported from two different module paths
# It fires only when every changed line belongs to an import statement, and multi line imports are grouped first
# _binding_sources maps each imported name, alias or namespace to its sources, and a name with two sources on one side is skipped
# Its regular expressions and helper functions are also reused by the import restructure pattern

import difflib
import re

from .base import ClassifyInput, DeterministicResult, PatternPlugin

_IMPORT_LINE = re.compile(r"^\s*(import|from)\b")

# The first line of an ES import statement, used to group multi-line imports.
_STATEMENT_START = re.compile(r"^\s*import\b")

# A statement that has not closed after this many lines is dropped.
_MAX_STATEMENT_LINES = 40

# One import statement, matching the common TS/JS forms. Group 1 is the
# bindings clause (empty for side-effect imports), group 2 is the source
# string, group 3 is the quote character used so the same character closes.
# DOTALL lets the bindings clause span several lines, the caller passes one
# whole statement at a time.
_IMPORT_STATEMENT = re.compile(
    r"""^\s*import\s+
        (?:type\s+)?
        (?P<bindings>.*?)
        \s+from\s+
        (?P<quote>['"])(?P<source>[^'"]+)(?P=quote)
        \s*;?\s*$""",
    re.VERBOSE | re.DOTALL,
)

# A bare side-effect import with no bindings, such as import "./polyfill".
_SIDE_EFFECT_IMPORT = re.compile(
    r"""^\s*import\s+(?P<quote>['"])(?P<source>[^'"]+)(?P=quote)\s*;?\s*$""",
    re.VERBOSE,
)

# Matches "a as b" so the alias, not the original name, is the binding.
_ALIAS = re.compile(r"^\s*([A-Za-z_$][\w$]*)\s+as\s+([A-Za-z_$][\w$]*)\s*$")

# Matches "* as ns".
_NAMESPACE = re.compile(r"^\s*\*\s+as\s+([A-Za-z_$][\w$]*)\s*$")

# Matches a bare identifier.
_BARE = re.compile(r"^\s*([A-Za-z_$][\w$]*)\s*$")


def _group(text):
    # Groups the lines of a region into complete import statements. A
    # statement may span several lines. Returns the statements, each joined
    # with newlines, and the set of line indexes that belong to a complete
    # statement. A statement that never closes is dropped, so a fragment cut
    # in the middle of an import is not guessed at.
    statements = []
    marked = set()
    buffer = []
    start = 0
    for index, line in enumerate((text or "").splitlines()):
        if buffer and _STATEMENT_START.match(line):
            buffer = []
        if not buffer:
            if not _STATEMENT_START.match(line):
                continue
            start = index
        buffer.append(line)
        joined = "\n".join(buffer)
        if _SIDE_EFFECT_IMPORT.match(joined) or _IMPORT_STATEMENT.match(joined):
            statements.append(joined)
            marked.update(range(start, index + 1))
            buffer = []
        elif len(buffer) >= _MAX_STATEMENT_LINES:
            buffer = []
    return statements, marked


def _only_import_lines_differ(h):
    # True when every line that differs between the sides is an import line,
    # or sits inside a complete import statement, and at least one line
    # differs. A non-import line among the changed lines means the region is
    # not a pure import conflict.
    ours = h.ours_text.splitlines()
    theirs = h.theirs_text.splitlines()
    _, ours_marked = _group(h.ours_text)
    _, theirs_marked = _group(h.theirs_text)
    matcher = difflib.SequenceMatcher(None, ours, theirs, autojunk=False)
    found = False
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        found = True
        for i in range(i1, i2):
            if i not in ours_marked and not _IMPORT_LINE.match(ours[i]):
                return False
        for j in range(j1, j2):
            if j not in theirs_marked and not _IMPORT_LINE.match(theirs[j]):
                return False
    return found


def _bindings_from_clause(clause):
    # Yields binding names from a bindings clause. Handles a default
    # import, a braces list with optional aliases, and a namespace form.
    # The clause may span several lines.
    clause = clause.strip()
    if not clause:
        return

    if clause.startswith("{"):
        inner = clause.strip("{}")
        for part in inner.split(","):
            part = part.strip()
            if not part:
                continue
            alias = _ALIAS.match(part)
            if alias:
                yield alias.group(2)
                continue
            bare = _BARE.match(part)
            if bare:
                yield bare.group(1)
        return

    if clause.startswith("*"):
        namespace = _NAMESPACE.match(clause)
        if namespace:
            yield namespace.group(1)
        return

    # Default import, optionally followed by a braces list.
    head, _, tail = clause.partition(",")
    bare = _BARE.match(head)
    if bare:
        yield bare.group(1)
    if tail.strip():
        yield from _bindings_from_clause(tail.strip())


def _binding_sources(text):
    # Returns a mapping of binding name to the list of sources it is
    # imported from, in order of first appearance. A binding with more than
    # one source on a single side is a conflict the caller must not guess at.
    sources = {}
    statements, _ = _group(text)
    for statement in statements:
        if _SIDE_EFFECT_IMPORT.match(statement):
            continue
        match = _IMPORT_STATEMENT.match(statement)
        if not match:
            continue
        source = match.group("source")
        for binding in _bindings_from_clause(match.group("bindings")):
            seen = sources.setdefault(binding, [])
            if source not in seen:
                seen.append(source)
    return sources


def _binding_to_source(text):
    # Returns a mapping of binding name to its first source. Kept for other
    # patterns that reuse it. Callers that must notice a binding imported
    # from two sources use _binding_sources instead.
    return {name: found[0] for name, found in _binding_sources(text).items()}


class ImportPathOnly(PatternPlugin):
    # Taxonomy rule 5 third sentence: the same binding imported from two
    # different module paths. This is a dependency label, not a
    # structural label, so it lives in Group D.
    #
    # Rule 5 has three cases and this pattern only fires on the third:
    #   1. equal (binding, source) sets means structural/import-restructure
    #   2. different bindings added on each side means mechanical/disjoint-edits
    #   3. the same binding appears on both sides with different sources
    #
    # The check requires a shared binding name with a differing source, so
    # cases 1 and 2 fall through. Import statements may span several lines.
    # A binding imported from two different sources on the same side is
    # ambiguous, so the region is skipped and left to the model.
    #
    # The taxonomy says a relative path vs an alias counts as a different
    # source, so no path normalization is attempted. Two different strings
    # are two different sources, full stop.
    #
    # Priority 85 puts this rule ahead of DisjointEdits (90), so a same
    # binding with two paths is not absorbed as a disjoint edit.
    name = "ImportPathOnly"
    priority = 85
    requires = "both"
    precedence_rule = 5

    def detect(self, h: ClassifyInput) -> bool:
        if not _only_import_lines_differ(h):
            return False
        ours_sources = _binding_sources(h.ours_text)
        theirs_sources = _binding_sources(h.theirs_text)
        if any(len(found) > 1 for found in ours_sources.values()):
            return False
        if any(len(found) > 1 for found in theirs_sources.values()):
            return False
        shared = set(ours_sources) & set(theirs_sources)
        if not shared:
            return False
        return any(ours_sources[name][0] != theirs_sources[name][0] for name in shared)

    def resolve(self, h: ClassifyInput) -> DeterministicResult:
        return DeterministicResult(
            label="dependency/import-path",
            reason="same binding imported from different module paths",
        )