# Deterministic checks that confirm what the model claimed about a region before a logic label is written
# evidence_is_real requires every quoted piece of the evidence to appear in ours, theirs or base, or to be an AST change name
# CHECKS holds one cheap text check per logic test, such as null markers, signature lines, control flow lines, shared names or competing assignments
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


def check_assignment_override(region):
    # The same target gets different values on the two sides
    ours = assignments(region.ours_text)
    theirs = assignments(region.theirs_text)
    return any(ours[name] != theirs[name] for name in ours if name in theirs)


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