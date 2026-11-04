import os

from .base import ClassifyInput, DeterministicResult, PatternPlugin

# Taxonomy Group D, dependency/lockfile. The label is decided purely by
# path. Any conflict inside one of these files is a lockfile conflict,
# and the handler is to regenerate the file from the merged manifest
# rather than text-merge it.
#
# Only these four exact filenames count. Other YAML files such as
# docker-compose.yml or a workflow file are NOT lockfiles and are handled
# by dependency/config-schema instead.
LOCKFILE_NAMES = (
    "package-lock.json",
    "npm-shrinkwrap.json",
    "yarn.lock",
    "pnpm-lock.yaml",
)


class Lockfile(PatternPlugin):
    # Taxonomy rule 7 and the dependency/lockfile label definition. Path
    # based only, no content check. Rules 1 to 4 still run first in the
    # registry, so byte-identical, one-side-change, whitespace-only, and
    # reorder-only cases are claimed before this pattern is reached.
    #
    # PRECONDITION for the resolve strategy (not enforced here):
    #   Regeneration requires the sibling manifest to exist and be
    #   parseable. Every lockfile above sits next to package.json in the
    #   same directory. If package.json is missing, is itself conflicted,
    #   or is unparseable, regeneration cannot complete. The classifier
    #   does NOT check this, because it sees one region and one path, not
    #   the repo tree. The check belongs to the resolver layer, which
    #   must flag the region for human review when the precondition
    #   fails. The label stays dependency/lockfile either way.
    name = "Lockfile"
    priority = 60
    requires = "both"
    precedence_rule = 7

    def detect(self, h: ClassifyInput) -> bool:
        return os.path.basename(h.file_path or "") in LOCKFILE_NAMES

    def resolve(self, h: ClassifyInput) -> DeterministicResult:
        return DeterministicResult(
            label="dependency/lockfile",
            reason="lockfile conflict, regenerate from the merged manifest",
        )