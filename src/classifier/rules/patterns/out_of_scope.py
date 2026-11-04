import os

from .base import ClassifyInput, DeterministicResult, PatternPlugin

# Taxonomy decision order step 0 and rule 16: binary, generated, minified,
# snapshot and vendored files are out of scope. They are never classified
# and always go to human review.

# Directory names matched as a whole path segment, anywhere in the path.
# A segment such as "rebuild" or "output" does not match, only an exact
# "build" or "out" does.
OUT_OF_SCOPE_DIRS = {
    "dist",
    "build",
    ".next",
    "out",
    "coverage",
    "__snapshots__",
    "node_modules",
    "vendor",
}


def _segments(path):
    # Splits on both separators and drops empty parts, so a Windows style
    # path and a leading "./" behave the same as a plain relative path.
    normalized = (path or "").replace("\\", "/").lower()
    return [part for part in normalized.split("/") if part and part != "."]


def _is_out_of_scope(path):
    parts = _segments(path)
    if not parts:
        return False

    name = parts[-1]
    directories = parts[:-1]

    # Directory rules look only at directory segments, never at the file
    # name, so a file that happens to be called "build" is not matched.
    if any(segment in OUT_OF_SCOPE_DIRS for segment in directories):
        return True

    # File name rules. "*.min.*" means the name carries a ".min." part,
    # as in app.min.js or site.min.css.
    if ".min." in name:
        return True
    if name.endswith(".map"):
        return True
    if name.endswith(".snap"):
        return True
    return False


class OutOfScope(PatternPlugin):
    # Taxonomy decision order step 0 and rule 16: a binary, generated,
    # minified, snapshot or vendored file is labeled unknown with the
    # reason out-of-scope. Path based only, no content check. It runs
    # first of all patterns (priority 0) so that nothing below it can
    # claim a region inside such a file.
    name = "OutOfScope"
    priority = 0
    requires = "both"
    precedence_rule = 16

    def detect(self, h: ClassifyInput) -> bool:
        return _is_out_of_scope(h.file_path)

    def resolve(self, h: ClassifyInput) -> DeterministicResult:
        return DeterministicResult(
            label="unknown",
            reason="binary, generated, minified, snapshot or vendored path",
            unknown_reason="out-of-scope",
        )