import difflib
import importlib
import json
import os
import sys
import textwrap
from collections import Counter
from dataclasses import dataclass, field
from typing import Literal, Optional

from tree_sitter import Language, Parser

# Maps a file extension to the language key used by this module
EXTENSION_TO_LANGUAGE = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".java": "java",
    ".go": "go",
}

# Each language names the pip module and the function that returns its grammar
GRAMMAR_LOADERS = {
    "python": ("tree_sitter_python", "language"),
    "javascript": ("tree_sitter_javascript", "language"),
    "typescript": ("tree_sitter_typescript", "language_typescript"),
    "tsx": ("tree_sitter_typescript", "language_tsx"),
    "java": ("tree_sitter_java", "language"),
    "go": ("tree_sitter_go", "language"),
}

# Conflict regions are usually code fragments, so if the raw text does not
# parse cleanly the snippet is placed inside one of these wrappers instead
WRAPPERS = {
    "python": [("none", "", ""), ("block", "if True:\n", "\n")],
    "javascript": [
        ("none", "", ""),
        ("function", "function __w__() {\n", "\n}\n"),
        ("class", "class __W__ {\n", "\n}\n"),
    ],
    "typescript": [
        ("none", "", ""),
        ("function", "function __w__() {\n", "\n}\n"),
        ("class", "class __W__ {\n", "\n}\n"),
    ],
    "tsx": [
        ("none", "", ""),
        ("function", "function __w__() {\n", "\n}\n"),
        ("class", "class __W__ {\n", "\n}\n"),
    ],
    "java": [
        ("none", "", ""),
        ("class", "class __W__ {\n", "\n}\n"),
        ("method", "class __W__ {\nvoid __w__() {\n", "\n}\n}\n"),
    ],
    "go": [
        ("none", "", ""),
        ("package", "package w\n", "\n"),
        ("function", "package w\nfunc __w__() {\n", "\n}\n"),
    ],
}

# Node types that carry no useful meaning when counting node types
IGNORED_NODE_TYPES = {"ERROR", "program", "module", "source_file"}

# Ancestor node types that show a token belongs to an import statement
IMPORT_PARENTS = {
    "import_statement",
    "import_from_statement",
    "future_import_statement",
    "import_declaration",
    "import_spec",
    "import_clause",
}

PUNCTUATION = {"(", ")", "{", "}", "[", "]", ",", ";", ":"}
CLOSERS = {")", "]", "}"}

MAX_CHANGES_IN_PAYLOAD = 20
MAX_TEXT_CHARS = 120

_PARSER_CACHE = {}


@dataclass
class Token:
    kind: str
    text: str
    parents: tuple = ()

    def key(self):
        return (self.kind, self.text)


@dataclass
class ParsedSide:
    tokens: list = field(default_factory=list)
    node_counts: Counter = field(default_factory=Counter)
    comments: list = field(default_factory=list)
    error_count: int = 0

    def status(self):
        if not self.tokens:
            return "empty"
        return "clean" if self.error_count == 0 else "partial"


def detect_language(file_path):
    # The language is chosen only from the file extension
    extension = os.path.splitext(file_path or "")[1].lower()
    return EXTENSION_TO_LANGUAGE.get(extension)


def get_parser(language):
    # Grammars are loaded lazily and cached, a missing package returns None
    if language in _PARSER_CACHE:
        return _PARSER_CACHE[language]
    module_name, function_name = GRAMMAR_LOADERS[language]
    try:
        module = importlib.import_module(module_name)
        grammar = Language(getattr(module, function_name)())
        parser = Parser(grammar)
    except Exception:
        parser = None
    _PARSER_CACHE[language] = parser
    return parser


def is_comment_type(node_type):
    return "comment" in node_type


def is_string_type(node_type):
    # Strings are treated as one token so quote style is not split apart
    return (
        node_type == "string"
        or node_type == "template_string"
        or node_type.endswith("string_literal")
    )


def token_kind(node):
    node_type = node.type
    if is_string_type(node_type):
        return "string"
    if node_type.endswith("identifier"):
        return "identifier"
    if any(word in node_type for word in ("number", "integer", "float", "int_literal", "decimal")):
        return "number"
    if node.is_named:
        return "literal"
    return "keyword" if node_type.replace("_", "").isalpha() else "punct"


def apply_wrapper(language, wrapper_name, snippet):
    # Returns the wrapped source plus the byte range that holds the snippet
    body = textwrap.dedent(snippet).strip("\n")
    prefix, suffix = "", ""
    for name, wrapper_prefix, wrapper_suffix in WRAPPERS[language]:
        if name == wrapper_name:
            prefix, suffix = wrapper_prefix, wrapper_suffix
    if language == "python" and wrapper_name == "block":
        body = textwrap.indent(body, "    ")
    source = (prefix + body + suffix).encode("utf-8")
    start = len(prefix.encode("utf-8"))
    end = start + len(body.encode("utf-8"))
    return source, start, end


def parse_side(parser, language, wrapper_name, snippet):
    source, start, end = apply_wrapper(language, wrapper_name, snippet)
    tree = parser.parse(source)
    side = ParsedSide()

    # An explicit stack keeps the walk safe on deeply nested code
    stack = [(tree.root_node, ())]
    while stack:
        node, parents = stack.pop()
        inside = node.start_byte >= start and node.end_byte <= end
        if node.type == "ERROR" or node.is_missing:
            side.error_count += 1

        text = source[node.start_byte:node.end_byte].decode("utf-8", errors="replace")

        if is_comment_type(node.type):
            if inside:
                side.comments.append(text.strip())
            continue

        if node.is_named and inside and node.type not in IGNORED_NODE_TYPES:
            side.node_counts[node.type] += 1

        if is_string_type(node.type) or node.child_count == 0:
            if inside and text.strip():
                side.tokens.append(Token(token_kind(node), text.strip(), parents))
            continue

        child_parents = (parents + (node.type,))[-6:]
        for child in reversed(node.children):
            stack.append((child, child_parents))

    return side


def choose_and_parse(language, ours_text, theirs_text):
    # The wrapper with the fewest parse errors across both sides wins
    parser = get_parser(language)
    if parser is None:
        return None
    best = None
    for wrapper_name, _, _ in WRAPPERS[language]:
        ours = parse_side(parser, language, wrapper_name, ours_text)
        theirs = parse_side(parser, language, wrapper_name, theirs_text)
        errors = ours.error_count + theirs.error_count
        if best is None or errors < best[0]:
            best = (errors, wrapper_name, ours, theirs)
        if errors == 0:
            break
    return best[1], best[2], best[3]


def normalized_keys(tokens):
    # Drops semicolons, trailing commas, and quote characters so that pure
    # formatting choices do not count as differences
    keys = []
    for index, token in enumerate(tokens):
        if token.text == ";":
            continue
        if token.text == "," and index + 1 < len(tokens) and tokens[index + 1].text in CLOSERS:
            continue
        if token.kind == "string" and len(token.text) >= 2 and token.text[0] in "'\"`":
            keys.append(("string", token.text[1:-1]))
        else:
            keys.append(token.key())
    return keys


def shorten(text):
    text = " ".join(text.split())
    return text if len(text) <= MAX_TEXT_CHARS else text[:MAX_TEXT_CHARS] + "..."


def join_tokens(tokens):
    return shorten(" ".join(token.text for token in tokens))


def in_import(tokens, before):
    for token in tokens[:1]:
        if any(parent in IMPORT_PARENTS for parent in token.parents):
            return True
    return any(token.text in {"import", "from", "require"} for token in before[-4:])


def classify_change(tag, ours, theirs, before):
    # Turns one token level difference into a named kind of change
    changed = ours if ours else theirs
    if tag == "replace":
        if len(ours) == 1 and len(theirs) == 1:
            old, new = ours[0], theirs[0]
            if old.kind == "string" and new.kind == "string":
                return "import_path_changed" if in_import(ours, before) else "string_literal_changed"
            if old.kind == "identifier" and new.kind == "identifier":
                return "import_name_changed" if in_import(ours, before) else "identifier_changed"
            if old.kind == "number" and new.kind == "number":
                return "number_literal_changed"
            if old.kind == "punct" and new.kind == "punct":
                return "operator_changed"
        return "code_replaced"

    suffix = "added" if tag == "insert" else "removed"
    previous = before[-1].text if before else ""
    texts = [token.text for token in changed]
    has_identifier = any(token.kind == "identifier" for token in changed)
    if previous == "catch" and has_identifier and all(
        token.kind == "identifier" or token.text in {"(", ")"} for token in changed
    ):
        return "catch_binding_" + suffix
    if all(text in PUNCTUATION for text in texts):
        return "punctuation_" + suffix
    if in_import(changed, before):
        return "import_" + suffix
    return "code_" + suffix


def verify_rename(operations, tokens_ours, tokens_theirs):
    # A rename is only confirmed when every difference is an identifier that
    # maps one to one and the old name no longer appears on the other side
    forward, backward = {}, {}
    for tag, ours, theirs in operations:
        if tag != "replace" or len(ours) != len(theirs):
            return None
        for old, new in zip(ours, theirs):
            if old.kind != "identifier" or new.kind != "identifier":
                return None
            if forward.setdefault(old.text, new.text) != new.text:
                return None
            if backward.setdefault(new.text, old.text) != old.text:
                return None
    if not forward:
        return None
    theirs_names = {t.text for t in tokens_theirs if t.kind == "identifier"}
    ours_names = {t.text for t in tokens_ours if t.kind == "identifier"}
    if any(name in theirs_names for name in forward):
        return None
    if any(name in ours_names for name in backward):
        return None
    return forward


def counter_delta(counter_a, counter_b):
    added = dict(sorted((counter_b - counter_a).items()))
    removed = dict(sorted((counter_a - counter_b).items()))
    return added, removed


def build_ast_summary(file_path, ours_text, theirs_text):
    # Main entry point, returns a plain dict that is safe to dump as JSON
    ours_text = ours_text or ""
    theirs_text = theirs_text or ""
    language = detect_language(file_path)

    parsed = choose_and_parse(language, ours_text, theirs_text) if language else None
    if parsed is None:
        # Without a grammar the only safe fact is whether whitespace explains it
        same_without_space = "".join(ours_text.split()) == "".join(theirs_text.split())
        return {
            "language": language,
            "parse": {"status": "no_parser_available"},
            "equivalence": "whitespace_or_layout_only" if same_without_space else "not_analyzed",
            "changes": [],
            "notes": ["no grammar for this file type, read the raw text instead"],
        }

    wrapper_name, ours, theirs = parsed

    # Comments are removed from the token streams before any comparison
    strict_ours = [t.key() for t in ours.tokens]
    strict_theirs = [t.key() for t in theirs.tokens]
    same_tokens = strict_ours == strict_theirs
    same_normalized = normalized_keys(ours.tokens) == normalized_keys(theirs.tokens)

    matcher = difflib.SequenceMatcher(None, strict_ours, strict_theirs, autojunk=False)
    operations = []
    changes = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        ours_slice = ours.tokens[i1:i2]
        theirs_slice = theirs.tokens[j1:j2]
        before = ours.tokens[max(0, i1 - 3):i1]
        after = ours.tokens[i2:i2 + 3]
        operations.append((tag, ours_slice, theirs_slice))
        anchor = (ours_slice or theirs_slice)[0]
        changes.append({
            "kind": classify_change(tag, ours_slice, theirs_slice, before),
            "ours": join_tokens(ours_slice),
            "theirs": join_tokens(theirs_slice),
            "before": join_tokens(before),
            "after": join_tokens(after),
            "inside": [p for p in anchor.parents if p != "ERROR"][-2:],
        })

    rename_map = None
    if same_tokens:
        equivalence = (
            "whitespace_or_layout_only"
            if ours.comments == theirs.comments
            else "comments_only"
        )
    elif same_normalized:
        equivalence = "formatting_only"
    else:
        rename_map = verify_rename(operations, ours.tokens, theirs.tokens)
        equivalence = "identifier_rename_only" if rename_map else "content_changed"

    nodes_added, nodes_removed = counter_delta(ours.node_counts, theirs.node_counts)
    names_ours = Counter(t.text for t in ours.tokens if t.kind == "identifier")
    names_theirs = Counter(t.text for t in theirs.tokens if t.kind == "identifier")
    names_added, names_removed = counter_delta(names_ours, names_theirs)

    kind_counts = Counter(change["kind"] for change in changes)
    notes = []
    if len(changes) > MAX_CHANGES_IN_PAYLOAD:
        notes.append(f"only the first {MAX_CHANGES_IN_PAYLOAD} of {len(changes)} changes are listed")
    if ours.status() == "partial" or theirs.status() == "partial":
        notes.append("the snippet is a code fragment so node types are approximate")
    if ours.comments != theirs.comments and equivalence != "comments_only":
        notes.append("comment text also differs between the two sides")

    summary = {
        "language": language,
        "parse": {
            "ours": ours.status(),
            "theirs": theirs.status(),
            "wrapper": wrapper_name,
        },
        "equivalence": equivalence,
        "change_kind_counts": dict(kind_counts),
        "changes": changes[:MAX_CHANGES_IN_PAYLOAD],
        "node_type_delta": {"added_in_theirs": nodes_added, "removed_from_ours": nodes_removed},
        "identifier_delta": {"added_in_theirs": names_added, "removed_from_ours": names_removed},
        "notes": notes,
    }
    if rename_map:
        summary["rename_map"] = rename_map
    return summary


def format_for_prompt(summary):
    # This is the block that gets placed into the Gemini user message
    header = (
        "AST diff summary computed by a parser. Whitespace, line wrapping, and "
        "comments are already ignored in it. Treat the equivalence field as "
        "fact and use the changes list as the token level evidence."
    )
    return header + "\n" + json.dumps(summary, indent=2)


@dataclass
class ASTEquivalence:
    equivalence: Literal[
        "identical",
        "whitespace_only",
        "comments_only",
        "formatting_only",
        "identifier_rename_only",
        "content_changed",
        "not_analyzed",
    ]
    renames: dict          # {"old_name": "new_name"}
    changed_nodes: list    # ["operator_changed:>\u2192>="]
    parse_error: Optional[str] = None


# Maps the wording used inside build_ast_summary to the names of the gate
_EQUIVALENCE_NAMES = {
    "whitespace_or_layout_only": "whitespace_only",
    "comments_only": "comments_only",
    "formatting_only": "formatting_only",
    "identifier_rename_only": "identifier_rename_only",
    "content_changed": "content_changed",
    "not_analyzed": "not_analyzed",
}


def compute_ast_equivalence(file_path, ours_text, theirs_text):
    # Thin wrapper over build_ast_summary, it returns a structured verdict
    # instead of a prompt string so the caller can branch on it
    ours_text = ours_text or ""
    theirs_text = theirs_text or ""
    if ours_text == theirs_text:
        return ASTEquivalence("identical", {}, [])

    try:
        summary = build_ast_summary(file_path, ours_text, theirs_text)
    except Exception as e:
        return ASTEquivalence("not_analyzed", {}, [], parse_error=str(e))

    parse_error = None
    if summary.get("parse", {}).get("status") == "no_parser_available":
        parse_error = "no_parser_available"

    changed_nodes = [
        f"{change['kind']}:{change['ours']}\u2192{change['theirs']}"
        for change in summary.get("changes", [])
    ]
    return ASTEquivalence(
        equivalence=_EQUIVALENCE_NAMES.get(summary.get("equivalence"), "not_analyzed"),
        renames=dict(summary.get("rename_map") or {}),
        changed_nodes=changed_nodes,
        parse_error=parse_error,
    )


def demo():
    examples = [
        ("catch binding added", "src/api.js",
         "  } catch {\n    logger.warn('failed');\n  }",
         "  } catch (error) {\n    logger.warn('failed');\n  }"),
        ("import path changed", "src/app.ts",
         "import { load } from './utils/loader';",
         "import { load } from './core/loader';"),
        ("whitespace only", "src/math.py",
         "total = a+b",
         "total  =  a + b"),
        ("identifier rename", "src/calc.js",
         "const n = items.length; return n * price;",
         "const count = items.length; return count * price;"),
        ("operator change", "src/gate.js",
         "if (age > 18) { allow(); }",
         "if (age >= 18) { allow(); }"),
    ]
    for title, path, ours, theirs in examples:
        print("=== " + title)
        print(format_for_prompt(build_ast_summary(path, ours, theirs)))
        print()


if __name__ == "__main__":
    if len(sys.argv) == 4:
        # Usage is script file_path ours_file theirs_file
        with open(sys.argv[2], "r", encoding="utf-8") as f_ours, \
                open(sys.argv[3], "r", encoding="utf-8") as f_theirs:
            print(format_for_prompt(build_ast_summary(sys.argv[1], f_ours.read(), f_theirs.read())))
    else:
        demo()