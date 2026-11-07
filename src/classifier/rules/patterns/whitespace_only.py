# Stage 2 pattern that labels a region whitespace-only when both sides have the same tokens and differ only in spacing
# Tokens come from the tree sitter TypeScript grammar when a snippet parses cleanly, otherwise from a simple lexical tokenizer
# Strings, template literals and comments are single tokens, and Python, YAML and Makefile files are skipped because indentation matters there
# It steps aside when line ending return, throw, break, continue or yield counts differ, and _asi_sensitive_count is reused by the AST gate

import os
import re

from .base import ClassifyInput, DeterministicResult, PatternPlugin

# Taxonomy rule 3 says whitespace-only does not apply to languages where
# indentation is significant, because there a whitespace change alters
# behavior. Those file types fall through to later rules or to the model.
INDENT_SIGNIFICANT_EXTENSIONS = (
    ".py", ".pyi", ".yaml", ".yml", ".mk",
)
INDENT_SIGNIFICANT_NAMES = (
    "Makefile", "makefile", "GNUmakefile",
)

# Which tree-sitter grammar to try for which file type. The tsx grammar is
# used for plain JavaScript as well because JavaScript may carry JSX.
_TYPESCRIPT_EXTENSIONS = (".ts",)
_TSX_EXTENSIONS = (".tsx", ".jsx", ".js", ".mjs", ".cjs")

# File types where JSX markup may appear. The lexical fallback cannot
# judge whitespace inside JSX text, so it steps aside when markup is seen.
_MARKUP_EXTENSIONS = (".jsx", ".tsx", ".js", ".mjs", ".cjs")

# Nodes kept whole as one token so whitespace inside them stays visible.
_WHOLE_NODE_TYPES = frozenset(
    {"string", "template_string", "regex", "jsx_text", "comment"}
)

# Multi character operators, longest first within the same prefix, so that
# "a + +b" and "a++b" stay different token sequences.
_OPERATORS = (
    ">>>=", "...", "===", "!==", "**=", "<<=", ">>=", ">>>", "&&=", "||=",
    "??=", "=>", "==", "!=", "<=", ">=", "&&", "||", "??", "?.", "++", "--",
    "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=", "<<", ">>", "**", "->",
    "::", ":=",
)

# Lexical tokenizer. Comments and string or template literals are single
# tokens, so whitespace inside them is a real difference. Whitespace between
# tokens is skipped because no group matches it.
_LEXER = re.compile(
    r"(?P<comment>//[^\n]*|/\*.*?\*/|#[^\n]*)"
    r"""|(?P<string>"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*'|`(?:\\.|[^`\\])*`)"""
    r"|(?P<word>[\w$]+)"
    r"|(?P<op>" + "|".join(re.escape(op) for op in _OPERATORS) + r"|\S)",
    re.S,
)

# A keyword that ends its line. A newline after one of these can change
# behavior through automatic semicolon insertion, so the two sides must
# agree on how many of them there are.
_ASI_KEYWORD_EOL = re.compile(r"\b(?:return|throw|break|continue|yield)[ \t]*\r?\n")

# A slash that starts a regex literal. Whitespace inside a regex literal is
# significant and the lexer cannot tell it from division reliably.
_REGEX_START = re.compile(r"(?:[=(,:;!&|?{}\[]|\breturn|\btypeof)\s*/(?![/*=])")

_MARKUP = re.compile(r"</|/>")

_PARSERS = {}


def _get_parser(path):
    # Grammars are loaded lazily and cached. A missing package gives None
    # and the lexical tokenizer takes over.
    lowered = (path or "").lower()
    if lowered.endswith(_TYPESCRIPT_EXTENSIONS):
        loader = "language_typescript"
    elif lowered.endswith(_TSX_EXTENSIONS):
        loader = "language_tsx"
    else:
        return None
    if loader in _PARSERS:
        return _PARSERS[loader]
    parser = None
    try:
        from tree_sitter import Language, Parser
        import tree_sitter_typescript
        parser = Parser(Language(getattr(tree_sitter_typescript, loader)()))
    except Exception:
        parser = None
    _PARSERS[loader] = parser
    return parser


def _tree_tokens(parser, text):
    # Returns the ordered leaf token texts, or None when the snippet does not
    # parse cleanly. Conflict regions are often fragments, and a fragment with
    # parse errors is better judged by the lexical tokenizer.
    try:
        source = text.encode("utf-8")
        root = parser.parse(source).root_node
        if root.has_error:
            return None
        tokens = []
        stack = [root]
        while stack:
            node = stack.pop()
            if node.is_missing:
                return None
            if node.type in _WHOLE_NODE_TYPES or node.child_count == 0:
                piece = source[node.start_byte:node.end_byte].decode("utf-8", errors="replace")
                if piece.strip():
                    tokens.append(piece)
                continue
            stack.extend(reversed(node.children))
        return tokens
    except Exception:
        return None


def _lex_tokens(text):
    return [m.group(0) for m in _LEXER.finditer(text or "")]


def _code_view(text):
    # The text with comments and string literals removed, used only by the
    # regex literal guard.
    return " ".join(
        m.group(0) for m in _LEXER.finditer(text or "") if m.lastgroup in ("word", "op")
    )


def _asi_sensitive_count(text):
    return len(_ASI_KEYWORD_EOL.findall(text or ""))


def _lexical_equal(path, ours, theirs):
    if (path or "").lower().endswith(_MARKUP_EXTENSIONS):
        if _MARKUP.search(ours) or _MARKUP.search(theirs):
            return False
    if _REGEX_START.search(_code_view(ours)) or _REGEX_START.search(_code_view(theirs)):
        return False
    return _lex_tokens(ours) == _lex_tokens(theirs)


class WhitespaceOnly(PatternPlugin):
    # Taxonomy rule 3: identical token sequences, different spacing. Byte
    # identical sides are excluded (that is rule 1) and indentation-
    # significant file types are excluded (they are the taxonomy's stated
    # exception). A difference inside a string, template literal or comment
    # is a real difference because those are single tokens.
    #
    # Tokens come from tree_sitter_typescript when it is installed and the
    # snippet parses cleanly. Otherwise a lexical tokenizer is used. It
    # returns False, so the model decides, when the text holds a regex
    # literal or JSX markup, and when the two sides differ in the number of
    # line-ending return, throw, break, continue or yield keywords, since a
    # newline there can change behavior.
    name = "WhitespaceOnly"
    priority = 30
    requires = "both"
    precedence_rule = 3

    def detect(self, h: ClassifyInput) -> bool:
        if h.ours_text == h.theirs_text:
            return False
        path = h.file_path or ""
        base_name = os.path.basename(path)
        if base_name in INDENT_SIGNIFICANT_NAMES:
            return False
        if path.lower().endswith(INDENT_SIGNIFICANT_EXTENSIONS):
            return False

        ours = h.ours_text or ""
        theirs = h.theirs_text or ""
        if _asi_sensitive_count(ours) != _asi_sensitive_count(theirs):
            return False

        parser = _get_parser(path)
        if parser is not None:
            ours_tokens = _tree_tokens(parser, ours)
            theirs_tokens = _tree_tokens(parser, theirs)
            if ours_tokens is not None and theirs_tokens is not None:
                return ours_tokens == theirs_tokens

        return _lexical_equal(path, ours, theirs)

    def resolve(self, h: ClassifyInput) -> DeterministicResult:
        return DeterministicResult(
            label="mechanical/whitespace-only",
            reason="token sequences are identical, only spacing differs",
        )