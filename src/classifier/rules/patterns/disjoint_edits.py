# Stage 3 pattern that labels a region disjoint-edits when both sides changed different parts that do not interact
# It needs a base and checks that the changed base lines do not overlap, the declared names differ, and neither side uses a name the other defines or deleted
# Helper functions find changed lines, strip strings, hide JSX attributes and collect identifiers and declared names
# The fourth check about a joint use in context lines cannot run because the data has no surrounding lines

import difflib
import re

from .base import ClassifyInput, DeterministicResult, PatternPlugin

_STRING = re.compile(
    r'''("(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*'|`(?:\\.|[^`\\])*`)''', re.S
)

_IDENTIFIER = re.compile(r"[A-Za-z_$][\w$]*")

# File types where JSX markup may appear.
_JSX_EXTENSIONS = (".jsx", ".tsx", ".js", ".mjs")

# A JSX tag, from "<Name" to its closing ">" or the end of the line. It must
# not follow an identifier, ")" or "]", so a comparison such as a<b and a
# generic such as Array<T> are not read as tags.
_JSX_TAG = re.compile(
    r"""(?<![\w$)\]])<[A-Za-z][\w.:-]*(?:"[^"]*"|'[^']*'|\{[^{}]*\}|[^<>"'{}])*>?"""
)

# A line that starts with one or more JSX attributes such as className="x"
# or onClick={...}, which is how a multi-line tag shows its attributes.
_JSX_ATTRIBUTE_LINE = re.compile(
    r"""^\s*(?:[A-Za-z_$][\w$:-]*=(?:"[^"]*"|'[^']*'|\{)\s*)+"""
)

_DECLARATION_PATTERNS = [
    re.compile(r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)"),
    re.compile(r"\bfunction\s+([A-Za-z_$][\w$]*)"),
    re.compile(r"\bclass\s+([A-Za-z_$][\w$]*)"),
    re.compile(r"\binterface\s+([A-Za-z_$][\w$]*)"),
    re.compile(r"\btype\s+([A-Za-z_$][\w$]*)"),
    re.compile(r"\benum\s+([A-Za-z_$][\w$]*)"),
    re.compile(r"(?<![.\w$])([A-Za-z_$][\w$]*)\s*=(?!=)"),
    re.compile(r"(?<![.\w$])([A-Za-z_$][\w$]*)\??\s*:\s*[^:=]"),
]

# A parameter list of a function or an arrow function, the same shape the rename guard reads
_PARAMETER_LIST = re.compile(r"\bfunction\b[^(]*\(([^()]*)\)|\(([^()]*)\)\s*(?::[^=>{]+)?=>")

# Real local declarations only, a type counts only as a type alias as in the rename guard of D9
_LOCAL_DECLARATIONS = [
    re.compile(r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)"),
    re.compile(r"\bfunction\s+([A-Za-z_$][\w$]*)"),
    re.compile(r"\bclass\s+([A-Za-z_$][\w$]*)"),
    re.compile(r"\binterface\s+([A-Za-z_$][\w$]*)"),
    re.compile(r"\btype\s+([A-Za-z_$][\w$]*)\s*[<=]"),
    re.compile(r"\benum\s+([A-Za-z_$][\w$]*)"),
]

# An import or export list names bindings of another file or of an export, never a new local declaration
_MODULE_LIST = re.compile(r"\b(?:import|export)\s+(?:type\s+)?\{[^{}]*\}", re.S)

_KEYWORDS = frozenset({
    "const", "let", "var", "function", "class", "interface", "type", "enum",
    "return", "if", "else", "for", "while", "do", "switch", "case", "default",
    "break", "continue", "new", "delete", "typeof", "instanceof", "in", "of",
    "true", "false", "null", "undefined", "this", "super",
    "import", "export", "from", "as", "async", "await", "yield",
    "try", "catch", "finally", "throw",
    "extends", "implements", "public", "private", "protected", "static",
    "readonly", "abstract", "declare",
})


def _split_lines(text):
    return (text or "").splitlines()


def _changed_line_indices(base_lines, side_lines):
    # Base line indexes that a side modified or deleted. A pure insertion
    # takes no base line, so it records nothing, and two sides inserting at
    # the same boundary do not look like an overlap.
    matcher = difflib.SequenceMatcher(None, base_lines, side_lines, autojunk=False)
    touched = set()
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag in ("equal", "insert"):
            continue
        touched.update(range(i1, i2))
    return touched


def _changed_line_text(base_lines, side_lines):
    matcher = difflib.SequenceMatcher(None, base_lines, side_lines, autojunk=False)
    pieces = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        pieces.extend(side_lines[j1:j2])
    return pieces


def _parameter_names(lines):
    names = set()
    for match in _PARAMETER_LIST.finditer(_strip_strings("\n".join(lines))):
        for part in (match.group(1) or match.group(2) or "").split(","):
            found = re.match(r"\s*(?:\.\.\.)?([A-Za-z_$][\w$]*)", part)
            if found and found.group(1) not in _KEYWORDS:
                names.add(found.group(1))
    return names


def _locally_declared(lines, jsx):
    # Names the side still declares itself, by a declaration keyword or as a parameter
    # Object keys, assignments and names in import or export lists do not count
    masked = _MODULE_LIST.sub(" ", _strip_strings("\n".join(lines))).splitlines()
    names = set()
    for line in masked:
        stripped = _mask_jsx(line) if jsx else line
        for pattern in _LOCAL_DECLARATIONS:
            for match in pattern.finditer(stripped):
                if match.group(1) not in _KEYWORDS:
                    names.add(match.group(1))
    return names | _parameter_names(masked)


def _deleted_names(base_lines, side_lines, jsx):
    # Names declared on base lines the side deleted or replaced that the side no longer declares anywhere
    removed = _declared_names(_removed_base_lines(base_lines, side_lines), jsx)
    return removed - _locally_declared(side_lines, jsx)


def _removed_base_lines(base_lines, side_lines):
    # Base lines that a side deleted or replaced, an insertion removes none
    matcher = difflib.SequenceMatcher(None, base_lines, side_lines, autojunk=False)
    pieces = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag in ("replace", "delete"):
            pieces.extend(base_lines[i1:i2])
    return pieces


def _strip_strings(text):
    return _STRING.sub(" ", text)


def _mask_jsx(line):
    # Removes JSX attributes from a line so that href= and className= are
    # not read as assignments. Attribute-only lines of a multi-line tag are
    # dropped, and any tag on the line is reduced to a stub.
    line = _JSX_ATTRIBUTE_LINE.sub("", line, count=1)
    return _JSX_TAG.sub("<tag>", line)


def _identifiers(lines):
    joined = _strip_strings("\n".join(lines))
    return set(_IDENTIFIER.findall(joined)) - _KEYWORDS


def _declared_names(lines, jsx=False):
    names = set()
    for line in lines:
        stripped = _strip_strings(_mask_jsx(line) if jsx else line)
        for pattern in _DECLARATION_PATTERNS:
            for match in pattern.finditer(stripped):
                name = match.group(1)
                if name and name not in _KEYWORDS:
                    names.add(name)
    return names


class DisjointEdits(PatternPlugin):
    # Taxonomy rule 8: each side changed different parts of the region and
    # the edits do not interact. Needs base. The taxonomy lists four
    # conditions, all of which must hold:
    #   1. changed-line sets do not overlap
    #   2. names each side declares or assigns are disjoint
    #   3. neither side's changed lines reference a name the other defines or deleted
    #   4. no unchanged line in the context window uses names from both
    #
    # Condition 4 cannot be checked here, because the input region does
    # not carry the surrounding context lines. The visible context the
    # taxonomy refers to lives outside the conflict markers and is not
    # part of ours_text or theirs_text. This pattern therefore checks
    # conditions 1 to 3 only.
    #
    # The consequences of skipping condition 4: this pattern may fire on
    # a region that should be logic/confluent-interference, when the only
    # joint use of the two names is in a line outside the conflict
    # markers. That is an over-fire risk in the direction of a safe
    # mechanical label, which is a lower severity mistake than the
    # inverse. The fix is a v3.1 change, adding a context window to the
    # input so that condition 4 can be evaluated.
    #
    # A side that equals base has no edit to merge, so the pattern steps
    # aside. Pure insertions at the same boundary qualify, as the taxonomy
    # says, because an insertion takes no base line. JSX attributes are not
    # read as declarations in JS and TSX files, and optional members written
    # name?: count as declarations.
    #
    # The class is also gated on has_base at the registry so it needs a real base
    name = "DisjointEdits"
    priority = 90
    requires = "diff3"
    precedence_rule = 8

    def detect(self, h: ClassifyInput) -> bool:
        if not h.base_text:
            return False

        base_lines = _split_lines(h.base_text)
        ours_lines = _split_lines(h.ours_text)
        theirs_lines = _split_lines(h.theirs_text)

        if ours_lines == base_lines or theirs_lines == base_lines:
            return False

        ours_touched = _changed_line_indices(base_lines, ours_lines)
        theirs_touched = _changed_line_indices(base_lines, theirs_lines)

        if ours_touched & theirs_touched:
            return False

        ours_changed = _changed_line_text(base_lines, ours_lines)
        theirs_changed = _changed_line_text(base_lines, theirs_lines)

        jsx = (h.file_path or "").lower().endswith(_JSX_EXTENSIONS)
        ours_declared = _declared_names(ours_changed, jsx)
        theirs_declared = _declared_names(theirs_changed, jsx)

        if ours_declared & theirs_declared:
            return False

        ours_referenced = _identifiers(ours_changed)
        theirs_referenced = _identifiers(theirs_changed)

        if ours_referenced & theirs_declared:
            return False
        if theirs_referenced & ours_declared:
            return False

        # A name declared on a base line that one side deleted or replaced
        # must not be used by the changed lines of the other side
        ours_removed = _deleted_names(base_lines, ours_lines, jsx)
        theirs_removed = _deleted_names(base_lines, theirs_lines, jsx)

        if ours_referenced & theirs_removed:
            return False
        if theirs_referenced & ours_removed:
            return False

        return True

    def resolve(self, h: ClassifyInput) -> DeterministicResult:
        return DeterministicResult(
            label="mechanical/disjoint-edits",
            reason="non-interacting edits to different parts of the region",
        )