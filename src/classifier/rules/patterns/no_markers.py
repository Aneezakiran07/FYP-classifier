from .base import ClassifyInput, DeterministicResult, PatternPlugin

        #github put ours theirs marker ,and if we delete that file, there is gen1 no markers
        # so , in our input file, its given k In your AgenticFlict data, this shows up as a region with "no_markers": true 
        # in the JSON. There's no ours_text or theirs_text to compare — one side is empty.
       #if the region has no markers, label it mechanical/one-side-change and skip everything else.

class NoMarkers(PatternPlugin):
    # A region with no text markers means one side deleted the file, so
    # there is no text to compare and the label is fixed. This is the
    # deletion half of taxonomy rule 2, one side is unchanged from the
    # original and the other side deleted it.
    name = "NoMarkers"
    priority = 5
    requires = "both"
    precedence_rule = 2

    def detect(self, h: ClassifyInput) -> bool:
        return bool(h.region and h.region.get("no_markers"))

    def resolve(self, h: ClassifyInput) -> DeterministicResult:
        return DeterministicResult(
            label="mechanical/one-side-change",
            reason="region has no text markers, one side deleted the file",
        )

