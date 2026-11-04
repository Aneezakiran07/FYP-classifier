import json
import os

from classifier import report
from classifier.llm import classify_llm, parsing, prompt_builder, prompts, providers


def raw(obj):
    return json.dumps(obj)


def test_prompts_file_is_under_120_lines():
    # The v3 prompt carries the full ordered logic test list, so it is
    # longer than v2. The limit exists to catch accidental drift, not to
    # enforce a specific size. Raise it only when a prompt change is
    # deliberate and has been reviewed against the taxonomy.
    with open(prompts.__file__, "r", encoding="utf-8") as f:
        assert len(f.read().splitlines()) < 120


def test_parse_kind_response():
    ok = parsing.parse_kind_response(raw({"kind": "semantic", "reason": "condition changed"}))
    assert ok == {"kind": "semantic", "reason": "condition changed"}
    fenced = "```json\n" + raw({"kind": "structural", "reason": "moved"}) + "\n```"
    assert parsing.parse_kind_response(fenced)["kind"] == "structural"
    assert parsing.parse_kind_response("not json") is None
    assert parsing.parse_kind_response(raw({"kind": "logic", "reason": "x"})) is None
    assert parsing.parse_kind_response(raw({"kind": "semantic"})) is None


def test_parse_subtype_response():
    ok = parsing.parse_subtype_response(
        raw({"subtype": "logic/assignment-override", "confidence": "high", "evidence": "x = 1"})
    )
    assert ok["subtype"] == "logic/assignment-override"
    assert parsing.parse_subtype_response(
        raw({"subtype": None, "confidence": "low", "evidence": None})
    )["subtype"] is None
    assert parsing.parse_subtype_response(raw({"subtype": "made_up", "confidence": "high"})) is None
    # v2 bare names are no longer valid
    assert parsing.parse_subtype_response(
        raw({"subtype": "assignment_override", "confidence": "high"})
    ) is None
    assert parsing.parse_subtype_response(raw({"subtype": "other", "confidence": "sure"})) is None


EXAMPLES = [
    {"file_path": "a.ts", "ours": "x = 1", "theirs": "x = 2",
     "true_label": "logic/assignment-override",
     "ast_equivalence": {"equivalence": "content_changed"}, "notes": "both assign x"},
    {"file_path": "b.ts", "ours": "a", "theirs": "b",
     "true_label": "structural/rename",
     "ast_equivalence": {"equivalence": "content_changed"}},
]


def test_examples_are_read_from_json_and_split_by_prompt(tmp_path):
    path = tmp_path / "shots.json"
    path.write_text(json.dumps(EXAMPLES))
    loaded = prompt_builder.load_few_shot(str(path))
    a = prompt_builder.build_system("A", loaded)
    b = prompt_builder.build_system("B", loaded)
    assert '"kind": "semantic"' in a and '"kind": "structural"' in a
    assert '"subtype": "logic/assignment-override"' in b
    assert "b.ts" not in b
    assert "<<EXAMPLES>>" not in a + b


def test_missing_example_file_means_no_examples(tmp_path):
    assert prompt_builder.load_few_shot(str(tmp_path / "nope.json")) == []
    assert "<<EXAMPLES>>" not in prompt_builder.build_system("A", [])


def test_shipped_example_file_is_valid_json():
    assert isinstance(prompt_builder.load_few_shot(), list)


def fake_model(answers):
    # Answers prompt A and B from a table keyed by the file path in the user message
    def call(model, system, user):
        which = "A" if '"kind"' in system else "B"
        for path, pair in answers.items():
            if path in user:
                return raw(pair[which])
        raise AssertionError("unexpected region")
    return call


def test_model_flow_on_sample_regions(monkeypatch):
    # After the escape-hatch fix in classify.py, an answer of "other" or a
    # low-confidence answer is reported as unknown with the model's guess
    # in candidate_labels, instead of being silently relabeled as the
    # residual business-logic-conflict class.
    answers = {
        "sem_ok.ts": {"A": {"kind": "semantic", "reason": "value differs"},
                      "B": {"subtype": "logic/assignment-override", "confidence": "high",
                            "evidence": "x = 1"}},
        "sem_other.ts": {"A": {"kind": "semantic", "reason": "value differs"},
                         "B": {"subtype": "other", "confidence": "medium", "evidence": "y"}},
        "sem_low.ts": {"A": {"kind": "semantic", "reason": "value differs"},
                       "B": {"subtype": "logic/overlap-contamination", "confidence": "low",
                             "evidence": "z"}},
        "struct.ts": {"A": {"kind": "structural", "reason": "moved"}},
        "unsure.ts": {"A": {"kind": "unknown", "reason": "missing context"}},
    }
    monkeypatch.setattr(providers, "call_model", fake_model(answers))
    monkeypatch.setattr(classify_llm, "DELAY_BETWEEN_CALLS_SECONDS", 0)
    report.reset_stats()

    def run(path):
        return classify_llm.classify_with_llm(path, "ours", "theirs", None, None)

    ok = run("sem_ok.ts")
    assert ok["label"] == "logic/assignment-override"
    assert not ok.get("needs_verification")

    # "other" from the model becomes unknown, with the raw answer preserved
    other = run("sem_other.ts")
    assert other["label"] == "unknown"
    assert other["needs_verification"]
    assert other.get("unknown_reason") == "ambiguous"
    assert other.get("candidate_labels") == ["other"]

    # low confidence on a real subtype becomes unknown with that subtype kept
    low = run("sem_low.ts")
    assert low["label"] == "unknown"
    assert low["needs_verification"]
    assert low.get("unknown_reason") == "ambiguous"
    assert low.get("candidate_labels") == ["logic/overlap-contamination"]

    # structural from A still becomes unknown with the two structural candidates
    struct = run("struct.ts")
    assert struct["label"] == "unknown"
    assert struct["needs_verification"]
    assert struct["unknown_reason"] == "ambiguous"
    assert struct["candidate_labels"] is not None

    # explicit unknown from A passes through
    unsure = run("unsure.ts")
    assert unsure["label"] == "unknown" and unsure["needs_verification"]
    assert report.STATS["prompt_a"] == 5 and report.STATS["prompt_b"] == 3
    assert report.STATS["a_structural"] == 1


def test_bad_shape_is_retried_then_marked_unknown(monkeypatch):
    calls = []
    monkeypatch.setattr(providers, "call_model",
                        lambda m, s, u: calls.append(1) or "garbage")
    monkeypatch.setattr(classify_llm, "DELAY_BETWEEN_CALLS_SECONDS", 0)
    report.reset_stats()
    result = classify_llm.classify_with_llm("a.ts", "x", "y", None, None)
    assert len(calls) == classify_llm.MAX_FORMAT_ATTEMPTS
    assert result["label"] == "unknown" and result["needs_verification"]


def test_missing_provider_never_retries(monkeypatch):
    def unavailable(*args):
        raise providers.ProviderUnavailable("no key")
    monkeypatch.setattr(providers, "call_model", unavailable)
    report.reset_stats()
    result = classify_llm.classify_with_llm("a.ts", "x", "y", None, None)
    assert result["label"] == "unknown" and "no key" in result["reason"]