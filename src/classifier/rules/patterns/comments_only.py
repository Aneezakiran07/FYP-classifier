import os
import re

from .base import ClassifyInput, DeterministicResult, PatternPlugin

# Taxonomy rule 14: file types where a slash-style comment is really a
# comment. In other languages a double slash can be real code, such as
# Python floor division, so those file types never reach the strip path.
C_STYLE_EXTENSIONS = (
    ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".java", ".go",
    ".c", ".h", ".cc", ".cpp", ".hpp", ".cs", ".rs", ".kt", ".swift", ".scala",
)

# Taxonomy rule 14 second sentence: prose-only files are documentation
# by definition, so any content difference in them is documentation.
PROSE_EXTENSIONS = (".md", ".txt", ".rst")

# Taxonomy rule 14 last sentence: directive comments count as code, so a
# difference that lives only in one of these is not documentation. The
# list is taken verbatim from the taxonomy.
DIRECTIVE_PATTERN = re.compile(
    r"@ts-ignore|@ts-expect-error|eslint-disable|prettier-ignore|@jsx|istanbul ignore"
)

# String literals are matched first and kept, so a double slash inside a
# url string is never mistaken for the start of a comment.
_TOKEN = re.compile(
    r'''("(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*'|`(?:\\.|[^`\\])*`)'''
    r"|//[^\n]*|/\*.*?\*/",
    re.S,
)

# A line that is inside a JSDoc block but carries no delimiter of its own,
# such as " * @param foo". It is only treated as a comment while a "/**"
# opener is visible and its closing "*/" has not been seen yet.
_JSDOC_CONTINUATION = re.compile(r"^\s*\*")


def _strip_jsdoc_continuations(text):
    # Replaces a JSDoc continuation line with an empty line so that the
    # token stripper below still sees line structure but the comment
    # content is gone. A line starting with "*" outside a "/**" block, such
    # as a wrapped multiplication, is code and is left alone. The opener and
    # closer lines are also left alone, the token stripper removes them as
    # part of the block comment. A block whose closer is not visible runs to
    # the end of the text.
    result = []
    inside = False
    for line in text.splitlines():
        if inside:
            if "*/" in line:
                inside = False
                result.append(line)
            elif _JSDOC_CONTINUATION.match(line):
                result.append("")
            else:
                result.append(line)
            continue
        result.append(line)
        start = line.find("/**")
        # "/**/" is an empty block comment, not a JSDoc opener.
        if start != -1 and line[start + 3:start + 4] != "/":
            inside = "*/" not in line[start + 3:]
    return "\n".join(result)


def _strip_comments(text):
    # A directive comment is left in place so that a difference confined
    # to it survives the strip and the pattern does not fire. Any other
    # comment is removed.
    text = _strip_jsdoc_continuations(text)
    def replacer(match):
        if match.group(1):
            return match.group(1)
        comment = match.group(0)
        if DIRECTIVE_PATTERN.search(comment):
            return comment
        return " "
    return _TOKEN.sub(replacer, text)


def _collapse(text):
    return re.sub(r"\s+", " ", text or "").strip()


class CommentsOnly(PatternPlugin):
    # Taxonomy rule 14: code identical once comments are stripped. Two
    # detection paths, either one fires the label. Directive comments do
    # not qualify, so a difference that lives only in a directive comment
    # is treated as a code difference and falls through.
    name = "CommentsOnly"
    priority = 40
    requires = "both"
    precedence_rule = 14

    def detect(self, h: ClassifyInput) -> bool:
        path = (h.file_path or "").lower()

        # Path 1, prose files. Any content difference is documentation.
        if path.endswith(PROSE_EXTENSIONS):
            return h.ours_text != h.theirs_text

        # Path 2, C-style code files. Strip comments and compare.
        if not path.endswith(C_STYLE_EXTENSIONS):
            return False
        if _collapse(h.ours_text) == _collapse(h.theirs_text):
            return False
        ours = _collapse(_strip_comments(h.ours_text))
        theirs = _collapse(_strip_comments(h.theirs_text))
        return ours == theirs

    def resolve(self, h: ClassifyInput) -> DeterministicResult:
        return DeterministicResult(
            label="structural/documentation",
            reason="sides are equal once comments are removed",
        )