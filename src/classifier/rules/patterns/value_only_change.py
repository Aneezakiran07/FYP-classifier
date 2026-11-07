# Stage 3 pattern that labels a region value-only-change when only one infrastructure literal differs
# The two sides must have equal tokens except for one number or string bound to a name or passed as a call argument
# That name must hold an infrastructure word such as port or timeout and no business word such as price, and manifest and config paths are skipped
# It steps aside when one side still equals the base, and the result is marked policy resolved

import os
import re

from .base import ClassifyInput, DeterministicResult, PatternPlugin
from .config_schema import ConfigSchema
from .lockfile import LOCKFILE_NAMES
from .package_manifest import PACKAGE_MANIFEST_NAME

# Taxonomy Group A word lists, copied from the taxonomy unchanged.
INFRA_WORDS = frozenset({
    "timeout", "ttl", "delay", "interval", "debounce", "throttle", "retry",
    "retries", "attempts", "backoff", "port", "buffer", "chunk", "batch",
    "poll", "concurrency", "width", "height", "padding", "margin", "duration",
})
BUSINESS_VETO_WORDS = frozenset({
    "price", "cost", "fee", "tax", "discount", "rate", "amount", "total",
    "balance", "score", "quota",
})

# Callee candidates that are really keywords, so `if (x, 5)` or
# `return (5)` never counts as a call with an infrastructure name.
_NON_CALLEES = frozenset({
    "if", "elif", "else", "for", "while", "switch", "catch", "return",
    "typeof", "await", "yield", "function", "with", "in", "of", "and",
    "or", "not", "assert",
})

_OPEN = frozenset({"(", "[", "{"})
_CLOSE = frozenset({")", "]", "}"})

# Lexical tokenizer. Comments and template literals are their own token
# kinds so a literal inside a comment is never mistaken for code, and a
# template literal is never treated as a plain literal. Anything else
# unmatched becomes a one character operator token.
_TOKEN = re.compile(
    r"""
    (?P<comment>//[^\n]*|/\*.*?\*/|\#[^\n]*)
  | (?P<template>`(?:\\.|[^`\\])*`)
  | (?P<string>"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*')
  | (?P<number>0[xX][0-9a-fA-F_]+|0[bB][01_]+|0[oO][0-7_]+
      |(?:\d[\d_]*\.?[\d_]*|\.\d[\d_]*)(?:[eE][+-]?\d+)?)
  | (?P<ident>[A-Za-z_$][\w$]*)
  | (?P<op>===|!==|==|!=|<=|>=|=>|:=|\+=|-=|\*=|/=|%=|&&|\|\||\?\?|\S)
    """,
    re.S | re.X,
)

_KEY_NAME = re.compile(r"^[\w$-]+$")


def _tokenize(text):
    return [(m.lastgroup, m.group(0)) for m in _TOKEN.finditer(text or "")]


def _collapse(text):
    return re.sub(r"\s+", " ", text or "").strip()


def _is_manifest_or_config_path(h, config_paths):
    # Rule 7: lockfiles, package manifests and declarative config files
    # belong to Group D, so this pattern never fires on them.
    name = os.path.basename(h.file_path or "")
    if name in LOCKFILE_NAMES or name == PACKAGE_MANIFEST_NAME:
        return True
    return config_paths.detect(h)


def _name_of(token):
    # A binding name is a plain identifier or a quoted property key such
    # as 'retry-delay'. Anything else, such as a number or a closing
    # bracket, is not a name.
    kind, text = token
    if kind == "ident":
        return text
    if kind == "string" and len(text) >= 2:
        inner = text[1:-1]
        if _KEY_NAME.match(inner):
            return inner
    return None


def _callee_name(tokens, index):
    # The literal is a direct call argument when the nearest unmatched
    # opening bracket to its left is a parenthesis. The callee is the
    # identifier just before that parenthesis.
    depth = 0
    for k in range(index - 1, -1, -1):
        kind, text = tokens[k]
        if kind != "op":
            continue
        if text in _CLOSE:
            depth += 1
        elif text in _OPEN:
            if depth == 0:
                if text != "(" or k == 0:
                    return None
                callee_kind, callee_text = tokens[k - 1]
                if callee_kind != "ident" or callee_text in _NON_CALLEES:
                    return None
                return callee_text
            depth -= 1
    return None


def _nearest_binding_name(tokens, index):
    # Returns the binding name a literal is attached to, or None when the
    # literal sits in a condition, a return value, an operand or any other
    # shape that is not a binding. Handles:
    #   name = literal, name: literal, name := literal
    #   name: Type = literal   (one token type annotation)
    #   callee(literal) and callee(a, literal)
    if index == 0:
        return None
    previous = tokens[index - 1][1]
    if tokens[index - 1][0] == "op" and previous in ("=", ":", ":="):
        j = index - 2
        if j < 0:
            return None
        if previous == "=" and j >= 2 and tokens[j - 1][1] == ":" and tokens[j][0] == "ident":
            j -= 2
        return _name_of(tokens[j])
    if tokens[index - 1][0] == "op" and previous in ("(", ","):
        return _callee_name(tokens, index)
    return None


def _words(name):
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name)
    spaced = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", spaced)
    return {w.lower() for w in re.split(r"[^A-Za-z0-9]+", spaced) if w}


def _is_infra_name(name):
    # Infra words match as whole words after camelCase and snake_case
    # splitting, so "report" never matches "port". Business veto words
    # match as substrings, which can only make the pattern under-fire.
    if not name:
        return False
    squashed = re.sub(r"[^a-z0-9]", "", name.lower())
    if any(word in squashed for word in BUSINESS_VETO_WORDS):
        return False
    return bool(_words(name) & INFRA_WORDS)


def _same_literal_value(old, new):
    # The same value written two ways is a formatting difference, not a
    # value change, so it is left to other rules.
    kind, old_text = old
    _, new_text = new
    if kind == "string":
        return old_text[1:-1] == new_text[1:-1]
    return old_text.replace("_", "").lower() == new_text.replace("_", "").lower()


class ValueOnlyChange(PatternPlugin):
    # Taxonomy rule 6, first branch, and the mechanical/value-only-change
    # label definition. The token sequences of the two sides are equal
    # except for exactly one number or string literal, the nearest binding
    # name contains an infrastructure word, and it contains no business
    # veto word. Manifest, lockfile and config paths are skipped (rule 7).
    #
    # This pattern belongs to Stage 3 so OneSideChange always runs first
    # It still steps aside when a side equals the base after whitespace collapsing
    #
    # Without base the label still fires, with base_available=False, as
    # the taxonomy's "When base is unavailable" table requires.
    # resolve() sets policy_resolved=True because the resolution is a
    # configurable policy pick, not a verified merge.
    name = "ValueOnlyChange"
    priority = 83
    requires = "both"
    precedence_rule = 6

    def __init__(self):
        self._config_paths = ConfigSchema()

    def detect(self, h: ClassifyInput) -> bool:
        if not h.ours_text or not h.theirs_text:
            return False
        if h.ours_text == h.theirs_text:
            return False
        if _is_manifest_or_config_path(h, self._config_paths):
            return False

        if h.base_text:
            base = _collapse(h.base_text)
            if _collapse(h.ours_text) == base or _collapse(h.theirs_text) == base:
                return False

        ours = _tokenize(h.ours_text)
        theirs = _tokenize(h.theirs_text)
        if len(ours) != len(theirs):
            return False

        differing = [i for i, (a, b) in enumerate(zip(ours, theirs)) if a != b]
        if len(differing) != 1:
            return False

        index = differing[0]
        old, new = ours[index], theirs[index]
        if old[0] != new[0] or old[0] not in ("number", "string"):
            return False
        if _same_literal_value(old, new):
            return False

        return _is_infra_name(_nearest_binding_name(ours, index))

    def resolve(self, h: ClassifyInput) -> DeterministicResult:
        return DeterministicResult(
            label="mechanical/value-only-change",
            reason="only an infrastructure literal differs",
            confidence="high",
            base_available=bool(h.base_text),
            policy_resolved=True,
        )