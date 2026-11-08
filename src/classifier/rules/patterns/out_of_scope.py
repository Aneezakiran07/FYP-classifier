# Stage 0 pattern that labels files outside the project scope as unknown with the reason out-of-scope
# It matches built, generated or vendored folders such as dist, build, node_modules, generated and snapshots, plus minified, map, snap and gen.ts files
# It also rejects any file that is not TypeScript, prose, a lockfile, package.json, declarative config or a JavaScript config file
# It runs first of all patterns so nothing else can claim a region inside such a file

import os
import re

from .base import ClassifyInput, DeterministicResult, PatternPlugin
from .comments_only import PROSE_EXTENSIONS
from .config_schema import is_config_name
from .lockfile import LOCKFILE_NAMES
from .package_manifest import PACKAGE_MANIFEST_NAME

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

# Folders and file names of generated TypeScript such as routeTree.gen.ts, added by D14
GENERATED_DIRS = {"__generated__", "generated"}
GENERATED_SUFFIXES = (".gen.ts", ".gen.tsx")


# The report scopes to TypeScript and these match the conflict file definition in the decisions log
TYPESCRIPT_EXTENSIONS = (".ts", ".tsx")

# A JavaScript config file stays in scope and is then handled as code
EXECUTABLE_CONFIG = re.compile(r"\.config\.(?:js|mjs|cjs)$", re.I)


def _segments(path):
    # Splits on both separators and drops empty parts, so a Windows style
    # path and a leading "./" behave the same as a plain relative path.
    normalized = (path or "").replace("\\", "/").lower()
    return [part for part in normalized.split("/") if part and part != "."]


def is_generated_path(path):
    # True for a generated TypeScript file by its folder or its file name
    parts = _segments(path)
    if not parts:
        return False
    return any(segment in GENERATED_DIRS for segment in parts[:-1]) or parts[-1].endswith(GENERATED_SUFFIXES)


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
    if is_generated_path(path):
        return True
    return False


def _is_allowed_file_type(path):
    # Stage 0 keeps TypeScript, lockfiles, manifests, config and prose only
    name = os.path.basename((path or "").replace("\\", "/"))
    lowered = name.lower()
    if lowered.endswith(TYPESCRIPT_EXTENSIONS) or lowered.endswith(PROSE_EXTENSIONS):
        return True
    if name in LOCKFILE_NAMES or name == PACKAGE_MANIFEST_NAME:
        return True
    return is_config_name(name) or bool(EXECUTABLE_CONFIG.search(name))


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
        return _is_out_of_scope(h.file_path) or not _is_allowed_file_type(h.file_path)

    def resolve(self, h: ClassifyInput) -> DeterministicResult:
        return DeterministicResult(
            label="unknown",
            reason="binary, generated, minified, snapshot or vendored path, or a file type outside the scope",
            unknown_reason="out-of-scope",
        )