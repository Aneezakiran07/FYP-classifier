# command line entry point for the classifier
# this module is shared and changes need both owners to agree

import argparse
import os

from classifier.llm import classify_llm, providers
from classifier.llm.classify_llm import (
    DEFAULT_DELAY_BETWEEN_CALLS_SECONDS, DEFAULT_MAX_CALL_ATTEMPTS, DEFAULT_MODEL_NAME,
)
from classifier.pipeline import run_one
from classifier.report import load_ground_truth, print_table, summarize_model


def output_path_for_model(output_path, model):
    # out.jsonl becomes out.model-name.jsonl
    root, ext = os.path.splitext(output_path)
    safe = model.replace("/", "_").replace(":", "_")
    return f"{root}.{safe}{ext or '.jsonl'}"

def print_usage(model):
    # The cost itself depends on the price of the model on the day of the run
    usage = providers.USAGE
    print(f"tokens for {model}: {usage['input']} input, {usage['output']} output")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Label merge conflict regions with patterns, an ast gate and a model"
    )
    parser.add_argument("input_path", help="Path to the input JSONL file")
    parser.add_argument("output_path", help="Path to the output JSONL file")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY_BETWEEN_CALLS_SECONDS,
                        help=f"Seconds to wait between API calls, defaults to {DEFAULT_DELAY_BETWEEN_CALLS_SECONDS}")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL_NAME,
                        help=f"Model name to send to the API, defaults to {DEFAULT_MODEL_NAME}")
    parser.add_argument("--models", type=str, default=None,
                        help="Comma separated model names, runs the same input through each and writes one output file per model")
    parser.add_argument("--labels", type=str, default=None,
                        help="Hand labels jsonl used for the accuracy columns, defaults to sample_labels.jsonl next to the input")
    parser.add_argument("--max-retries", type=int, default=DEFAULT_MAX_CALL_ATTEMPTS,
                        help=f"Give up on a failing model call after this many tries, defaults to {DEFAULT_MAX_CALL_ATTEMPTS}")
    parser.add_argument("--rerun", action="store_true",
                        help="Classify every region in the input again and overwrite only those records")
    parser.add_argument("--retry-errors", action="store_true",
                        help="Classify the llm-error regions again against one model and overwrite those records")
    parser.add_argument("--max-calls", type=int, default=None,
                        help="Stop the run after this many model calls, run the same command again to resume")
    parser.add_argument("--no-llm", action="store_true",
                        help="Run only the rule stages, regions that reach Stage 4 get no record and are counted")
    args = parser.parse_args(argv)
    if args.max_retries < 1:
        parser.error("--max-retries must be at least 1")
    if args.retry_errors and (args.models or args.rerun):
        parser.error("--retry-errors runs against one model and cannot be used with --models or --rerun")
    if args.no_llm and (args.models or args.retry_errors or args.max_calls):
        parser.error("--no-llm calls no model and cannot be used with --models, --retry-errors or --max-calls")
    if args.no_llm and args.rerun:
        # A region that reaches Stage 4 writes nothing, so an old model record for it would survive the rerun
        parser.error("--no-llm cannot be used with --rerun, start from an empty output file instead")

    if args.no_llm:
        # No key is checked because no model is called
        print("The model is off, Stage 4 is skipped by choice and nothing is capped")
        run_one(args.input_path, args.output_path, use_llm=False)
        print("Done")
        return

    classify_llm.DELAY_BETWEEN_CALLS_SECONDS = args.delay
    classify_llm.MAX_CALL_ATTEMPTS = args.max_retries
    print(f"Using a delay of {classify_llm.DELAY_BETWEEN_CALLS_SECONDS} seconds between calls")

    if not args.models:
        # Stops here so a missing key does not fill the output with llm-error records
        ok, warning = providers.check_available(args.model)
        if not ok:
            parser.error(f"model {args.model} is not available, {warning}")
        classify_llm.MODEL_NAME = args.model
        print(f"Using model {classify_llm.MODEL_NAME}")
        providers.USAGE.clear()
        run_one(args.input_path, args.output_path, args.rerun, args.retry_errors, args.max_calls)
        print_usage(args.model)
        print("Done")
        return

    labels_path = args.labels or os.path.join(os.path.dirname(os.path.abspath(args.input_path)), "sample_labels.jsonl")
    truth = load_ground_truth(labels_path)
    if not truth:
        print(f"No hand labels found at {labels_path}, accuracy columns will be n/a")

    rows = []
    for model in [m.strip() for m in args.models.split(",") if m.strip()]:
        ok, warning = providers.check_available(model)
        if not ok:
            print(f"Warning, skipping {model}, {warning}")
            continue
        classify_llm.MODEL_NAME = model
        model_output = output_path_for_model(args.output_path, model)
        print(f"\n=== {model} -> {model_output}")
        providers.USAGE.clear()
        run_one(args.input_path, model_output, args.rerun, max_calls=args.max_calls)
        print_usage(model)
        rows.append(summarize_model(model, truth))

    print()
    if rows:
        print_table(rows)
    else:
        print("No model was available, nothing was run")
    print("Done")

if __name__ == "__main__":
    main()
