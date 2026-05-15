"""Tests for envforge.snapshot_label."""
import pytest
from envforge.snapshot_label import (
    LabelSet,
    LabelError,
    add_label,
    remove_label,
    get_labels,
    filter_by_label,
)


# ── LabelSet basics ──────────────────────────────────────────────────────────

def test_labelset_roundtrip():
    ls = LabelSet(snapshot_name="dev", labels={"env": "dev", "owner": "alice"})
    assert LabelSet.from_dict(ls.to_dict()) == ls


def test_labelset_defaults():
    ls = LabelSet(snapshot_name="prod")
    assert ls.labels == {}


def test_labelset_format_no_labels():
    ls = LabelSet(snapshot_name="staging")
    assert "(no labels)" in ls.format()
    assert "staging" in ls.format()


def test_labelset_format_with_labels():
    ls = LabelSet(snapshot_name="qa", labels={"tier": "test"})
    fmt = ls.format()
    assert "tier=test" in fmt
    assert "qa" in fmt


# ── add_label ────────────────────────────────────────────────────────────────

def test_add_label_creates_new_labelset():
    result = add_label([], "snap1", "env", "prod")
    assert len(result) == 1
    assert result[0].snapshot_name == "snap1"
    assert result[0].labels["env"] == "prod"


def test_add_label_updates_existing():
    existing = [LabelSet(snapshot_name="snap1", labels={"env": "dev"})]
    result = add_label(existing, "snap1", "env", "prod")
    assert len(result) == 1
    assert result[0].labels["env"] == "prod"


def test_add_label_adds_new_key_to_existing():
    existing = [LabelSet(snapshot_name="snap1", labels={"env": "dev"})]
    result = add_label(existing, "snap1", "owner", "bob")
    assert result[0].labels["owner"] == "bob"
    assert result[0].labels["env"] == "dev"


def test_add_label_empty_key_raises():
    with pytest.raises(LabelError):
        add_label([], "snap1", "", "value")


# ── remove_label ─────────────────────────────────────────────────────────────

def test_remove_label_present():
    existing = [LabelSet(snapshot_name="snap1", labels={"env": "dev", "owner": "alice"})]
    result = remove_label(existing, "snap1", "env")
    assert "env" not in result[0].labels
    assert "owner" in result[0].labels


def test_remove_label_missing_key_silent():
    existing = [LabelSet(snapshot_name="snap1", labels={"owner": "alice"})]
    result = remove_label(existing, "snap1", "nonexistent")
    assert result[0].labels == {"owner": "alice"}


def test_remove_label_unknown_snapshot_noop():
    result = remove_label([], "ghost", "key")
    assert result == []


# ── get_labels ────────────────────────────────────────────────────────────────

def test_get_labels_found():
    existing = [LabelSet(snapshot_name="snap1", labels={"x": "1"})]
    ls = get_labels(existing, "snap1")
    assert ls is not None
    assert ls.labels["x"] == "1"


def test_get_labels_not_found_returns_none():
    assert get_labels([], "missing") is None


# ── filter_by_label ───────────────────────────────────────────────────────────

def test_filter_by_label_key_only():
    sets = [
        LabelSet("a", {"tier": "prod"}),
        LabelSet("b", {"tier": "dev"}),
        LabelSet("c", {"owner": "alice"}),
    ]
    result = filter_by_label(sets, "tier")
    names = [ls.snapshot_name for ls in result]
    assert "a" in names and "b" in names and "c" not in names


def test_filter_by_label_key_and_value():
    sets = [
        LabelSet("a", {"tier": "prod"}),
        LabelSet("b", {"tier": "dev"}),
    ]
    result = filter_by_label(sets, "tier", "prod")
    assert len(result) == 1
    assert result[0].snapshot_name == "a"


def test_filter_by_label_no_match():
    sets = [LabelSet("a", {"owner": "alice"})]
    assert filter_by_label(sets, "tier") == []
