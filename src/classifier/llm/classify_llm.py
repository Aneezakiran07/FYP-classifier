# model calling and the two prompt flow for stage 4
# owned by Aneeza
# the run settings below are set by cli.py and read by the functions in this module

import os
import time

from classifier.llm import prompt_builder, providers
from classifier.llm.parsing import parse_kind_response, parse_subtype_response
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

# Zero means retry a failing call forever, which keeps the old behavior for
# rate limits, a positive number gives up and marks the region for verification
MAX_CALL_RETRIES = 0

# A model that keeps answering in the wrong shape is asked this many times
# before the region is marked unknown instead of looping forever
MAX_FORMAT_ATTEMPTS = 3

# A cap on the backoff wait so it does not grow forever on a stuck request
MAX_BACKOFF_SECONDS = 120

RETRY_SUFFIX = "\n\nYour previous response was not valid. Reply with ONLY the JSON object described above."

class ModelCallFailed(Exception):
    pass

def call_with_retry(system_instruction, user_message):
    # A single call to the current model, retried with backoff on errors
    # A missing sdk or key is never retried because waiting cannot fix it
    attempt = 0
    while True:
        try:
            return providers.call_model(MODEL_NAME, system_instruction, user_message)
        except providers.ProviderUnavailable as e:
            raise ModelCallFailed(str(e))
        except Exception as e:
            attempt += 1
            if MAX_CALL_RETRIES and attempt >= MAX_CALL_RETRIES:
                raise ModelCallFailed(f"gave up after {attempt} attempts, {e}")
            wait_seconds = min(
                DELAY_BETWEEN_CALLS_SECONDS * (2 ** (attempt - 1)), MAX_BACKOFF_SECONDS
            )
            print(f"  Request failed, trying again. Error: {e}")
            print(f"  Waiting {wait_seconds} seconds before retry")
            time.sleep(wait_seconds)

def ask_model(system_instruction, user_message, parser, prompt_name):
    # One prompt round trip, a bad shape is retried a few times with a
    # stricter reminder and then gives back None
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
    return None

def uncertain(reason, priority="high", unknown_reason="ambiguous", candidate_labels=None):
    # The pipeline says it does not know and hands the region to verification.
    # candidate_labels preserves whatever the model actually picked, so a
    # human reviewer sees the raw guess rather than a forced subtype.
    return {
        "label": "unknown", "confidence": "low", "reason": reason,
        "needs_verification": True, "verification_priority": priority,
        "unknown_reason": unknown_reason,
        "candidate_labels": candidate_labels,
    }

def classify_with_llm(file_path, ours_text, theirs_text, eq, region):
    # Also reports whether the logic prompt ran so its hash is recorded only then
    logic_prompts_before = STATS["prompt_b"]
    result = run_two_prompts(file_path, ours_text, theirs_text, eq, region)
    result["logic_prompt_ran"] = STATS["prompt_b"] > logic_prompts_before
    return result

def run_two_prompts(file_path, ours_text, theirs_text, eq, region):
    # Prompt A decides structural or semantic, prompt B only runs for semantic.
    # Output labels are v3 taxonomy labels in every branch.
    #
    # Escape hatch behavior (v3): a model answer of "other" or a low-confidence
    # answer becomes unknown with the raw answer kept in candidate_labels,
    # instead of being relabeled as the residual logic/business-logic-conflict.
    # Taxonomy rule 15 reserves that label for the case where the other six
    # tests actually fail, not for the case where the model is unsure.
    user_message = prompt_builder.build_user_message(file_path, ours_text, theirs_text, eq)
    STATS["llm"] += 1
    try:
        STATS["prompt_a"] += 1
        kind = ask_model(prompt_builder.build_system("A"), user_message, parse_kind_response, "A")
        if kind is None:
            return uncertain("model answered prompt A in an invalid shape")
        if kind["kind"] == "structural":
            # The rule layer already ran all 11 patterns and the ast gate
            # before reaching here. A structural verdict from the model
            # therefore names a structural/* case the rule layer could not
            # decide, most commonly structural/import-restructure or
            # mechanical/value-only-change, neither of which is implemented
            # in v3. The classifier cannot pick one label without more
            # evidence, so the region goes to verification with the two
            # most likely candidates recorded.
            STATS["a_structural"] += 1
            return uncertain(
                "model says the difference is structural, no rule layer mapping for it in v3",
                priority="high",
                unknown_reason="ambiguous",
                candidate_labels=["structural/formatting", "structural/import-restructure"],
            )
        if kind["kind"] == "unknown":
            STATS["a_unknown"] += 1
            return uncertain(kind["reason"])

        STATS["prompt_b"] += 1
        sub = ask_model(prompt_builder.build_system("B"), user_message, parse_subtype_response, "B")
    except ModelCallFailed as e:
        return uncertain(f"model call failed, {e}")

    # A bad shape from prompt B after all retries: the model did not name a
    # subtype at all. Record what happened and route to verification rather
    # than silently choosing the residual class.
    if sub is None:
        return uncertain(
            f"model answered prompt B in an invalid shape, prompt A reason: {kind['reason']}",
            priority="high",
            unknown_reason="ambiguous",
            candidate_labels=None,
        )

    subtype = sub["subtype"]
    confidence = sub["confidence"]
    is_other = subtype in (None, "other")
    is_low = confidence == "low"

    # Either the model said "other" / null, or it named a subtype but is not
    # confident. Both mean the pipeline does not have a defensible label,
    # so the region goes to verification with the model's own answer kept
    # as a candidate.
    if is_other or is_low:
        candidates = [subtype] if subtype is not None else None
        return uncertain(
            f"model picked {subtype!r} with confidence {confidence}",
            priority="high" if is_low else "normal",
            unknown_reason="ambiguous",
            candidate_labels=candidates,
        )

    return {
        "label": subtype,
        "confidence": confidence,
        "reason": kind["reason"],
        "evidence": sub["evidence"],
    }
