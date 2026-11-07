# Stage 1 pattern that labels a region one-side-change when exactly one side differs from the base
# It needs a base, collapses whitespace on every file type, and for JavaScript and TypeScript also ignores semicolons, quote style and trailing commas
# Formatting normalization is turned off when any side holds a regex literal or markup
# Deletions count too, where one side is empty and the other side still equals the base

import re

from .base import ClassifyInput, DeterministicResult, PatternPlugin

# Formatting normalization (semicolons, quote style, trailing commas) is
# applied only to the JavaScript and TypeScript family. In other languages
# these differences can change meaning, for example a quoted character
# versus a string, so only whitespace is normalized there.
FORMATTING_EXTENSIONS = (".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx")

# Comments, quoted strings and template literals are matched so their
# contents are never touched by the semicolon and comma rules.
_TOKEN = re.compile(
    r"(?P<comment>//[^\n]*|/\*.*?\*/)"
    r"""|(?P<string>"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*')"""
    r"|(?P<template>`(?:\\.|[^`\\])*`)",
    re.S,
)

# A slash that starts a regex literal, whose quotes and semicolons are
# part of the pattern. Markup text has the same problem. Either one turns
# the formatting normalization off for the whole region.
_REGEX_LITERAL = re.compile(r"(?:[=(,:;!&|?{}\[]|\breturn|\btypeof)\s*/(?![/*=])")
_MARKUP = re.compile(r"</|/>")

_TRAILING_COMMA = re.compile(r",\s*([)\]}])")


def _collapse(text):
    # Every run of whitespace becomes one space so indentation, blank
    # lines, and line endings stop mattering when a side is compared
    # against base. Same rule the taxonomy applies to rule 2.
    return re.sub(r"\s+", " ", text or "").strip()


def _canonical_string(literal):
    # Rewrites a quoted string to double quotes with the same value. An
    # escaped quote of either kind is unescaped, then any double quote in
    # the value is escaped again, so two different strings never collide.
    inner = literal[1:-1]
    value = []
    i = 0
    while i < len(inner):
        ch = inner[i]
        if ch == "\\" and i + 1 < len(inner):
            nxt = inner[i + 1]
            value.append(nxt if nxt in "'\"" else ch + nxt)
            i += 2
            continue
        value.append(ch)
        i += 1
    return '"' + "".join(value).replace('"', '\\"') + '"'


def _normalize_code(code):
    # A semicolon becomes a space so that neighbours never merge into one
    # token, a trailing comma before a closer is dropped.
    code = code.replace(";", " ")
    return _TRAILING_COMMA.sub(r"\1", code)


def _normalize_formatting(text):
    parts = []
    last = 0
    for match in _TOKEN.finditer(text):
        parts.append(_normalize_code(text[last:match.start()]))
        if match.group("string"):
            parts.append(_canonical_string(match.group(0)))
        else:
            parts.append(match.group(0))
        last = match.end()
    parts.append(_normalize_code(text[last:]))
    return "".join(parts)


def _formatting_applies(file_path, texts):
    path = (file_path or "").lower()
    if not path.endswith(FORMATTING_EXTENSIONS):
        return False
    for text in texts:
        if _REGEX_LITERAL.search(text or "") or _MARKUP.search(text or ""):
            return False
    return True


def _normalize(text, formatting):
    text = text or ""
    if formatting:
        text = _normalize_formatting(text)
    return _collapse(text)


class OneSideChange(PatternPlugin):
    # Taxonomy rule 2: if one side equals base after whitespace and
    # formatting normalization, the label is mechanical/one-side-change.
    # This includes deletions, where one side is empty and the other
    # equals base. A side that was only reformatted counts as untouched.
    # Whitespace normalization applies to every file type. Formatting
    # normalization (semicolons, quote style, trailing commas) applies to
    # JavaScript and TypeScript files only, and only when none of base,
    # ours or theirs holds a regex literal or markup, so a side that
    # differs from base only by those three things counts as untouched.
    # Parentheses and braces are not normalized. Needs diff3, without base
    # this pattern never runs and the region goes on to the model instead.
    name = "OneSideChange"
    priority = 20
    requires = "diff3"
    precedence_rule = 2

    def detect(self, h: ClassifyInput) -> bool:
        if not h.base_text:
            return False
        formatting = _formatting_applies(
            h.file_path, (h.base_text, h.ours_text, h.theirs_text)
        )
        base = _normalize(h.base_text, formatting)
        ours = _normalize(h.ours_text, formatting)
        theirs = _normalize(h.theirs_text, formatting)
        return (ours == base) != (theirs == base)

    def resolve(self, h: ClassifyInput) -> DeterministicResult:
        return DeterministicResult(
            label="mechanical/one-side-change",
            confidence="high",
            reason="only one side changed relative to base",
        )