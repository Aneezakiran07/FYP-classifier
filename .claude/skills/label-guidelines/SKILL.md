---
name: label-guidelines
description: Definitions and tie break rules for the 23 conflict labels, used for hand labeling and few shot examples. Use when labeling regions or writing label examples.
---

Use the label table in docs/classifier_design_from_report.md section 5.2.
Label with exactly one label per region.
Apply the stage order when two labels fit: scope, identity, shape, boundary, then logic.
Use unknown with a reason when no single label is supported by the region text.
Confluent-interference is recorded as unknown while context lines are unavailable.
Record a one line reason for every hand label so it can be reused as a few shot note.
Add tie break decisions below as the team agrees on them.

## Agreed tie breaks
- Same change plus extra (D12). Both sides changed from base and one side's result is the other side's result plus something extra. No label fits, so label it unknown with the reason "same change plus extra, no label defined".
- Value-only-change is broadened (D12). It now means only a literal's text differs and nothing else in the region differs, so UI and log text count, not only infrastructure values. If the text is used in a condition or code compares against it, use the logic labels instead. If anything else differs too, such as an added line, it is not value-only-change.
