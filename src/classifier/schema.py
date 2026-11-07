# Shared types and constants used by both the rules side and the llm side
# It defines the 23 LABELS, the three statuses, the two sources and the four base states
# strip_family and bare_label clean label names, find_base_state reads the base state and compute_input_hash fingerprints a region
# Region holds one conflict and its join key, TestAnswer holds one logic test answer, and Result checks the record rules and builds the classifier block

# shared record types and constants
# this module is shared and changes need both owners to agree
# it imports nothing from rules or llm so both sides can use it
# Defines labels, statuses, Region, Result and test-answer structures
import hashlib
import json
from dataclasses import dataclass, field
from typing import Optional


# The 23 labels of Table 5.1 in table order
LABELS = (
    "same-change",
    "one-side-change",
    "whitespace-only",
    "reorder-only",
    "value-only-change",
    "disjoint-edits",
    "formatting",
    "documentation",
    "import-restructure",
    "rename",
    "null-safety-conflict",
    "type-incompatibility",
    "execution-perturbation",
    "overlap-contamination",
    "assignment-override",
    "confluent-interference",
    "business-logic-conflict",
    "lockfile",
    "package",
    "config-schema",
    "import-path",
    "export-shape",
    "unknown",
)

UNKNOWN_LABEL = "unknown"

STATUS_CLASSIFIED = "classified"
STATUS_CAPPED = "capped"
STATUS_LLM_ERROR = "llm-error"
STATUSES = (STATUS_CLASSIFIED, STATUS_CAPPED, STATUS_LLM_ERROR)

# A region with one of these statuses is recorded with no label
UNLABELED_STATUSES = (STATUS_CAPPED, STATUS_LLM_ERROR)

SOURCE_RULE = "rule"
SOURCE_MODEL = "model"

BASE_PRESENT = "present"
BASE_EMPTY = "empty"
BASE_MISSING = "missing"
BASE_NO_MARKERS = "no-markers"
BASE_STATES = (BASE_PRESENT, BASE_EMPTY, BASE_MISSING, BASE_NO_MARKERS)


def strip_family(label):
    # Removes the old family prefix and leaves any other text as it is
    return label.rsplit("/", 1)[-1] if label else label


def bare_label(label):
    # Returns the Table 5.1 name and refuses anything outside the taxonomy
    name = strip_family(label)
    if name not in LABELS:
        raise ValueError(f"{label!r} is not one of the 23 labels")
    return name


def find_base_state(raw):
    # Tells apart a base that is empty from a base that was never available
    if raw.get("no_markers"):
        return BASE_NO_MARKERS
    base_text = raw.get("base_text")
    if base_text is None:
        return BASE_MISSING
    return BASE_PRESENT if base_text else BASE_EMPTY


def compute_input_hash(raw):
    # Hashes everything the classifier reads from one region
    # Missing text stays null so a missing base never matches an empty base
    fields = {
        "file_path": raw.get("file_path"),
        "conflict_type": raw.get("conflict_type"),
        "base_text": raw.get("base_text"),
        "ours_text": raw.get("ours_text"),
        "theirs_text": raw.get("theirs_text"),
    }
    canonical = json.dumps(fields, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass
class Region:
    # One conflict region and its join key
    pr_key: str
    file_path: str
    effective_index: object
    conflict_index: Optional[int]
    ours_text: str
    theirs_text: str
    base_text: Optional[str]
    base_state: str
    input_hash: str
    raw: dict

    @classmethod
    def from_raw(cls, pr_key, position, raw):
        # A no marker region has no conflict index so its list position is used
        conflict_index = raw.get("conflict_index")
        effective_index = (
            conflict_index if conflict_index is not None else f"no_markers_{position}"
        )
        return cls(
            pr_key=pr_key,
            file_path=raw.get("file_path"),
            effective_index=effective_index,
            conflict_index=conflict_index,
            ours_text=raw.get("ours_text") or "",
            theirs_text=raw.get("theirs_text") or "",
            base_text=raw.get("base_text"),
            base_state=find_base_state(raw),
            input_hash=compute_input_hash(raw),
            raw=raw,
        )

    @property
    def key(self):
        return (self.pr_key, self.file_path, self.effective_index)


@dataclass
class TestAnswer:
    # The answer of the model to one logic test
    # The flag below stops pytest from collecting this class as a test
    __test__ = False

    test_id: str
    met: bool
    evidence: Optional[str] = None


@dataclass
class Result:
    # The decision for one region, written out as the classifier block
    status: str
    stage: int
    source: Optional[str] = None
    label: Optional[str] = None
    reason: Optional[str] = None
    base_state: Optional[str] = None
    input_hash: Optional[str] = None
    trace: list = field(default_factory=list)
    confirming_test: Optional[str] = None
    changed_names: list = field(default_factory=list)
    joint_use_lines: list = field(default_factory=list)
    provenance: dict = field(default_factory=dict)
    # Older fields that are kept in the block next to the report fields
    extra: dict = field(default_factory=dict)

    def check(self):
        # Refuses a block that breaks the record rules of the report
        if self.status not in STATUSES:
            raise ValueError(f"{self.status!r} is not a known status")
        if self.status in UNLABELED_STATUSES and self.label is not None:
            raise ValueError(f"status {self.status} must not carry a label")
        if self.status == STATUS_CLASSIFIED and self.label not in LABELS:
            raise ValueError(f"{self.label!r} is not one of the 23 labels")
        needs_reason = self.status != STATUS_CLASSIFIED or self.label == UNKNOWN_LABEL
        if needs_reason and not self.reason:
            raise ValueError(f"status {self.status} with label {self.label} needs a reason")

    def to_block(self):
        self.check()
        block = {} if self.label is None else {"label": self.label}
        block.update({
            "status": self.status,
            "reason": self.reason,
            "stage": self.stage,
            "source": self.source,
            "base_state": self.base_state,
            "input_hash": self.input_hash,
            "trace": self.trace,
            "confirming_test": self.confirming_test,
            "changed_names": self.changed_names,
            "joint_use_lines": self.joint_use_lines,
            "provenance": self.provenance,
        })
        block.update(self.extra)
        return block
