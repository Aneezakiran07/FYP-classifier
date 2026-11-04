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

# Order follows the taxonomy decision order. OutOfScope is step 0 and
# claims binary, generated, minified, snapshot and vendored paths before
# anything else. NoMarkers and SameChange follow (rules 2 and 1).
# ValueOnlyChange (rule 6, first branch) sits ahead of OneSideChange but
# steps aside when a side equals base, so rule 2 still wins. OneSideChange
# is rule 2 and beats every rule below it when base is present, then the
# shape checks: whitespace, comments, import restructure (rule 4 and rule 5
# case 1), reorder. Then the file-type gate (rule 7), which claims
# lockfiles, manifests and config files after rules 1 to 4. ImportPathOnly
# (rule 5 case 3) runs ahead of DisjointEdits so a same binding with two
# paths is not absorbed as a disjoint edit. DisjointEdits is last because
# rule 8 only fires when nothing earlier matched.
PATTERNS = [
    OutOfScope(),         # priority 0   taxonomy step 0 (rule 16)
    NoMarkers(),          # priority 5   special: region has no text
    SameChange(),         # priority 10  taxonomy rule 1
    ValueOnlyChange(),    # priority 15  taxonomy rule 6 first branch
    OneSideChange(),      # priority 20  taxonomy rule 2 (requires diff3)
    WhitespaceOnly(),     # priority 30  taxonomy rule 3
    CommentsOnly(),       # priority 40  taxonomy rule 14
    ImportRestructure(),  # priority 45  taxonomy rule 4 and rule 5 case 1
    ReorderOnly(),        # priority 50  taxonomy rule 4
    Lockfile(),           # priority 60  taxonomy rule 7
    PackageManifest(),    # priority 70  taxonomy rule 7
    ConfigSchema(),       # priority 80  taxonomy rule 7
    ImportPathOnly(),     # priority 85  taxonomy rule 5 case 3
    DisjointEdits(),      # priority 90  taxonomy rule 8 (requires diff3)
]


def classify_deterministic_named(h):
    # Returns the matching pattern name together with its result so the
    # caller can count matches per pattern, None means nothing matched
    has_base = h.base_text is not None and h.base_text != ""
    eligible = [p for p in PATTERNS
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


def classify_deterministic(h):
    matched = classify_deterministic_named(h)
    return matched[1] if matched else None