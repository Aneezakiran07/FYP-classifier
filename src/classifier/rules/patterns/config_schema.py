import os

from .base import ClassifyInput, DeterministicResult, PatternPlugin

# Taxonomy Group D, dependency/config-schema. Any declarative config file
# whose values are merged at key level. Executable config files such as
# vite.config.ts, eslint.config.js, or next.config.mjs are NOT matched
# here, because none of the patterns below can match them. They go
# through the logic layers as code.

# Filenames matched exactly.
EXACT_NAMES = {
    "jsconfig.json",
}

# Filenames matched as a prefix followed by either the end of the name or
# a dot. For example .eslintrc, .eslintrc.json, .eslintrc.cjs all match
# the .eslintrc prefix. This mirrors the taxonomy's ".eslintrc*" style.
# tsconfig is NOT here because it needs the strict .json check below.
PREFIX_NAMES = (
    ".eslintrc",
    ".prettierrc",
    ".babelrc",
    ".env",
)

# Extensions whose files are declarative config in the taxonomy, treated
# as keyed structures that merge at key level.
CONFIG_EXTENSIONS = (
    ".yml",
    ".yaml",
    ".toml",
    ".json",
)


def _basename(path):
    return os.path.basename(path or "")


def _matches_tsconfig(name):
    # taxonomy says tsconfig*.json, so tsconfig.json, tsconfig.build.json,
    # tsconfig.node.json all match. A file named tsconfig alone does not.
    return name.startswith("tsconfig") and name.endswith(".json")


def _matches_prefix(name, prefix):
    if name == prefix:
        return True
    # The dot form covers .env.local, .eslintrc.json, .prettierrc.yaml.
    return name.startswith(prefix + ".")


class ConfigSchema(PatternPlugin):
    # Taxonomy rule 7 and the dependency/config-schema label definition.
    # Path based only, no content check. Rules 1 to 4 still run first in
    # the registry, so byte-identical, one-side-change, whitespace-only,
    # and reorder-only cases are claimed before this pattern is reached.
    #
    # Priority ordering interacts with the other Group D patterns.
    # Lockfile (priority 60) claims package-lock.json, npm-shrinkwrap.json,
    # yarn.lock, pnpm-lock.yaml. PackageManifest (priority 70) claims
    # package.json at any depth. Those run before this pattern, so the
    # generic .json and .yaml matches below never touch a lockfile or a
    # package manifest.
    #
    # PRECONDITION for the resolve strategy (not enforced here):
    #   The Group D handler merges at key level and flags any key that
    #   both sides set to different values. The classifier does not do
    #   this merge, the resolver does. The label stays
    #   dependency/config-schema either way.
    name = "ConfigSchema"
    priority = 80
    requires = "both"
    precedence_rule = 7

    def detect(self, h: ClassifyInput) -> bool:
        name = _basename(h.file_path)
        if not name:
            return False

        if name in EXACT_NAMES:
            return True
        if _matches_tsconfig(name):
            return True
        if any(_matches_prefix(name, prefix) for prefix in PREFIX_NAMES):
            return True
        if name.lower().endswith(CONFIG_EXTENSIONS):
            return True
        return False

    def resolve(self, h: ClassifyInput) -> DeterministicResult:
        return DeterministicResult(
            label="dependency/config-schema",
            reason="declarative config conflict, merge at key level",
        )