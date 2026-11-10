# Deterministic checks that confirm what the model claimed about a region before a logic label is written
# evidence_is_real requires every quoted piece of the evidence to appear in ours, theirs or base, and a quote may hold a template string
# CHECKS holds one cheap text check per logic test, and assignment override reads names with values, return types and JSX children
# validate_logic_test needs both checks to pass, confluent interference always fails, and confirm_structural is not built yet so it returns None

# deterministic checks that confirm what the model said about a region
# owned by Fatima

import re

QUOTED = re.compile(r"`([^`]+)`")
DOUBLE_QUOTED = re.compile(r'"([^"]{3,})"')
SIDE_LABEL = re.compile(r"^(?:OURS|THEIRS|BASE)\s*:\s*", re.IGNORECASE)
AST_KIND = re.compile(r"^[a-z_]+_(?:added|removed|replaced|changed)(?::|$)")

NULL_MARKER = re.compile(r"\bnull\b|\bundefined\b|\?\.|\?\?|!\.")
CONTROL_WORD = re.compile(
    r"\b(?:return|throw|break|continue|yield|if|else|switch|for|while|try|catch)\b"
)
LINE_COMMENT = re.compile(r"//.*$")
SIGNATURE_LINE = re.compile(r"\bfunction\b|=>|\binterface\b|\btype\s+[\w$]+\s*[<=]|\)\s*:\s*[\w$]")
ASSIGNMENT = re.compile(r"([A-Za-z_$][\w$.]*)\s*(?::|=(?![=>]))\s*([^;\n]+)")
RETURN_TYPE = re.compile(
    r"([A-Za-z_$][\w$]*)\s*(?:=\s*(?:async\s*)?)?\([^()]*\)\s*:\s*(.+?)\s*(?:\{|=>)?\s*$"
)
# characters that put a brace in code position, so the brace is not a JSX child
NOT_JSX_CHILD_BEFORE = set("=(),:[?&|+-*/!")
JSX_FILES = (".tsx", ".jsx")
# words that open a code block or a declaration, so a brace after them or on their line is code
CODE_WORDS = {
    "if", "else", "for", "while", "do", "switch", "try", "catch", "finally", "return", "yield",
    "class", "interface", "type", "enum", "namespace", "module", "function", "const", "let", "var",
    "import", "export", "default", "async", "await", "case", "throw", "new",
}
LAST_WORD = re.compile(r"([A-Za-z_$][\w$]*)$")
FIRST_WORD = re.compile(r"^\s*([A-Za-z_$][\w$]*)")
IDENTIFIER = re.compile(r"[A-Za-z_$][\w$]{2,}")

# words that appear in almost every region so sharing them proves nothing
COMMON_WORDS = {
    "const", "let", "var", "function", "return", "class", "import", "export", "from",
    "default", "new", "this", "true", "false", "null", "undefined", "else", "for",
    "while", "async", "await", "type", "interface",
}


def squeeze(text):
    # Removes all whitespace so layout differences do not matter
    return "".join((text or "").split())


def quoted_pieces(evidence):
    # Backticks first, and double quotes only when there are no backticks
    found = [SIDE_LABEL.sub("", piece).strip() for piece in QUOTED.findall(evidence or "")]
    if not found:
        found = [piece.strip() for piece in DOUBLE_QUOTED.findall(evidence or "")]
    return [piece for piece in found if piece]


def clean_piece(raw):
    return SIDE_LABEL.sub("", raw).strip()


def longest_real_close(evidence, ticks, start, region):
    # A quote may hold a template string, so it ends at the last backtick that still gives real code
    best = None
    for close in ticks:
        if close <= start:
            continue
        piece = clean_piece(evidence[start + 1:close])
        if piece and piece_is_real(piece, region):
            best = close
    return best


def backtick_quotes_are_real(region, evidence):
    # Reads backtick quotes one by one and fails as soon as one quote is not in the region
    ticks = [i for i, char in enumerate(evidence) if char == "`"]
    found_one = False
    position = 0
    while position < len(ticks) - 1:
        start = ticks[position]
        close = longest_real_close(evidence, ticks, start, region)
        if close is None:
            if clean_piece(evidence[start + 1:ticks[position + 1]]):
                return False
            position += 1
            continue
        found_one = True
        position = ticks.index(close) + 1
    return found_one


def piece_is_real(piece, region):
    # An AST change name comes from the parser summary, so it is not in the region text
    if AST_KIND.match(piece):
        return True
    target = squeeze(piece)
    for text in (region.ours_text, region.theirs_text, region.base_text):
        if target in squeeze(text):
            return True
    return False


def evidence_is_real(region, evidence):
    # Check one, at least one quoted piece and every piece must appear in the region
    # Backtick quotes are read with template strings in mind, double quotes only when there are no backticks
    if "`" in (evidence or ""):
        return backtick_quotes_are_real(region, evidence)
    pieces = quoted_pieces(evidence)
    if not pieces:
        return False
    return all(piece_is_real(piece, region) for piece in pieces)


def check_null_safety(region):
    ours = len(NULL_MARKER.findall(region.ours_text or ""))
    theirs = len(NULL_MARKER.findall(region.theirs_text or ""))
    return ours != theirs


def signature_lines(text):
    # The pattern is searched on the real line, only the stored copy loses its spaces
    found = set()
    for line in (text or "").splitlines():
        if line.strip() and SIGNATURE_LINE.search(line):
            found.add(squeeze(line))
    return found


def check_type_incompatibility(region):
    return signature_lines(region.ours_text) != signature_lines(region.theirs_text)


def control_lines(text):
    # The lines that hold a control flow word, in order, with comments and layout removed
    lines = []
    for line in (text or "").splitlines():
        code = LINE_COMMENT.sub("", line)
        if CONTROL_WORD.search(code):
            lines.append(squeeze(code))
    return lines


def check_execution_perturbation(region):
    return control_lines(region.ours_text) != control_lines(region.theirs_text)


def changed_lines(side, base):
    base_lines = {squeeze(line) for line in (base or "").splitlines()}
    lines = (line for line in (side or "").splitlines() if squeeze(line))
    return [line for line in lines if squeeze(line) not in base_lines]


def identifiers_in(lines):
    names = set()
    for line in lines:
        names.update(IDENTIFIER.findall(line))
    return names - COMMON_WORDS


def check_overlap_contamination(region):
    # Both sides changed something and the changed lines share a name
    ours = changed_lines(region.ours_text, region.base_text)
    theirs = changed_lines(region.theirs_text, region.base_text)
    if not ours or not theirs:
        return False
    return bool(identifiers_in(ours) & identifiers_in(theirs))


def assignments(text):
    found = {}
    for name, value in ASSIGNMENT.findall(text or ""):
        found.setdefault(name, set()).add(squeeze(value))
    return found


def return_types(text):
    # Maps each function name to its return type annotation
    found = {}
    for line in (text or "").splitlines():
        match = RETURN_TYPE.search(line)
        if match:
            found.setdefault(match.group(1), set()).add(squeeze(match.group(2)))
    return found


def jsx_child_slots(text):
    # Each line with a brace expression in child position becomes its text with empty braces and the expressions
    slots = {}
    for line in (text or "").splitlines():
        first = FIRST_WORD.match(line)
        if first and first.group(1) in CODE_WORDS:
            continue
        shape, children = split_jsx_children(line)
        if children:
            slots.setdefault(squeeze(shape), set()).add(tuple(children))
    return slots


def split_jsx_children(line):
    # Walks the line and lifts out every balanced top level brace that is not in code position
    shape, children, depth, start = [], [], 0, None
    for index, char in enumerate(line):
        if depth == 0 and char == "{" and is_child_brace(line, index):
            depth, start = 1, index
            continue
        if depth:
            depth += {"{": 1, "}": -1}.get(char, 0)
            if depth == 0:
                children.append(squeeze(line[start + 1:index]))
                shape.append("{}")
            continue
        shape.append(char)
    if depth:
        return line, []
    return "".join(shape), children


def is_child_brace(line, index):
    before = line[:index].rstrip()
    if not before:
        return True
    if before[-1] in NOT_JSX_CHILD_BEFORE or before.endswith("=>"):
        return False
    last = LAST_WORD.search(before)
    return not (last and last.group(1) in CODE_WORDS)


def same_target_differs(ours, theirs):
    return any(ours[name] != theirs[name] for name in ours if name in theirs)


def target_readers(region):
    # A JSX child can only be a target in a JSX file
    readers = [assignments, return_types]
    if (region.file_path or "").endswith(JSX_FILES):
        readers.append(jsx_child_slots)
    return readers


def check_assignment_override(region):
    # The same target gets different values on the two sides
    # A target is a name with a value, a function return type, or a JSX child in the same text slot
    for read in target_readers(region):
        if same_target_differs(read(region.ours_text), read(region.theirs_text)):
            return True
    return False


def check_confluent_interference(region):
    # There are no context lines so a joint use can never be shown
    return False


def check_business_logic(region):
    return squeeze(region.ours_text) != squeeze(region.theirs_text)


CHECKS = {
    "null-safety-conflict": check_null_safety,
    "type-incompatibility": check_type_incompatibility,
    "execution-perturbation": check_execution_perturbation,
    "overlap-contamination": check_overlap_contamination,
    "assignment-override": check_assignment_override,
    "confluent-interference": check_confluent_interference,
    "business-logic-conflict": check_business_logic,
}


def validate_logic_test(region, test_id, evidence):
    # The evidence must be real and the test specific check must pass
    check = CHECKS.get(test_id)
    if check is None:
        return False
    return evidence_is_real(region, evidence) and check(region)


def confirm_structural(region, ast_verdict):
    # Not built yet, so a structural hint never gets a label and the region stays unknown
    return None