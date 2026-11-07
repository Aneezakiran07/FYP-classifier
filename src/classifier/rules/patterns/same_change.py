# Stage 1 pattern that labels a region same-change when both sides are byte identical
# The text is compared exactly with no stripping, so outer whitespace differences do not count
# Empty sides are excluded so regions with no text move on to later stages
# It returns a high confidence result with the reason that both sides are byte identical

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