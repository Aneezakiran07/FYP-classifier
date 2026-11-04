from .base import ClassifyInput, DeterministicResult, PatternPlugin


class SameChange(PatternPlugin):
    # Taxonomy rule 1: byte identical text is mechanical/same-change,
    # whatever the content or file type. Outer whitespace differences are
    # NOT this label, rule 3 claims them, so detect() does not strip.
    # Empty sides are still excluded so that regions with no text fall
    # through to WhitespaceOnly and then to the model, matching v2.
    name = "SameChange"
    priority = 10
    requires = "both"
    precedence_rule = 1

    def detect(self, h: ClassifyInput) -> bool:
        return h.ours_text != "" and h.ours_text == h.theirs_text

    def resolve(self, h: ClassifyInput) -> DeterministicResult:
        return DeterministicResult(
            label="mechanical/same-change",
            reason="both sides are byte identical",
        )