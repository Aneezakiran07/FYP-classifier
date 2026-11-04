---
name: report-check
description: Compare the classifier code against the FYP report design and list mismatches. Use when asked whether the code matches the report, or before writing Chapter 7 or 9.
---

Read docs/classifier_design_from_report.md.
For each stage 0 to 5, find the matching code and list what is missing, extra or different.
Check the 23 labels against schema.py.
Check that the classifier block has every field the report lists: label, status, stage, source, base state, trace, confirming test, changed names, joint use lines, provenance.
Check capped and llm-error are statuses with no label.
Check the model never assigns a label itself and the first met logic test wins.
Output a table with columns: item, report says, code does, action.
Do not edit any code.
