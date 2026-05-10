"""Tests for envforge.dedupe."""

import pytest

from envforge.snapshot import Snapshot
from envforge.dedupe import (
    DedupeResult,
    find_duplicates,
    remove_duplicates,
    _snapshot_fingerprint,
)


def _snap(name: str, variables: dict) -> Snapshot:
    return Snapshot(name=name, variables=variables)


# ---------------------------------------------------------------------------
# _snapshot_fingerprint
# ---------------------------------------------------------------------------

def test_fingerprint_is_order_independent():
    s1 = _snap("a", {"X": "1", "Y": "2"})
    s2 = _snap("b", {"Y": "2", "X": "1"})
    assert _snapshot_fingerprint(s1) == _snapshot_fingerprint(s2)


def test_fingerprint_differs_for_different_values():
    s1 = _snap("a", {"X": "1"})
    s2 = _snap("b", {"X": "2"})
    assert _snapshot_fingerprint(s1) != _snapshot_fingerprint(s2)


# ---------------------------------------------------------------------------
# find_duplicates
# ---------------------------------------------------------------------------

def test_find_duplicates_no_duplicates():
    snaps = {
        "alpha": _snap("alpha", {"A": "1"}),
        "beta": _snap("beta", {"B": "2"}),
    }
    result = find_duplicates(snaps)
    assert not result.has_duplicates
    assert result.groups == []


def test_find_duplicates_detects_pair():
    snaps = {
        "alpha": _snap("alpha", {"A": "1"}),
        "alpha2": _snap("alpha2", {"A": "1"}),
        "beta": _snap("beta", {"B": "2"}),
    }
    result = find_duplicates(snaps)
    assert result.has_duplicates
    assert len(result.groups) == 1
    assert sorted(result.groups[0]) == ["alpha", "alpha2"]


def test_find_duplicates_multiple_groups():
    snaps = {
        "a": _snap("a", {"X": "1"}),
        "b": _snap("b", {"X": "1"}),
        "c": _snap("c", {"Y": "2"}),
        "d": _snap("d", {"Y": "2"}),
    }
    result = find_duplicates(snaps)
    assert len(result.groups) == 2


# ---------------------------------------------------------------------------
# remove_duplicates
# ---------------------------------------------------------------------------

def test_remove_duplicates_keep_first():
    snaps = {
        "beta": _snap("beta", {"A": "1"}),
        "alpha": _snap("alpha", {"A": "1"}),
    }
    result = remove_duplicates(snaps, keep="first")
    assert "alpha" in snaps
    assert "beta" not in snaps
    assert "beta" in result.removed


def test_remove_duplicates_keep_last():
    snaps = {
        "alpha": _snap("alpha", {"A": "1"}),
        "beta": _snap("beta", {"A": "1"}),
    }
    result = remove_duplicates(snaps, keep="last")
    assert "beta" in snaps
    assert "alpha" not in snaps
    assert "alpha" in result.removed


def test_remove_duplicates_no_duplicates_unchanged():
    snaps = {
        "alpha": _snap("alpha", {"A": "1"}),
        "beta": _snap("beta", {"B": "2"}),
    }
    result = remove_duplicates(snaps)
    assert len(snaps) == 2
    assert result.removed == []


# ---------------------------------------------------------------------------
# DedupeResult.__str__
# ---------------------------------------------------------------------------

def test_str_no_duplicates():
    r = DedupeResult()
    assert "No duplicate" in str(r)


def test_str_with_groups_and_removed():
    r = DedupeResult(groups=[["a", "b"]], removed=["b"])
    text = str(r)
    assert "1 duplicate group" in text
    assert "a, b" in text
    assert "Removed" in text
