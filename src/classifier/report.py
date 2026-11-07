# Keeps the run counters and prints the end of run report and the model comparison table
# STATS holds counts per layer, pattern, AST verdict, prompt, capped, llm-error and model calls, and RUN_LOG keeps one entry per region
# reset_stats clears both, print_report prints the counts, and load_ground_truth reads hand labels keyed by pull request, file and conflict index
# summarize_model scores labeled regions against the hand labels, skipping capped and llm-error ones, and print_table prints one row per model

# per layer counts and the accuracy table
# this module is shared and holds the run counters that the other modules update

import json
import os

from classifier.schema import strip_family


# Counters for the end of run report, reset at the start of every model run
STATS = {}
# One entry per region handled in this run, used for the accuracy table
RUN_LOG = []

def reset_stats():
    STATS.clear()
    STATS.update({
        "total": 0, "deterministic": 0, "by_pattern": {}, "ast": 0, "by_equivalence": {},
        "llm": 0, "prompt_a": 0, "prompt_b": 0, "a_structural": 0, "a_unknown": 0,
        "needs_verification": 0, "capped": 0, "llm_error": 0, "model_calls": 0,
        "consecutive_llm_errors": 0, "stage_4_skipped": 0,
    })
    RUN_LOG.clear()


reset_stats()

def pct(count):
    total = STATS["total"]
    return f"{(100.0 * count / total) if total else 0.0:.1f}%"

def fmt_dict(counts):
    return "{" + ", ".join(f"{k}: {v}" for k, v in sorted(counts.items())) + "}"

def print_report():
    # Shows how much work each layer did, the numbers for the project report
    s = STATS
    print(f"deterministic matched: {s['deterministic']} ({pct(s['deterministic'])})")
    print(f"  by pattern: {fmt_dict(s['by_pattern'])}")
    print(f"AST gate matched:     {s['ast']} ({pct(s['ast'])})")
    print(f"  by equivalence: {fmt_dict(s['by_equivalence'])}")
    print(f"LLM called:           {s['llm']} ({pct(s['llm'])})")
    extra = f", {s['a_unknown']} were unknown" if s["a_unknown"] else ""
    print(f"  prompt A: {s['prompt_a']}, prompt B: {s['prompt_b']} ({s['a_structural']} were structural{extra})")
    print(f"needs_verification:   {s['needs_verification']} ({pct(s['needs_verification'])})")
    print(f"calls to the model:   {s['model_calls']}")
    if s["capped"]:
        print(f"capped:               {s['capped']} ({pct(s['capped'])})")
    if s["llm_error"]:
        print(f"llm-error:            {s['llm_error']} ({pct(s['llm_error'])})")
    if s["stage_4_skipped"]:
        # These regions have no record so they are not part of the total above
        print(f"reached Stage 4 with the model off, no record written: {s['stage_4_skipped']}")

def load_ground_truth(labels_path):
    # Hand labels keyed the same way as the output records
    truth = {}
    if not labels_path or not os.path.exists(labels_path):
        return truth
    with open(labels_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            # Hand labels may still carry the old family prefix
            true_label = strip_family(row.get("true_label"))
            truth[(row.get("pr_key"), row.get("file_path"), row.get("conflict_index"))] = true_label
    return truth

def matches_truth(entry, true_label):
    # A label counts as right if it equals the true label, or if the true
    # label names the bare subtype that the entry carries alongside it.
    return true_label in (entry["label"], entry.get("subtype"))

def summarize_model(model, truth):
    # One row of the comparison table for the model that just finished
    total = STATS["total"]
    # Capped and llm-error regions have no label and are never scored as wrong
    labeled = [e for e in RUN_LOG if e["key"] in truth and e["label"] is not None]
    llm_entries = [e for e in labeled if e["layer"] == "llm"]
    agreed = sum(matches_truth(e, truth[e["key"]]) for e in llm_entries)
    all_entries = labeled
    overall = sum(matches_truth(e, truth[e["key"]]) for e in all_entries)
    row = {
        "model": model,
        "deterministic": f"{STATS['deterministic'] + STATS['ast']}/{total}",
        "llm_called": f"{STATS['llm']}/{total}",
        "agreed_with_gt": f"{agreed}/{len(llm_entries)}" if truth else "n/a",
        "accuracy": f"{100 * agreed / len(llm_entries):.0f}%" if llm_entries else "n/a",
        "overall_acc": f"{100 * overall / len(all_entries):.0f}%" if all_entries else "n/a",
    }
    return row

def print_table(rows):
    columns = ["model", "deterministic", "llm_called", "agreed_with_gt", "accuracy", "overall_acc"]
    widths = {c: max(len(c), *(len(r[c]) for r in rows)) + 2 for c in columns}
    print("".join(c.ljust(widths[c]) for c in columns).rstrip())
    for r in rows:
        print("".join(r[c].ljust(widths[c]) for c in columns).rstrip())
