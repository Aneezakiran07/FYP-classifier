# Stage 1 pattern for records with no conflict markers, where there is no text to compare
# A whole file deleted on one side and modified on the other is labeled business-logic-conflict
# Every other no marker conflict type is labeled unknown with the reason no-markers
# DELETION_TYPES lists the two conflict types that mean one side deleted the file

from .base import ClassifyInput, DeterministicResult, PatternPlugin

DELETION_TYPES = ("deleted_by_us", "deleted_by_them")


class NoMarkers(PatternPlugin):
    # A no marker region has no text to compare so its conflict type decides
    # Table 5.1 puts a whole file deletion on one side under business logic
    # Every other no marker type has no supported label so it is unknown
    name = "NoMarkers"
    priority = 5
    requires = "both"
    precedence_rule = 2

    def detect(self, h: ClassifyInput) -> bool:
        return bool(h.region and h.region.get("no_markers"))

    def resolve(self, h: ClassifyInput) -> DeterministicResult:
        conflict_type = (h.region or {}).get("conflict_type")
        if conflict_type in DELETION_TYPES:
            return DeterministicResult(
                label="logic/business-logic-conflict",
                reason="one side deleted the whole file and the other side modified it",
            )
        return DeterministicResult(
            label="unknown",
            reason=f"region has no text markers and its conflict type is {conflict_type}",
            unknown_reason="no-markers",
        )
