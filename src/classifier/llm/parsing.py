# turns raw model replies into plain dictionaries
# owned by Aneeza

import json

from classifier.llm.prompts import SUBTYPES


# SUBTYPES now holds v3 logic/* labels. "other" is still allowed as the
# model's escape hatch. classify_with_llm maps both "other" and a low
# confidence answer to unknown with the raw answer preserved, following
# taxonomy rule 15 (business-logic-conflict is the residual, only after
# the other six tests fail).
VALID_LOGIC_SUBTYPES = set(SUBTYPES) | {"other"}

def clean_optional_text(value):
    # The model sometimes returns the string null or an empty string
    # instead of a real null, this turns those into None and keeps real text
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    if not stripped or stripped.lower() == "null":
        return None
    return stripped

def load_json_object(raw_text):
    # Pull a json object out of a model reply, some models add fences anyway
    text = (raw_text or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None

def parse_kind_response(raw_text):
    # Prompt A answer, kind and a required reason
    parsed = load_json_object(raw_text)
    if parsed is None or parsed.get("kind") not in ("structural", "semantic", "unknown"):
        return None
    reason = parsed.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        return None
    return {"kind": parsed["kind"], "reason": reason.strip()}

def parse_subtype_response(raw_text):
    # Prompt B answer, a null subtype is allowed and is treated as other later
    parsed = load_json_object(raw_text)
    if parsed is None or "subtype" not in parsed:
        return None
    subtype = clean_optional_text(parsed.get("subtype"))
    if subtype is not None and subtype not in VALID_LOGIC_SUBTYPES:
        return None
    confidence = parsed.get("confidence")
    if confidence not in ("high", "medium", "low"):
        return None
    return {
        "subtype": subtype,
        "confidence": confidence,
        "evidence": clean_optional_text(parsed.get("evidence")),
    }
