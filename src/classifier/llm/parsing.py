# turns raw model replies into plain values
# owned by Aneeza

import json

from classifier.llm.prompts import LOGIC_TESTS
from classifier.schema import TestAnswer


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
    # Router answer, kind and a required reason
    parsed = load_json_object(raw_text)
    if parsed is None or parsed.get("kind") not in ("structural", "semantic", "unknown"):
        return None
    reason = parsed.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        return None
    return {"kind": parsed["kind"], "reason": reason.strip()}


def parse_test_answer(item, expected_id):
    # One test answer must name the expected test and carry a flag and evidence
    if not isinstance(item, dict) or item.get("test_id") != expected_id:
        return None
    met, evidence = item.get("met"), item.get("evidence")
    if not isinstance(met, bool) or not isinstance(evidence, str) or not evidence.strip():
        return None
    return TestAnswer(expected_id, met, evidence.strip())


def parse_logic_tests_response(raw_text):
    # Logic answer, all seven tests in the fixed order or the shape is invalid
    parsed = load_json_object(raw_text)
    items = parsed.get("tests") if parsed else None
    if not isinstance(items, list) or len(items) != len(LOGIC_TESTS):
        return None
    answers = [parse_test_answer(item, test_id) for item, test_id in zip(items, LOGIC_TESTS)]
    return None if None in answers else answers
