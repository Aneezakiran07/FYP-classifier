# model calling for stage 4
# owned by Aneeza
# the model only answers questions here and the pipeline turns answers into labels
# the run settings below are set by cli.py and read by the functions in this module

import os
import time

from classifier.llm import prompt_builder, providers
from classifier.llm.parsing import parse_kind_response, parse_logic_tests_response
from classifier.report import STATS


# Model name can be overridden with an env var or the model flag
DEFAULT_MODEL_NAME = os.environ.get(
    "CLASSIFIER_MODEL", os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
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

# These answers from a provider cannot change by sending the same request again
PERMANENT_STATUS_CODES = (400, 401, 403, 404)

# A cap on the backoff wait so it does not grow forever on a stuck request
MAX_BACKOFF_SECONDS = 120

RETRY_SUFFIX = "\n\nYour previous response was not valid. Reply with ONLY the JSON object described above."


class ModelCallFailed(Exception):
    # Carries a reason code for the record and a short detail for the trace
    def __init__(self, code, detail):
        super().__init__(detail)
        self.code = code


def describe_error(error):
    # Names the error without its message because a provider message can echo a key
    status = getattr(error, "status_code", None)
    return type(error).__name__ if status is None else f"{type(error).__name__} status {status}"


def call_with_retry(system_instruction, user_message):
    # One request to the current model, only a passing transport error is retried
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
            if getattr(e, "status_code", None) in PERMANENT_STATUS_CODES:
                raise ModelCallFailed(REASON_PROVIDER_REJECTED, described)
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
