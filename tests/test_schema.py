# Tests for schema.py, the shared labels, helpers and record rules
# They check there are 23 labels with no family prefix, old prefixed names convert and names outside the taxonomy are refused
# They check every pattern has a stage, the base state values, and that the input hash tells a missing base from an empty one
# They check that capped and llm-error refuse a label, classified needs a real label, unknown needs a reason and made up statuses fail

import pytest

from classifier import schema
from classifier.pipeline import STAGE_BY_PATTERN
from classifier.rules.patterns import PATTERNS


def test_there_are_23_labels_with_no_family_prefix():
    assert len(schema.LABELS) == len(set(schema.LABELS)) == 23
    assert not any("/" in label for label in schema.LABELS)


def test_old_prefixed_names_convert_and_outside_names_are_refused():
    assert schema.bare_label("mechanical/same-change") == "same-change"
    assert schema.bare_label("unknown") == "unknown"
    with pytest.raises(ValueError):
        schema.bare_label("not-reviewed")


def test_every_pattern_has_a_stage():
    assert {pattern.name for pattern in PATTERNS} == set(STAGE_BY_PATTERN)


@pytest.mark.parametrize("raw,expected", [
    ({"base_text": "a"}, "present"),
    ({"base_text": ""}, "empty"),
    ({}, "missing"),
    ({"base_text": None}, "missing"),
    ({"no_markers": True}, "no-markers"),
])
def test_base_state(raw, expected):
    assert schema.find_base_state(raw) == expected


def test_input_hash_tells_a_missing_base_from_an_empty_base():
    shared = {"file_path": "a.ts", "ours_text": "x", "theirs_text": "y"}
    assert schema.compute_input_hash(shared) != schema.compute_input_hash({**shared, "base_text": ""})


def test_input_hash_changes_with_the_text_and_is_stable():
    raw = {"file_path": "a.ts", "ours_text": "x", "theirs_text": "y", "base_text": "z"}
    assert schema.compute_input_hash(raw) == schema.compute_input_hash(dict(raw))
    assert schema.compute_input_hash(raw) != schema.compute_input_hash({**raw, "ours_text": "w"})


def test_no_marker_regions_get_their_position_as_index():
    region = schema.Region.from_raw("o/r#1", 7, {"file_path": "a.ts", "no_markers": True})
    assert region.effective_index == "no_markers_7"
    assert region.key == ("o/r#1", "a.ts", "no_markers_7")


@pytest.mark.parametrize("status", ["capped", "llm-error"])
def test_unlabeled_statuses_refuse_a_label_and_require_a_reason(status):
    with pytest.raises(ValueError):
        schema.Result(status=status, stage=4, label="unknown", reason="r").to_block()
    with pytest.raises(ValueError):
        schema.Result(status=status, stage=4).to_block()
    assert "label" not in schema.Result(status=status, stage=4, reason="r").to_block()


def test_classified_needs_a_real_label_and_unknown_needs_a_reason():
    with pytest.raises(ValueError):
        schema.Result(status="classified", stage=1, label="not-reviewed").to_block()
    with pytest.raises(ValueError):
        schema.Result(status="classified", stage=4, label="unknown").to_block()
    block = schema.Result(status="classified", stage=1, label="same-change").to_block()
    assert block["label"] == "same-change"


def test_a_made_up_status_is_refused():
    with pytest.raises(ValueError):
        schema.Result(status="done", stage=1, label="same-change").to_block()
