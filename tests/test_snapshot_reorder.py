"""Tests for envforge.snapshot_reorder."""

from __future__ import annotations

import pytest

from envforge.snapshot import Snapshot
from envforge.snapshot_reorder import (
    ReorderError,
    ReorderResult,
    ReorderStrategy,
    reorder_snapshot,
)


def _snap(name: str = "test", **vars_: str) -> Snapshot:
    return Snapshot(name=name, variables=dict(vars_))


# ---------------------------------------------------------------------------
# ReorderResult
# ---------------------------------------------------------------------------

def test_reorder_result_changed_false_when_same_order():
    result = ReorderResult(
        snapshot_name="s",
        strategy=ReorderStrategy.ALPHABETICAL,
        original_order=["A", "B"],
        new_order=["A", "B"],
    )
    assert not result.changed


def test_reorder_result_changed_true_when_different():
    result = ReorderResult(
        snapshot_name="s",
        strategy=ReorderStrategy.ALPHABETICAL,
        original_order=["B", "A"],
        new_order=["A", "B"],
    )
    assert result.changed


def test_reorder_result_str_unchanged():
    result = ReorderResult(
        snapshot_name="mysnap",
        strategy=ReorderStrategy.ALPHABETICAL,
        original_order=["A"],
        new_order=["A"],
    )
    assert "unchanged" in str(result)
    assert "mysnap" in str(result)


def test_reorder_result_str_changed():
    result = ReorderResult(
        snapshot_name="mysnap",
        strategy=ReorderStrategy.REVERSE_ALPHA,
        original_order=["A", "B"],
        new_order=["B", "A"],
    )
    assert "Reordered" in str(result)
    assert "reverse_alpha" in str(result)


# ---------------------------------------------------------------------------
# reorder_snapshot – strategies
# ---------------------------------------------------------------------------

def test_alphabetical_sorts_keys():
    snap = _snap("s", ZEBRA="z", APPLE="a", MANGO="m")
    _, reordered = reorder_snapshot(snap, ReorderStrategy.ALPHABETICAL)
    assert list(reordered.variables.keys()) == ["APPLE", "MANGO", "ZEBRA"]


def test_reverse_alpha_sorts_descending():
    snap = _snap("s", ZEBRA="z", APPLE="a", MANGO="m")
    _, reordered = reorder_snapshot(snap, ReorderStrategy.REVERSE_ALPHA)
    assert list(reordered.variables.keys()) == ["ZEBRA", "MANGO", "APPLE"]


def test_by_value_length_sorts_by_value():
    snap = _snap("s", A="hello world", B="hi", C="hey")
    _, reordered = reorder_snapshot(snap, ReorderStrategy.BY_VALUE_LENGTH)
    keys = list(reordered.variables.keys())
    lengths = [len(reordered.variables[k]) for k in keys]
    assert lengths == sorted(lengths)


def test_custom_order_respects_given_sequence():
    snap = _snap("s", X="1", Y="2", Z="3")
    _, reordered = reorder_snapshot(
        snap, ReorderStrategy.CUSTOM, custom_order=["Z", "X"]
    )
    keys = list(reordered.variables.keys())
    assert keys[0] == "Z"
    assert keys[1] == "X"
    assert keys[2] == "Y"  # trailing key appended alphabetically


def test_custom_order_missing_custom_order_raises():
    snap = _snap("s", A="1")
    with pytest.raises(ReorderError, match="custom_order must be provided"):
        reorder_snapshot(snap, ReorderStrategy.CUSTOM)


def test_custom_order_unknown_key_raises():
    snap = _snap("s", A="1")
    with pytest.raises(ReorderError, match="unknown keys"):
        reorder_snapshot(snap, ReorderStrategy.CUSTOM, custom_order=["NOPE"])


def test_original_snapshot_not_mutated():
    snap = _snap("s", B="2", A="1")
    original_keys = list(snap.variables.keys())
    reorder_snapshot(snap, ReorderStrategy.ALPHABETICAL)
    assert list(snap.variables.keys()) == original_keys


def test_result_metadata_preserved():
    snap = _snap("mysnap", B="2", A="1")
    snap.description = "original desc"
    snap.tags = ["prod"]
    _, reordered = reorder_snapshot(snap, ReorderStrategy.ALPHABETICAL)
    assert reordered.name == "mysnap"
    assert reordered.description == "original desc"
    assert reordered.tags == ["prod"]
