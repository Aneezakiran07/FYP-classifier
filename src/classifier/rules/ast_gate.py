# Turns a passing AST verdict into a label with no model call, as part of Stage 2
# GATE_LABELS maps the identical, whitespace, comments, formatting and rename verdicts to their labels and reasons
# apply_guards marks a verdict as content changed when line ending keywords or directive comments differ, and marks files with no parser as not analyzed
# is_local_rename, is_declared_in_region and is_named_export accept a rename only when every old name is declared locally and not exported

# label table for the ast gate verdicts
# owned by Fatima

import re

from .patterns.comments_only import DIRECTIVE_PATTERN
from .patterns.whitespace_only import _asi_sensitive_count


# The ast gate turns a parser verdict into a label with no model call
# Values are the seven gate equivalences, labels are the taxonomy labels
# A rename counts only when every old name is declared inside the region
# and none of the old names is a named export, see the rename guard below
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


def declaration_patterns(name):
    # The ways a name can be declared inside a region
    escaped = re.escape(name)
    word = rf"(?<![\w$]){escaped}(?![\w$])"
    return [
        rf"\b(?:const|let|var|function|class|interface|enum)\s+{escaped}(?![\w$])",
        # A type alias has a type parameter list or an equals sign after the name
        # A bare type before a name is an import or export specifier
        rf"\btype\s+{escaped}\s*[<=]",
        rf"(?<![\w$.]){escaped}\s*=>",
        # Array destructuring is by position so a new name is a real local rename
        # Object destructuring is left out because the name picks which property is read
        rf"\b(?:const|let|var)\s*\[[^\]]*{word}",
        rf"\bcatch\s*\(\s*{escaped}(?![\w$])",
    ]


def is_declared_in_region(name, text):
    # Looks for a local declaration or a parameter of this name
    for pattern in declaration_patterns(name):
        if re.search(pattern, text or ""):
            return True
    return name in parameter_names(text)


def is_named_export(name, text):
    # A default export is not matched because importers choose their own name for it
    escaped = re.escape(name)
    declared = rf"\bexport\s+(?:declare\s+|abstract\s+|async\s+)*(?:const|let|var|function|class|type|interface|enum)\s+{escaped}(?![\w$])"
    listed = rf"\bexport\s*\{{[^}}]*(?<![\w$]){escaped}(?![\w$])"
    return bool(re.search(declared, text or "") or re.search(listed, text or ""))


def is_local_rename(eq, ours_text):
    # The report says renamed local identifiers, so every old name must be declared here
    # A named export is not local because other files import it
    for old_name in eq.renames:
        if is_named_export(old_name, ours_text):
            return False
        if not is_declared_in_region(old_name, ours_text):
            return False
    return True


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
