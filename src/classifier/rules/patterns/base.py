from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Literal

Label = Literal[
    "mechanical/same-change",
    "mechanical/one-side-change",
    "mechanical/whitespace-only",
    "mechanical/reorder-only",
    "mechanical/value-only-change",
    "mechanical/disjoint-edits",
    "structural/formatting",
    "structural/documentation",
    "structural/import-restructure",
    "structural/rename",
    "logic/null-safety-conflict",
    "logic/type-incompatibility",
    "logic/execution-perturbation",
    "logic/overlap-contamination",
    "logic/assignment-override",
    "logic/confluent-interference",
    "logic/business-logic-conflict",
    "dependency/lockfile",
    "dependency/package",
    "dependency/config-schema",
    "dependency/import-path",
    "dependency/export-shape",
    "unknown",
]


@dataclass
class ClassifyInput:
    file_path: str
    ours_text: str
    theirs_text: str
    base_text: Optional[str] = None        # None when only diff2 is available
    region: Optional[dict] = None          # raw region dict from input JSONL
    ast_equivalence: Optional[str] = None  # gate verdict, when the gate ran
    context_lines: int = 20                # visible window used by context checks


@dataclass
class DeterministicResult:
    label: Label
    reason: str
    confidence: str = "high"
    logic_subtype: Optional[str] = None
    base_available: bool = True
    graph_unavailable: bool = True
    policy_resolved: bool = False
    unknown_reason: Optional[str] = None
    candidate_labels: Optional[list] = None


class PatternPlugin(ABC):
    # Every pattern sets these three class attributes, the registry reads
    # them to decide which patterns are eligible and in what order to try
    # them. precedence_rule records the taxonomy precedence rule number
    # (1-16) the pattern implements and is documentation only, never read
    # at runtime.
    name: str
    priority: int                          # lower = tried first
    requires: Literal["diff2", "diff3", "both"]
    precedence_rule: int = 0

    @abstractmethod
    def detect(self, h: ClassifyInput) -> bool: ...

    @abstractmethod
    def resolve(self, h: ClassifyInput) -> DeterministicResult: ...