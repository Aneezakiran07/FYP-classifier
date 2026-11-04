# label table for the ast gate verdicts
# owned by Fatima


# The ast gate turns a parser verdict into a label with no model call.
# Values are the seven gate equivalences, labels are the v3 taxonomy labels.
# compute_ast_equivalence returns "identical" only on byte equality, so the
# rule-1 guard is satisfied upstream. Rename is mapped directly to
# structural/rename, without the rule-10 graph check, because v3 has no
# dependency graph and the clarification document says rename fires
# whenever a bijective identifier rename is detected.
GATE_LABELS = {
    "identical": ("mechanical/same-change", "both sides are byte identical"),
    "whitespace_only": ("mechanical/whitespace-only", "parser shows the sides differ in whitespace or layout only"),
    "comments_only": ("structural/documentation", "parser shows only comments differ"),
    "formatting_only": ("structural/formatting", "parser shows formatting differences only"),
    "identifier_rename_only": ("structural/rename", "parser shows one consistent identifier rename"),
}
