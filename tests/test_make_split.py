# Tests for the make_split script, loaded from the scripts folder by its file path
# They check that the same seed gives the same split and a different seed gives a different one
# They check that input order does not change the split and every pull request lands in exactly one set
# They check that each file count bucket keeps the same dev, test and train shares

import importlib.util
from collections import Counter
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "make_split.py"
spec = importlib.util.spec_from_file_location("make_split", SCRIPT)
make_split = importlib.util.module_from_spec(spec)
spec.loader.exec_module(make_split)


def rows():
    small = [{"pr_key": f"o/r#{i}", "bucket": "1-3"} for i in range(800)]
    large = [{"pr_key": f"o/s#{i}", "bucket": "4-10"} for i in range(200)]
    return small + large


def test_the_same_seed_gives_the_same_split():
    assert make_split.split_rows(rows(), 7) == make_split.split_rows(rows(), 7)


def test_a_different_seed_gives_a_different_split():
    assert make_split.split_rows(rows(), 7) != make_split.split_rows(rows(), 8)


def test_input_order_does_not_change_the_split():
    forward = {r["pr_key"]: r["split"] for r in make_split.split_rows(rows(), 7)}
    backward = {r["pr_key"]: r["split"] for r in make_split.split_rows(rows()[::-1], 7)}
    assert forward == backward


def test_every_pull_request_lands_in_exactly_one_set():
    split = make_split.split_rows(rows())
    assert len(split) == len({r["pr_key"] for r in split}) == 1000
    assert {r["split"] for r in split} == {"train", "dev", "test"}


def test_each_bucket_keeps_the_same_shares():
    counts = Counter((r["bucket"], r["split"]) for r in make_split.split_rows(rows()))
    assert counts[("1-3", "dev")] == counts[("1-3", "test")] == 120
    assert counts[("4-10", "dev")] == counts[("4-10", "test")] == 30
    assert counts[("1-3", "train")] == 560 and counts[("4-10", "train")] == 140
