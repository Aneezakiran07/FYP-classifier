# command line entry point for the classifier
# this module is shared and changes need both owners to agree

import argparse
import os

from classifier.llm import classify_llm, providers
from classifier.llm.classify_llm import DEFAULT_DELAY_BETWEEN_CALLS_SECONDS, DEFAULT_MODEL_NAME
from classifier.pipeline import run_one
from classifier.report import load_ground_truth, print_table, summarize_model


def output_path_for_model(output_path, model):
    # out.jsonl becomes out.model-name.jsonl
    root, ext = os.path.splitext(output_path)
    safe = model.replace("/", "_").replace(":", "_")
    return f"{root}.{safe}{ext or '.jsonl'}"

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
    parser.add_argument("--max-retries", type=int, default=0,
                        help="Give up on a failing model call after this many tries, 0 retries forever")
    parser.add_argument("--rerun", action="store_true",
                        help="Classify every region in the input again and overwrite only those records")
    args = parser.parse_args(argv)

    classify_llm.DELAY_BETWEEN_CALLS_SECONDS = args.delay
    classify_llm.MAX_CALL_RETRIES = args.max_retries
    print(f"Using a delay of {classify_llm.DELAY_BETWEEN_CALLS_SECONDS} seconds between calls")

    if not args.models:
        classify_llm.MODEL_NAME = args.model
        print(f"Using model {classify_llm.MODEL_NAME}")
        run_one(args.input_path, args.output_path, args.rerun)
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
        run_one(args.input_path, model_output, args.rerun)
        rows.append(summarize_model(model, truth))

    print()
    if rows:
        print_table(rows)
    else:
        print("No model was available, nothing was run")
    print("Done")

if __name__ == "__main__":
    main()
