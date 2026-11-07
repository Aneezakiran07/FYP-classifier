# Sends Stage 4 questions to the model and returns parsed answers, the model never picks a label
# route runs the router prompt A and run_logic_tests runs the seven logic tests prompt B
# ask_model retries a badly shaped reply once with a stricter reminder, and call_with_retry retries only network errors, rate limits and server errors
# Failures raise ModelCallFailed with a reason code such as transport-error, provider-rejected or unexpected-error, and every reply is counted in STATS

# model calling for stage 4
# owned by Aneeza
# the model only answers questions here and the pipeline turns answers into labels
# the run settings below are set by cli.py and read by the functions in this module

import os
import time

from classifier.llm import prompt_builder, providers
from classifier.llm.parsing import parse_kind_response, parse_logic_tests_response
from classifier.report import STATS


# The default is the classify alias named in CLAUDE.md, an env var or the model flag overrides it
DEFAULT_MODEL_NAME = os.environ.get(
    "CLASSIFIER_MODEL", os.environ.get("GEMINI_MODEL", "hackclub-classify")
)

# These are set from the command line once the script starts, the functions
# below read them instead of fixed constants
MODEL_NAME = DEFAULT_MODEL_NAME
DEFAULT_DELAY_BETWEEN_CALLS_SECONDS = 4
DELAY_BETWEEN_CALLS_SECONDS = DEFAULT_DELAY_BETWEEN_CALLS_SECONDS

# A failing request is sent at most this many times with backoff in between
DEFAULT_MAX_CALL_ATTEMPTS = 5
MAX_CALL_ATTEMPTS = DEFAULT_MAX_CALL_ATTEMPTS

# A reply in the wrong shape is asked for once more with a stricter reminder
MAX_FORMAT_ATTEMPTS = 2

# The reason codes of the llm-error status
REASON_PROVIDER_UNAVAILABLE = "provider-unavailable"
REASON_PROVIDER_REJECTED = "provider-rejected"
REASON_TRANSPORT_ERROR = "transport-error"
REASON_INVALID_ANSWER = "invalid-answer"
REASON_TRUNCATED_OUTPUT = "truncated-output"
REASON_UNEXPECTED_ERROR = "unexpected-error"

# Status codes that can pass on their own, every 5xx code counts too
# These are the same codes the OpenAI and Anthropic sdks retry
TRANSIENT_STATUS_CODES = (408, 409, 429)

# Words in the class names of network errors across the provider sdks and httpx
TRANSIENT_ERROR_WORDS = ("Timeout", "Connection", "Network", "Transport")

# A cap on the backoff wait so it does not grow forever on a stuck request
MAX_BACKOFF_SECONDS = 120

RETRY_SUFFIX = "\n\nYour previous response was not valid. Reply with ONLY the JSON object described above."


class ModelCallFailed(Exception):
    # Carries a reason code for the record and a short detail for the trace
    def __init__(self, code, detail):
        super().__init__(detail)
        self.code = code


def error_status(error):
    # Most sdks keep the http status in status_code and the google sdk keeps it in code
    # The OpenAI sdk also has a code field that holds text, so only a number counts
    for name in ("status_code", "code"):
        value = getattr(error, name, None)
        if isinstance(value, int):
            return value
    return None


def is_transient(error):
    # Only a network problem, a rate limit or a server error can pass by sending the same request again
    status = error_status(error)
    if status is not None:
        return status in TRANSIENT_STATUS_CODES or 500 <= status <= 599
    names = [cls.__name__ for cls in type(error).__mro__]
    return any(word in name for name in names for word in TRANSIENT_ERROR_WORDS)


def describe_error(error):
    # Names the error without its message because a provider message can echo a key
    status = error_status(error)
    return type(error).__name__ if status is None else f"{type(error).__name__} status {status}"


def call_with_retry(system_instruction, user_message):
    # One request to the current model, only an error that can pass on its own is retried
    # An error with a status is the provider refusing, and an error with none is a bug or a reply the code did not expect
    # Only requests that got a reply count toward the call ceiling of the file
    attempt = 0
    while True:
        try:
            reply = providers.call_model(MODEL_NAME, system_instruction, user_message)
            STATS["model_calls"] += 1
            return reply
        except providers.ProviderUnavailable as e:
            raise ModelCallFailed(REASON_PROVIDER_UNAVAILABLE, str(e))
        except providers.TruncatedOutput as e:
            STATS["model_calls"] += 1
            raise ModelCallFailed(REASON_TRUNCATED_OUTPUT, str(e))
        except Exception as e:
            described = describe_error(e)
            if not is_transient(e):
                code = REASON_PROVIDER_REJECTED if error_status(e) is not None else REASON_UNEXPECTED_ERROR
                raise ModelCallFailed(code, described)
            attempt += 1
            if attempt >= MAX_CALL_ATTEMPTS:
                raise ModelCallFailed(REASON_TRANSPORT_ERROR, f"gave up after {attempt} attempts, {described}")
            wait_seconds = min(
                DELAY_BETWEEN_CALLS_SECONDS * (2 ** (attempt - 1)), MAX_BACKOFF_SECONDS
            )
            print(f"  Request failed, trying again. Error: {described}")
            print(f"  Waiting {wait_seconds} seconds before retry")
            time.sleep(wait_seconds)


def ask_model(system_instruction, user_message, parser, prompt_name):
    # One prompt round trip, a bad shape is retried with a stricter reminder
    for format_attempt in range(MAX_FORMAT_ATTEMPTS):
        instruction = system_instruction if format_attempt == 0 else system_instruction + RETRY_SUFFIX
        print(f"  calling model {MODEL_NAME} prompt {prompt_name}")
        raw_text = call_with_retry(instruction, user_message)
        # The pause between calls keeps a free tier under its rate limit
        time.sleep(DELAY_BETWEEN_CALLS_SECONDS)
        parsed = parser(raw_text)
        if parsed is not None:
            return parsed
        print("  Request failed, trying again. Error: response was not valid JSON in the required shape")
    raise ModelCallFailed(REASON_INVALID_ANSWER, f"model answered prompt {prompt_name} in an invalid shape")


def route(region, ast_verdict):
    # Returns the kind and the reason from the router prompt
    STATS["llm"] += 1
    STATS["prompt_a"] += 1
    user_message = prompt_builder.build_user_message(region, ast_verdict)
    answer = ask_model(prompt_builder.build_system("A"), user_message, parse_kind_response, "A")
    if answer["kind"] == "structural":
        STATS["a_structural"] += 1
    elif answer["kind"] == "unknown":
        STATS["a_unknown"] += 1
    return answer


def run_logic_tests(region, ast_verdict):
    # Returns seven TestAnswer objects in the fixed order
    STATS["prompt_b"] += 1
    user_message = prompt_builder.build_user_message(region, ast_verdict)
    return ask_model(prompt_builder.build_system("B"), user_message, parse_logic_tests_response, "B")
