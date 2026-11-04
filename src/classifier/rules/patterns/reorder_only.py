import re

from .base import ClassifyInput, DeterministicResult, PatternPlugin

# Taxonomy rule 4: reorder-only applies only to order-insensitive
# containers. The list is deliberately short.
#   object members (no spread, no duplicate keys), interface and type
#   members, class methods, function and type declarations, specifier
#   lists inside {}, JSON keys.
# It never applies to statement sequences, array elements, call
# arguments, or whole import statements.

# A line that looks like a member of an order-insensitive container.
# The pattern is deliberately loose because fragments have no full
# syntax, but the reject list below catches the common non-member shapes.
_MEMBER_LINE = re.compile(
    r"^\s*"
    r"(?:readonly\s+|public\s+|private\s+|protected\s+|static\s+|declare\s+)?"
    r"(?:"
    r"(?:[A-Za-z_$][\w$]*|\"[^\"]+\"|'[^']+')"      # bare key
    r"\s*"
    r"(?::|\?:|\()"                                 # then : or ?: or (
    r"|"
    r"[A-Za-z_$][\w$]*\s*,\s*$"                     # bare member, comma
    r")"
)

# A line that looks like a statement or an import, which makes the whole
# region non-reorderable under rule 4. Declarations (function, class,
# async methods) are no longer rejected by word, they are judged by the
# line and block checks. Only the anonymous forms stay rejected here.
_REJECT_LINE = re.compile(
    r"^\s*(?:"
    r"import\b|export\b|from\b|require\s*\("
    r"|const\b|let\b|var\b"
    r"|function\s*\*?\s*\(|async\s*\("
    r"|if\b|else\b|for\b|while\b|switch\b|case\b|try\b|catch\b|finally\b"
    r"|return\b|throw\b|break\b|continue\b"
    r"|do\b|new\b|await\b|yield\b|delete\b"
    r")"
)

# A line that opens or closes an interface, class, type literal or object.
# These lines carry no member of their own and their position relative to
# the members does not affect behavior, so a reorder of the members inside
# a wrapper is still safe. They are skipped by the member check rather
# than rejected.
_WRAPPER_LINE = re.compile(
    r"^\s*(?:"
    r"interface\s+[A-Za-z_$][\w$]*(?:\s+extends\s+[^{]+)?\s*\{"
    r"|class\s+[A-Za-z_$][\w$]*(?:\s+extends\s+[^{]+)?\s*\{"
    r"|type\s+[A-Za-z_$][\w$]*\s*=\s*\{"
    r"|\{"
    r"|\}"
    r")\s*;?\s*$"
)

# Lines that contain an assignment. A bare `key = value` inside a
# container is a statement (or a class field, which the taxonomy does not
# list as order-insensitive). The three character lookarounds keep `=>`,
# `==`, and `===` from matching as `=`.
_ASSIGNMENT = re.compile(r"(?<![=!<>])=(?!=|>)")

# A line that ends with a closing parenthesis, optionally followed by a
# semicolon, is a call statement such as init(); unless it has the shape
# of a method signature.
_CALL_END = re.compile(r"\)\s*;?\s*$")

# One typed parameter, such as `id: string`, `id?: string` or `...rest: T`.
_TYPED_PARAM = re.compile(r"^\s*(?:\.\.\.)?[A-Za-z_$][\w$]*\??\s*:\s*\S")

# Files whose content is a single JSON object or similar keyed structure.
_KEYED_EXTENSIONS = (".json",)

# Files where interface, type, class, and object members are common.
_MEMBER_EXTENSIONS = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".java", ".cs")

# Files where the block path for multi-line declarations is attempted.
_BLOCK_EXTENSIONS = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs")

# Strings and comments are removed before braces and parentheses are counted.
_STRING_OR_COMMENT = re.compile(
    r'"(?:\\.|[^"\\\n])*"|\'(?:\\.|[^\'\\\n])*\'|`(?:\\.|[^`\\])*`|//[^\n]*|/\*.*?\*/',
    re.S,
)

# Names that can head a statement and never head a method.
_CONTROL_WORDS = frozenset({
    "if", "for", "while", "switch", "catch", "with", "return", "throw", "try",
    "do", "else", "finally", "new", "await", "yield", "typeof", "delete",
    "void", "super", "import", "export",
})

_FUNCTION_HEADER = re.compile(
    r"^(?:async\s+)?function\s*\*?\s*([A-Za-z_$][\w$]*)\s*(?:<[^>()]*>)?\s*\("
)
_TYPE_HEADER = re.compile(
    r"^(?:interface\s+([A-Za-z_$][\w$]*)"
    r"|type\s+([A-Za-z_$][\w$]*)\s*(?:<[^>()]*>)?\s*=)"
)
_METHOD_HEADER = re.compile(
    r"^(?:(?:public|private|protected|static|readonly|override|abstract|async|get|set)\s+)*"
    r"\*?\s*([A-Za-z_$][\w$]*)\s*(?:<[^>()]*>)?\s*\("
)
# What may follow the closing parenthesis of a header: an optional return
# type, then the opening brace of the body.
_HEADER_REST = re.compile(r"^\s*(?::\s*[^{};=]+)?\{")


def _nonempty_lines(text):
    return [line for line in (text or "").splitlines() if line.strip()]


def _normalize_line(line):
    # Indentation and one trailing comma do not matter when comparing line
    # multisets, so moving the last member of a list still matches.
    stripped = line.strip()
    if stripped.endswith(","):
        stripped = stripped[:-1].rstrip()
    return stripped


def _extract_key(line):
    # Returns the identifier or quoted key of a member line, or None.
    match = re.match(
        r"""^\s*(?:readonly\s+|public\s+|private\s+|protected\s+|static\s+|declare\s+)?"""
        r"""(?:([A-Za-z_$][\w$]*)|"([^"]+)"|'([^']+)')""",
        line,
    )
    if not match:
        return None
    return match.group(1) or match.group(2) or match.group(3)


def _ends_like_call(line):
    return bool(_CALL_END.search(line.rstrip().rstrip(",")))


def _has_signature_shape(line):
    # True when every parameter between the first "(" and the last ")" is
    # typed, as in `save(id: string)`. An empty list or an untyped list is
    # a call, not a signature.
    start = line.find("(")
    end = line.rfind(")")
    if start == -1 or end < start:
        return False
    inner = line[start + 1:end]
    if not inner.strip():
        return False
    return all(_TYPED_PARAM.match(part) for part in inner.split(","))


def _all_lines_are_members(lines):
    # Every non-empty line must either be a wrapper (skipped) or look
    # like a member. A statement, a call or an assignment disqualifies
    # the whole region.
    for line in lines:
        if _WRAPPER_LINE.match(line):
            continue
        if _REJECT_LINE.match(line):
            return False
        if _ends_like_call(line) and not _has_signature_shape(line):
            return False
        if _ASSIGNMENT.search(line):
            return False
        if not _MEMBER_LINE.match(line):
            return False
    return True


def _has_duplicate_keys(lines):
    # Rule 4 says object members with no duplicate keys. A duplicate key
    # makes the container order-sensitive again.
    seen = set()
    for line in lines:
        key = _extract_key(line)
        if key is None:
            continue
        if key in seen:
            return True
        seen.add(key)
    return False


def _line_reorder(ours, theirs):
    if not _all_lines_are_members(ours) or not _all_lines_are_members(theirs):
        return False
    return not (_has_duplicate_keys(ours) or _has_duplicate_keys(theirs))


def _split_items(lines):
    # Splits lines into top-level items by brace depth. An item runs from
    # its first line until the depth returns to zero. Returns None on
    # unbalanced braces.
    items = []
    current = []
    depth = 0
    for line in lines:
        clean = _STRING_OR_COMMENT.sub("", line)
        current.append(line)
        depth += clean.count("{") - clean.count("}")
        if depth < 0:
            return None
        if depth == 0:
            items.append(current)
            current = []
    if current:
        return None
    return items


def _identity(item):
    # Returns (kind, name) when the item is a function, type, interface or
    # method declaration, otherwise None.
    first = item[0].strip()
    clean_first = _STRING_OR_COMMENT.sub("", first)

    match = _FUNCTION_HEADER.match(first)
    if match:
        kind, name = "function", match.group(1)
    else:
        match = _TYPE_HEADER.match(first)
        if match:
            return ("type", match.group(1) or match.group(2))
        match = _METHOD_HEADER.match(first)
        if not match or match.group(1) in _CONTROL_WORDS:
            return None
        kind, name = "method", match.group(1)

    # A function or method header must close its parameter list on its first
    # line and open its body right after an optional return type. A call
    # that takes a callback, such as foo(() => {, fails the balance check.
    if clean_first.count("(") != clean_first.count(")"):
        return None
    if "{" not in clean_first:
        return None
    tail = clean_first[clean_first.rfind(")") + 1:]
    if not _HEADER_REST.match(tail):
        return None
    return (kind, name)


def _unwrapped(lines):
    # Returns (wrapper, declarations) or None. A single class, interface,
    # type or object wrapper around the whole region is peeled off once.
    items = _split_items(lines)
    if not items:
        return None
    wrapper = None
    if (
        len(items) == 1
        and len(items[0]) >= 3
        and _WRAPPER_LINE.match(items[0][0])
        and items[0][-1].strip().rstrip(";,") == "}"
    ):
        wrapper = items[0][0].strip()
        items = _split_items(items[0][1:-1])
        if items is None:
            return None

    declarations = []
    for item in items:
        identity = _identity(item)
        if identity is None:
            return None
        key = "\n".join(line.strip() for line in item).rstrip(",;")
        declarations.append((identity, key))
    return wrapper, declarations


def _block_reorder(ours, theirs):
    left = _unwrapped(ours)
    right = _unwrapped(theirs)
    if left is None or right is None:
        return False
    if left[0] != right[0]:
        return False
    ours_declarations, theirs_declarations = left[1], right[1]
    if len(ours_declarations) < 2 or len(theirs_declarations) < 2:
        return False

    ours_ids = [d[0] for d in ours_declarations]
    theirs_ids = [d[0] for d in theirs_declarations]
    if len(set(ours_ids)) != len(ours_ids) or len(set(theirs_ids)) != len(theirs_ids):
        return False

    ours_keys = [d[1] for d in ours_declarations]
    theirs_keys = [d[1] for d in theirs_declarations]
    return ours_keys != theirs_keys and sorted(ours_keys) == sorted(theirs_keys)


class ReorderOnly(PatternPlugin):
    # Taxonomy rule 4: same items in a different order inside an
    # order-insensitive container. Detection requires all of:
    #   1. the line multiset is identical between the two sides, compared
    #      after stripping indentation and one trailing comma,
    #   2. either every non-empty line is a container member or a wrapper
    #      (and no line is a bare call), or the region is made of whole
    #      function, type, interface or method declarations with unique
    #      names,
    #   3. no key repeats within either side.
    # Any file type is allowed as long as the shape checks pass, but the
    # reject list is what actually enforces "never statement sequences,
    # array elements, call arguments, or whole import statements".
    name = "ReorderOnly"
    priority = 50
    requires = "both"
    precedence_rule = 4

    def detect(self, h: ClassifyInput) -> bool:
        ours = _nonempty_lines(h.ours_text)
        theirs = _nonempty_lines(h.theirs_text)

        if len(ours) < 2 or len(theirs) < 2:
            return False

        ours_norm = [_normalize_line(line) for line in ours]
        theirs_norm = [_normalize_line(line) for line in theirs]
        if ours_norm == theirs_norm:
            return False
        if sorted(ours_norm) != sorted(theirs_norm):
            return False

        path = (h.file_path or "").lower()
        if not (path.endswith(_KEYED_EXTENSIONS) or path.endswith(_MEMBER_EXTENSIONS)):
            return False

        if _line_reorder(ours, theirs):
            return True
        if path.endswith(_BLOCK_EXTENSIONS):
            return _block_reorder(ours, theirs)
        return False

    def resolve(self, h: ClassifyInput) -> DeterministicResult:
        return DeterministicResult(
            label="mechanical/reorder-only",
            reason="same members in a different order inside an order-insensitive container",
        )