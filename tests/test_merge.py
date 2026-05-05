"""Tests for envforge.merge and cli_merge."""

from __future__ import annotations

import argparse
from unittest.mock import MagicMock, patch

import pytest

from envforge.merge import (
    ConflictStrategy,
    MergeConflictError,
    merge_snapshots,
)
from envforge.snapshot import Snapshot


def _snap(name: str, variables: dict, tags=None) -> Snapshot:
    return Snapshot(name=name, variables=variables, tags=tags or [])


def test_merge_disjoint_keys():
    a = _snap("a", {"FOO": "1", "BAR": "2"})
    b = _snap("b", {"BAZ": "3"})
    result = merge_snapshots(a, b, name="c")
    assert result.variables == {"FOO": "1", "BAR": "2", "BAZ": "3"}


def test_merge_same_value_no_conflict():
    a = _snap("a", {"FOO": "same"})
    b = _snap("b", {"FOO": "same"})
    result = merge_snapshots(a, b, name="c")
    assert result.variables["FOO"] == "same"


def test_merge_conflict_use_other():
    a = _snap("a", {"FOO": "base"})
    b = _snap("b", {"FOO": "other"})
    result = merge_snapshots(a, b, name="c", strategy=ConflictStrategy.USE_OTHER)
    assert result.variables["FOO"] == "other"


def test_merge_conflict_use_base():
    a = _snap("a", {"FOO": "base"})
    b = _snap("b", {"FOO": "other"})
    result = merge_snapshots(a, b, name="c", strategy=ConflictStrategy.USE_BASE)
    assert result.variables["FOO"] == "base"


def test_merge_conflict_error_raises():
    a = _snap("a", {"FOO": "base"})
    b = _snap("b", {"FOO": "other"})
    with pytest.raises(MergeConflictError) as exc_info:
        merge_snapshots(a, b, name="c", strategy=ConflictStrategy.ERROR)
    assert "FOO" in exc_info.value.conflicts


def test_merge_tags_combined():
    a = _snap("a", {}, tags=["prod", "backend"])
    b = _snap("b", {}, tags=["staging", "backend"])
    result = merge_snapshots(a, b, name="c")
    assert set(result.tags) == {"prod", "backend", "staging"}


def test_merge_result_name_and_description():
    a = _snap("alpha", {})
    b = _snap("beta", {})
    result = merge_snapshots(a, b, name="gamma", description="custom desc")
    assert result.name == "gamma"
    assert result.description == "custom desc"


def test_merge_default_description_contains_source_names():
    a = _snap("alpha", {})
    b = _snap("beta", {})
    result = merge_snapshots(a, b, name="gamma")
    assert "alpha" in result.description
    assert "beta" in result.description


def test_cmd_merge_missing_base(capsys):
    from envforge.cli_merge import cmd_merge

    store = MagicMock()
    store.get.side_effect = lambda n: None

    args = argparse.Namespace(
        base="missing", other="b", name="c",
        strategy="other", description=None, store=None
    )
    with patch("envforge.cli_merge.get_store", return_value=store):
        with pytest.raises(SystemExit):
            cmd_merge(args)
    captured = capsys.readouterr()
    assert "missing" in captured.err


def test_cmd_merge_conflict_error_exits(capsys):
    from envforge.cli_merge import cmd_merge

    snap_a = _snap("a", {"X": "1"})
    snap_b = _snap("b", {"X": "2"})
    store = MagicMock()
    store.get.side_effect = lambda n: snap_a if n == "a" else snap_b

    args = argparse.Namespace(
        base="a", other="b", name="c",
        strategy="error", description=None, store=None
    )
    with patch("envforge.cli_merge.get_store", return_value=store):
        with pytest.raises(SystemExit):
            cmd_merge(args)
    captured = capsys.readouterr()
    assert "X" in captured.err
