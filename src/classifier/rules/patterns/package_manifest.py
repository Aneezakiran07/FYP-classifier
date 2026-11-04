import os

from .base import ClassifyInput, DeterministicResult, PatternPlugin

# Taxonomy Group D, dependency/package. Any file named package.json, at
# any depth in the repository, is a package manifest. Monorepo workspaces
# keep their own package.json, and the taxonomy says "any workspace", so
# the match is on the basename only.
PACKAGE_MANIFEST_NAME = "package.json"


class PackageManifest(PatternPlugin):
    # Taxonomy rule 7 and the dependency/package label definition. Path
    # based only, no content check. Rules 1 to 4 still run first in the
    # registry, so byte-identical, one-side-change, whitespace-only, and
    # reorder-only cases are claimed before this pattern is reached.
    #
    # The Group D handler merges at key level and, for the same
    # dependency, picks the higher version within the same major. That
    # work is done in the resolver layer, not here.
    #
    # PRECONDITION for the resolve strategy (not enforced here):
    #   A conflict where the two sides set the same key to values that
    #   cannot be reconciled automatically, for example a different major
    #   version of the same dependency, must be flagged for human review
    #   instead of auto-resolved. The resolver decides this, not the
    #   classifier. The label stays dependency/package either way.
    name = "PackageManifest"
    priority = 70
    requires = "both"
    precedence_rule = 7

    def detect(self, h: ClassifyInput) -> bool:
        return os.path.basename(h.file_path or "") == PACKAGE_MANIFEST_NAME

    def resolve(self, h: ClassifyInput) -> DeterministicResult:
        return DeterministicResult(
            label="dependency/package",
            reason="package manifest conflict, merge at key level",
        )