# Registry of all rule patterns in stage order, which is also the tie break order
# PATTERNS lists each pattern with its priority, from OutOfScope at Stage 0 to DisjointEdits at Stage 3
# first_match tries the eligible patterns by priority, skips a pattern that crashes, and returns the first name and result
# classify_before_gate runs Stages 0 to 2 before the AST gate, classify_boundary_stage runs Stage 3 after it, and classify_deterministic runs them all

from .base import ClassifyInput, DeterministicResult, PatternPlugin
from .out_of_scope import OutOfScope
from .no_markers import NoMarkers
from .same_change import SameChange
from .value_only_change import ValueOnlyChange
from .one_side_change import OneSideChange
from .whitespace_only import WhitespaceOnly
from .comments_only import CommentsOnly
from .import_restructure import ImportRestructure
from .reorder_only import ReorderOnly
from .lockfile import Lockfile
from .package_manifest import PackageManifest
from .config_schema import ConfigSchema
from .import_path_only import ImportPathOnly
from .disjoint_edits import DisjointEdits

# Order follows the stages of the report, and the stage order is also the tie break order
# Stage 0 is OutOfScope
# Stage 1 is NoMarkers, SameChange and OneSideChange
# Stage 2 is WhitespaceOnly, CommentsOnly, ImportRestructure and ReorderOnly plus the AST gate
# Stage 3 is Lockfile, PackageManifest, ConfigSchema, ValueOnlyChange, ImportPathOnly and DisjointEdits
# ImportPathOnly runs before DisjointEdits so one binding with two paths is not called disjoint
PATTERNS = [
    OutOfScope(),         # priority 0   stage 0
    NoMarkers(),          # priority 5   stage 1
    SameChange(),         # priority 10  stage 1
    OneSideChange(),      # priority 20  stage 1
    WhitespaceOnly(),     # priority 30  stage 2
    CommentsOnly(),       # priority 40  stage 2
    ImportRestructure(),  # priority 45  stage 2
    ReorderOnly(),        # priority 50  stage 2
    Lockfile(),           # priority 60  stage 3
    PackageManifest(),    # priority 70  stage 3
    ConfigSchema(),       # priority 80  stage 3
    ValueOnlyChange(),    # priority 83  stage 3
    ImportPathOnly(),     # priority 85  stage 3
    DisjointEdits(),      # priority 90  stage 3
]

# The first priority of Stage 3, the AST gate runs just before it
BOUNDARY_STAGE_PRIORITY = 60


def first_match(h, patterns):
    # Returns the first matching pattern name and its result, or None
    has_base = h.base_text is not None and h.base_text != ""
    eligible = [p for p in patterns
                if p.requires == "both"
                or (p.requires == "diff3" and has_base)
                or (p.requires == "diff2" and not has_base)]
    for p in sorted(eligible, key=lambda x: x.priority):
        # A broken pattern must never stop a run, it is skipped and the
        # next pattern or the model takes over
        try:
            matched = p.detect(h)
        except Exception as e:
            print(f"  Pattern {p.name} failed, skipping it. Error: {e}")
            continue
        if matched:
            return p.name, p.resolve(h)
    return None


def classify_before_gate(h):
    # Runs the patterns of stages 0 to 2 that come before the AST gate
    return first_match(h, [p for p in PATTERNS if p.priority < BOUNDARY_STAGE_PRIORITY])


def classify_boundary_stage(h):
    # Runs the patterns of Stage 3 that come after the AST gate
    return first_match(h, [p for p in PATTERNS if p.priority >= BOUNDARY_STAGE_PRIORITY])


def classify_deterministic_named(h):
    # Runs every pattern in order without the AST gate
    return first_match(h, PATTERNS)


def classify_deterministic(h):
    matched = classify_deterministic_named(h)
    return matched[1] if matched else None
