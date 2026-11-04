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
(empty for now)
