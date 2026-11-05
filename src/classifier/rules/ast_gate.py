# label table for the ast gate verdicts
# owned by Fatima

import re

from .patterns.comments_only import DIRECTIVE_PATTERN
from .patterns.whitespace_only import _asi_sensitive_count


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


# A parameter list of a function or an arrow function, a call has neither shape
PARAMETER_LIST = re.compile(r"\bfunction\b[^(]*\(([^()]*)\)|\(([^()]*)\)\s*(?::[^=>{]+)?=>")


def parameter_names(text):
    names = set()
    for match in PARAMETER_LIST.finditer(text or ""):
        for part in (match.group(1) or match.group(2) or "").split(","):
            found = re.match(r"\s*(?:\.\.\.)?([A-Za-z_$][\w$]*)", part)
            if found:
                names.add(found.group(1))
    return names


def is_declared_in_region(name, text):
    # Looks for a local declaration or a parameter of this name
    escaped = re.escape(name)
    keyword = rf"\b(?:const|let|var|function|class|type|interface|enum)\s+{escaped}(?![\w$])"
    single_arrow = rf"(?<![\w$.]){escaped}\s*=>"
    if re.search(keyword, text or "") or re.search(single_arrow, text or ""):
        return True
    return name in parameter_names(text)


def is_local_rename(eq, ours_text):
    # The report says renamed local identifiers, so every old name must be declared here
    # Swapping a called function or a property has the same token shape but changes behavior
    return all(is_declared_in_region(old_name, ours_text) for old_name in eq.renames)


def directive_lines(text):
    # Keeps the whole line so a change in the rule named by a directive still counts
    return [line.strip() for line in (text or "").splitlines() if DIRECTIVE_PATTERN.search(line)]


def passes_guards(ours_text, theirs_text):
    # A newline after these keywords or a changed directive can change behavior
    if _asi_sensitive_count(ours_text) != _asi_sensitive_count(theirs_text):
        return False
    return directive_lines(ours_text) == directive_lines(theirs_text)


def apply_guards(eq, ours_text, theirs_text):
    # A verdict that fails a guard is treated as content changed
    # A file with no parser only compared text so its verdict is not analyzed
    if eq.equivalence not in GATE_LABELS or eq.equivalence == "identical":
        return eq
    if eq.parse_error == "no_parser_available":
        eq.equivalence = "not_analyzed"
    elif not passes_guards(ours_text, theirs_text):
        eq.equivalence = "content_changed"
    elif eq.equivalence == "identifier_rename_only" and not is_local_rename(eq, ours_text):
        eq.equivalence = "content_changed"
    return eq
