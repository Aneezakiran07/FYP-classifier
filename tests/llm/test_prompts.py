# Tests for the llm side, covering prompts, parsing, prompt building, model calling and providers, all with fake replies
# They check the seven tests keep Table 5.1 order, the logic prompt never asks for a label, and broken reply shapes are refused
# They check the base notes, that only the logic prompt gets few shot examples in the real message layout, and that its hash follows them
# They check which errors are retried, permanent rejections, truncated output, temperature zero for each provider and token counting

import json
from types import SimpleNamespace

import pytest

from classifier import report
from classifier.llm import classify_llm, parsing, prompt_builder, prompts, providers, route, run_logic_tests
from classifier.schema import Region, TestAnswer


def raw(obj):
    return json.dumps(obj)


def make_region(path="a.ts", base=None, ours="ours", theirs="theirs"):
    return Region.from_raw(None, 0, {
        "file_path": path, "ours_text": ours, "theirs_text": theirs, "base_text": base,
    })


def logic_reply(met=()):
    return {"tests": [{"test_id": test_id, "met": test_id in met, "evidence": "quoted"}
                      for test_id in prompts.LOGIC_TESTS]}


def test_prompts_file_is_under_120_lines():
    # The limit exists to catch accidental drift, not to enforce a specific size
    # Raise it only when a prompt change is deliberate and reviewed
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


def test_the_seven_tests_follow_table_5_1_order():
    assert prompts.LOGIC_TESTS == (
        "null-safety-conflict", "type-incompatibility", "execution-perturbation",
        "overlap-contamination", "assignment-override", "confluent-interference",
        "business-logic-conflict",
    )


def test_logic_prompt_presents_every_test_in_order():
    headings = [f"{number}. {test_id}\n" for number, test_id in enumerate(prompts.LOGIC_TESTS, 1)]
    positions = [prompts.PROMPT_B.index(heading) for heading in headings]
    assert positions == sorted(positions)


def test_logic_prompt_never_asks_the_model_for_a_label():
    for word in ("subtype", "confidence", "logic/"):
        assert word not in prompts.PROMPT_B


def test_parse_logic_tests_response_returns_seven_answers_in_order():
    answers = parsing.parse_logic_tests_response(raw(logic_reply(met=["assignment-override"])))
    assert [a.test_id for a in answers] == list(prompts.LOGIC_TESTS)
    assert all(isinstance(a, TestAnswer) for a in answers)
    assert [a.test_id for a in answers if a.met] == ["assignment-override"]
    assert answers[0].evidence == "quoted"


def broken_replies():
    # Each case breaks exactly one part of a valid answer
    wrong_order = logic_reply()
    wrong_order["tests"][0], wrong_order["tests"][1] = wrong_order["tests"][1], wrong_order["tests"][0]
    six_tests = logic_reply()
    six_tests["tests"].pop()
    made_up_test = logic_reply()
    made_up_test["tests"][6]["test_id"] = "made-up"
    string_flag = logic_reply()
    string_flag["tests"][0]["met"] = "true"
    no_evidence = logic_reply()
    del no_evidence["tests"][2]["evidence"]
    empty_evidence = logic_reply()
    empty_evidence["tests"][2]["evidence"] = "  "
    old_shape = {"subtype": "assignment-override", "confidence": "high", "evidence": "x"}
    return [wrong_order, six_tests, made_up_test, string_flag, no_evidence, empty_evidence, old_shape]


@pytest.mark.parametrize("reply", broken_replies())
def test_parse_logic_tests_response_refuses_a_broken_shape(reply):
    assert parsing.parse_logic_tests_response(raw(reply)) is None


def test_parse_logic_tests_response_refuses_text_that_is_not_json():
    assert parsing.parse_logic_tests_response("not json") is None


@pytest.mark.parametrize("base,expected", [
    ("const x = 0;", "BASE:\nconst x = 0;"),
    ("", prompt_builder.EMPTY_BASE_NOTE),
    (None, prompt_builder.NO_BASE_NOTE),
])
def test_user_message_describes_the_base(base, expected):
    message = prompt_builder.build_user_message(make_region(base=base))
    assert expected in message
    assert "OURS:\nours" in message and "THEIRS:\ntheirs" in message


def test_base_notes_say_what_the_design_asks_for():
    assert "additions" in prompt_builder.EMPTY_BASE_NOTE
    assert "direction of change is unknown" in prompt_builder.NO_BASE_NOTE


EXAMPLES = [
    {"file_path": "a.ts", "ours": "x = 1", "theirs": "x = 2", "base": "x = 0",
     "true_label": "assignment-override",
     "ast_equivalence": {"equivalence": "content_changed"}, "notes": "both assign x",
     "test_answers": logic_reply(met=["assignment-override"])["tests"]},
    {"file_path": "no_answers.ts", "ours": "y = 1", "theirs": "y = 2",
     "true_label": "assignment-override",
     "ast_equivalence": {"equivalence": "content_changed"}},
    {"file_path": "b.ts", "ours": "a", "theirs": "b",
     "true_label": "rename",
     "ast_equivalence": {"equivalence": "content_changed"}},
]


def test_examples_are_read_from_json_and_shown_only_to_the_logic_prompt(tmp_path):
    path = tmp_path / "shots.json"
    path.write_text(json.dumps(EXAMPLES))
    loaded = prompt_builder.load_few_shot(str(path))
    a = prompt_builder.build_system("A", loaded)
    b = prompt_builder.build_system("B", loaded)
    assert a == prompt_builder.build_system("A", [])
    assert '"test_id": "assignment-override", "met": true' in b
    assert "BASE:\nx = 0" in b
    assert "b.ts" not in b
    assert "<<EXAMPLES>>" not in a + b


@pytest.mark.parametrize("base", ["x = 0", "", None])
def test_an_example_is_laid_out_like_a_real_message(base):
    # The example must show the same base note a real message gets, including for an empty or missing base
    example = dict(EXAMPLES[0], base=base, ast_equivalence={"equivalence": "not_analyzed"})
    real = prompt_builder.build_user_message(make_region(base=base, ours="x = 1", theirs="x = 2"))
    assert real in prompt_builder.build_system("B", [example])


def test_logic_prompt_skips_an_example_with_no_per_test_answers():
    assert "no_answers.ts" not in prompt_builder.build_system("B", EXAMPLES)


def test_missing_example_file_means_no_examples(tmp_path):
    assert prompt_builder.load_few_shot(str(tmp_path / "nope.json")) == []
    assert "<<EXAMPLES>>" not in prompt_builder.build_system("A", [])


def test_shipped_example_file_is_valid_json():
    assert isinstance(prompt_builder.load_few_shot(), list)


@pytest.fixture
def quick(monkeypatch):
    monkeypatch.setattr(classify_llm, "DELAY_BETWEEN_CALLS_SECONDS", 0)
    report.reset_stats()


def test_route_returns_the_kind_and_counts_the_call(monkeypatch, quick):
    monkeypatch.setattr(providers, "call_model",
                        lambda m, s, u: raw({"kind": "structural", "reason": "moved"}))
    assert route(make_region(), None) == {"kind": "structural", "reason": "moved"}
    assert report.STATS["prompt_a"] == 1 and report.STATS["a_structural"] == 1


def test_run_logic_tests_returns_seven_answers(monkeypatch, quick):
    monkeypatch.setattr(providers, "call_model", lambda m, s, u: raw(logic_reply()))
    answers = run_logic_tests(make_region(), None)
    assert len(answers) == 7 and report.STATS["prompt_b"] == 1


def test_both_prompts_receive_the_base(monkeypatch, quick):
    seen = []

    def call(model, system, user):
        seen.append(user)
        return raw({"kind": "semantic", "reason": "r"}) if '"kind"' in system else raw(logic_reply())
    monkeypatch.setattr(providers, "call_model", call)
    region = make_region(base="const base = 1;")
    route(region, None)
    run_logic_tests(region, None)
    assert len(seen) == 2 and all("const base = 1;" in message for message in seen)


def test_bad_shape_is_retried_then_raises(monkeypatch, quick):
    calls = []
    monkeypatch.setattr(providers, "call_model", lambda m, s, u: calls.append(1) or "garbage")
    with pytest.raises(classify_llm.ModelCallFailed, match="invalid shape") as failed:
        route(make_region(), None)
    assert failed.value.code == classify_llm.REASON_INVALID_ANSWER
    # The first answer plus one retry with a stricter reminder
    assert len(calls) == 2


def test_missing_provider_never_retries(monkeypatch, quick):
    calls = []

    def unavailable(*args):
        calls.append(1)
        raise providers.ProviderUnavailable("no key")
    monkeypatch.setattr(providers, "call_model", unavailable)
    with pytest.raises(classify_llm.ModelCallFailed, match="no key") as failed:
        route(make_region(), None)
    assert failed.value.code == classify_llm.REASON_PROVIDER_UNAVAILABLE
    assert len(calls) == 1


def test_the_retry_uses_a_stricter_reminder(monkeypatch, quick):
    systems = []

    def call(model, system, user):
        systems.append(system)
        return "garbage" if len(systems) == 1 else raw({"kind": "semantic", "reason": "r"})
    monkeypatch.setattr(providers, "call_model", call)
    assert route(make_region(), None)["kind"] == "semantic"
    assert classify_llm.RETRY_SUFFIX not in systems[0] and classify_llm.RETRY_SUFFIX in systems[1]


class FakeTransportError(Exception):
    status_code = None


def failing_call(calls, error):
    def call(*args):
        calls.append(1)
        raise error
    return call


def test_a_transport_error_stops_after_the_bounded_attempts(monkeypatch, quick):
    calls = []
    monkeypatch.setattr(providers, "call_model", failing_call(calls, FakeTransportError("sk-secret")))
    monkeypatch.setattr(classify_llm, "MAX_CALL_ATTEMPTS", 3)
    with pytest.raises(classify_llm.ModelCallFailed) as failed:
        route(make_region(), None)
    assert failed.value.code == classify_llm.REASON_TRANSPORT_ERROR
    assert len(calls) == 3
    assert report.STATS["model_calls"] == 0
    # A provider message can echo a key so it never reaches the record
    assert "sk-secret" not in str(failed.value)


def test_a_transport_error_can_recover(monkeypatch, quick):
    calls = []

    def call(*args):
        calls.append(1)
        if len(calls) == 1:
            raise FakeTransportError("busy")
        return raw({"kind": "semantic", "reason": "r"})
    monkeypatch.setattr(providers, "call_model", call)
    assert route(make_region(), None)["kind"] == "semantic"
    assert report.STATS["model_calls"] == 1


@pytest.mark.parametrize("status", [400, 401, 403, 404])
def test_a_permanent_rejection_is_not_retried(monkeypatch, quick, status):
    calls = []
    error = FakeTransportError("sk-secret")
    error.status_code = status
    monkeypatch.setattr(providers, "call_model", failing_call(calls, error))
    with pytest.raises(classify_llm.ModelCallFailed) as failed:
        route(make_region(), None)
    assert failed.value.code == classify_llm.REASON_PROVIDER_REJECTED
    assert len(calls) == 1 and "sk-secret" not in str(failed.value)


def test_a_rate_limit_is_retried(monkeypatch, quick):
    calls = []
    error = FakeTransportError("slow down")
    error.status_code = 429
    monkeypatch.setattr(providers, "call_model", failing_call(calls, error))
    monkeypatch.setattr(classify_llm, "MAX_CALL_ATTEMPTS", 2)
    with pytest.raises(classify_llm.ModelCallFailed):
        route(make_region(), None)
    assert len(calls) == 2


class FakeStatusError(Exception):
    status_code = None


def test_an_unexpected_error_is_not_retried(monkeypatch, quick):
    # An error with no status that is not a network error is a bug or a reply the code did not expect
    calls = []
    monkeypatch.setattr(providers, "call_model", failing_call(calls, KeyError("sk-secret")))
    with pytest.raises(classify_llm.ModelCallFailed) as failed:
        route(make_region(), None)
    assert failed.value.code == classify_llm.REASON_UNEXPECTED_ERROR
    assert len(calls) == 1 and "sk-secret" not in str(failed.value)


@pytest.mark.parametrize("status", [408, 409, 500, 503])
def test_a_server_error_is_retried(monkeypatch, quick, status):
    calls = []
    error = FakeStatusError("busy")
    error.status_code = status
    monkeypatch.setattr(providers, "call_model", failing_call(calls, error))
    monkeypatch.setattr(classify_llm, "MAX_CALL_ATTEMPTS", 2)
    with pytest.raises(classify_llm.ModelCallFailed) as failed:
        route(make_region(), None)
    assert failed.value.code == classify_llm.REASON_TRANSPORT_ERROR and len(calls) == 2


@pytest.mark.parametrize("status", [402, 422])
def test_any_other_client_error_is_not_retried(monkeypatch, quick, status):
    calls = []
    error = FakeStatusError("refused")
    error.status_code = status
    monkeypatch.setattr(providers, "call_model", failing_call(calls, error))
    with pytest.raises(classify_llm.ModelCallFailed) as failed:
        route(make_region(), None)
    assert failed.value.code == classify_llm.REASON_PROVIDER_REJECTED and len(calls) == 1


@pytest.mark.parametrize("error", [ConnectionError("reset"), TimeoutError("slow")])
def test_a_network_error_is_retried(monkeypatch, quick, error):
    calls = []
    monkeypatch.setattr(providers, "call_model", failing_call(calls, error))
    monkeypatch.setattr(classify_llm, "MAX_CALL_ATTEMPTS", 2)
    with pytest.raises(classify_llm.ModelCallFailed) as failed:
        route(make_region(), None)
    assert failed.value.code == classify_llm.REASON_TRANSPORT_ERROR and len(calls) == 2


def test_a_status_in_code_counts_only_when_it_is_a_number():
    # The google sdk keeps the status in code, and the OpenAI sdk keeps text there
    google_style = Exception("x")
    google_style.code = 503
    openai_style = Exception("x")
    openai_style.code = "rate_limit_exceeded"
    assert classify_llm.is_transient(google_style)
    assert classify_llm.error_status(openai_style) is None and not classify_llm.is_transient(openai_style)


def test_truncated_output_is_not_retried_and_counts_as_a_call(monkeypatch, quick):
    calls = []
    monkeypatch.setattr(providers, "call_model", failing_call(calls, providers.TruncatedOutput("cut")))
    with pytest.raises(classify_llm.ModelCallFailed) as failed:
        route(make_region(), None)
    assert failed.value.code == classify_llm.REASON_TRUNCATED_OUTPUT
    assert len(calls) == 1 and report.STATS["model_calls"] == 1


class FakeChat:
    # Stands in for an OpenAI style client and records the request
    def __init__(self, finish_reason):
        self.finish_reason = finish_reason
        self.request = None
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **request):
        self.request = request
        message = SimpleNamespace(content="partial")
        return SimpleNamespace(choices=[SimpleNamespace(finish_reason=self.finish_reason, message=message)])


class FakeAnthropic:
    def __init__(self, stop_reason):
        self.stop_reason = stop_reason
        self.request = None
        self.messages = SimpleNamespace(create=self.create)

    def create(self, **request):
        self.request = request
        block = SimpleNamespace(type="text", text="partial")
        return SimpleNamespace(stop_reason=self.stop_reason, content=[block])


def test_openai_style_call_uses_temperature_zero(monkeypatch):
    client = FakeChat("stop")
    monkeypatch.setitem(providers._CLIENTS, "hackclub", client)
    assert providers.call_model("hackclub-classify", "s", "u") == "partial"
    assert client.request["temperature"] == 0


def test_openai_style_call_refuses_a_truncated_reply(monkeypatch):
    monkeypatch.setitem(providers._CLIENTS, "hackclub", FakeChat("length"))
    with pytest.raises(providers.TruncatedOutput):
        providers.call_model("hackclub-classify", "s", "u")


def test_anthropic_call_uses_temperature_zero_and_refuses_truncation(monkeypatch):
    client = FakeAnthropic("end_turn")
    monkeypatch.setitem(providers._CLIENTS, "anthropic", client)
    assert providers.call_model("claude-haiku-4-5", "s", "u") == "partial"
    assert client.request["temperature"] == 0
    monkeypatch.setitem(providers._CLIENTS, "anthropic", FakeAnthropic("max_tokens"))
    with pytest.raises(providers.TruncatedOutput):
        providers.call_model("claude-haiku-4-5", "s", "u")


def test_gemini_truncation_is_detected():
    finish = SimpleNamespace(name="MAX_TOKENS")
    assert providers.gemini_was_truncated(SimpleNamespace(candidates=[SimpleNamespace(finish_reason=finish)]))
    assert not providers.gemini_was_truncated(SimpleNamespace(candidates=None))


def test_only_the_logic_prompt_hash_changes_with_few_shot_examples(tmp_path, monkeypatch):
    empty = tmp_path / "empty.json"
    empty.write_text("[]")
    monkeypatch.setattr(prompt_builder.load_few_shot, "__defaults__", (str(empty),))
    router, logic = prompt_builder.system_prompt_hash("A"), prompt_builder.system_prompt_hash("B")
    assert router == prompt_builder.system_prompt_hash("A") and len(router) == 64
    assert logic == prompt_builder.system_prompt_hash("B") and len(logic) == 64
    full = tmp_path / "full.json"
    full.write_text(json.dumps(EXAMPLES[:1]))
    monkeypatch.setattr(prompt_builder.load_few_shot, "__defaults__", (str(full),))
    assert prompt_builder.system_prompt_hash("A") == router
    assert prompt_builder.system_prompt_hash("B") != logic


def test_logic_prompt_change_leaves_the_router_hash_alone(monkeypatch):
    router, logic = prompt_builder.system_prompt_hash("A"), prompt_builder.system_prompt_hash("B")
    monkeypatch.setattr(prompt_builder, "PROMPT_B", "changed")
    assert prompt_builder.system_prompt_hash("A") == router
    assert prompt_builder.system_prompt_hash("B") != logic


def test_provider_usage_is_counted_and_a_missing_usage_is_fine(monkeypatch):
    providers.USAGE.clear()
    monkeypatch.setitem(providers._CLIENTS, "hackclub", FakeChat("stop"))
    providers.call_model("hackclub-classify", "s", "u")
    assert providers.USAGE["input"] == 0
    providers.count_usage(SimpleNamespace(prompt_tokens=7, completion_tokens=3), "prompt_tokens", "completion_tokens")
    assert (providers.USAGE["input"], providers.USAGE["output"]) == (7, 3)
    providers.USAGE.clear()
