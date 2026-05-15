"""Tests for envforge.snapshot_trim."""
import pytest

from envforge.snapshot import Snapshot
from envforge.snapshot_trim import TrimResult, trim_snapshot


def _snap(variables: dict) -> Snapshot:
    return Snapshot(name="test", variables=variables)


# ---------------------------------------------------------------------------
# TrimResult
# ---------------------------------------------------------------------------

def test_trim_result_str_nothing_to_trim():
    result = TrimResult(name="test")
    assert str(result) == "test: nothing to trim"


def test_trim_result_str_shows_trimmed_keys():
    result = TrimResult(name="test", trimmed_keys=[" FOO "])
    assert "keys trimmed" in str(result)
    assert "FOO" in str(result)


def test_trim_result_str_shows_trimmed_values():
    result = TrimResult(name="test", trimmed_values=["BAR"])
    assert "values trimmed" in str(result)
    assert "BAR" in str(result)


def test_trim_result_str_shows_both():
    result = TrimResult(name="s", trimmed_keys=["K"], trimmed_values=["V"])
    text = str(result)
    assert "keys trimmed" in text
    assert "values trimmed" in text


def test_trim_result_has_changes_false():
    result = TrimResult(name="s")
    assert not result.has_changes


def test_trim_result_has_changes_true_keys():
    result = TrimResult(name="s", trimmed_keys=["X"])
    assert result.has_changes


def test_trim_result_has_changes_true_values():
    result = TrimResult(name="s", trimmed_values=["Y"])
    assert result.has_changes


# ---------------------------------------------------------------------------
# trim_snapshot
# ---------------------------------------------------------------------------

def test_trim_values_removes_whitespace():
    snap = _snap({"KEY": "  hello  "})
    result = trim_snapshot(snap)
    assert result.snapshot.variables["KEY"] == "hello"
    assert "KEY" in result.trimmed_values


def test_trim_keys_removes_whitespace():
    snap = _snap({" MY_VAR ": "value"})
    result = trim_snapshot(snap)
    assert "MY_VAR" in result.snapshot.variables
    assert " MY_VAR " in result.trimmed_keys


def test_trim_clean_vars_unchanged():
    snap = _snap({"CLEAN": "value"})
    result = trim_snapshot(snap)
    assert not result.has_changes
    assert result.snapshot.variables["CLEAN"] == "value"


def test_trim_keys_disabled():
    snap = _snap({" SPACED ": "val"})
    result = trim_snapshot(snap, trim_keys=False)
    assert " SPACED " in result.snapshot.variables
    assert not result.trimmed_keys


def test_trim_values_disabled():
    snap = _snap({"KEY": "  val  "})
    result = trim_snapshot(snap, trim_values=False)
    assert result.snapshot.variables["KEY"] == "  val  "
    assert not result.trimmed_values


def test_trim_preserves_snapshot_metadata():
    snap = Snapshot(name="mysnap", variables={"A": " b "}, description="desc", tags=["t1"])
    result = trim_snapshot(snap)
    assert result.snapshot.name == "mysnap"
    assert result.snapshot.description == "desc"
    assert "t1" in result.snapshot.tags


def test_trim_multiple_keys_and_values():
    snap = _snap({" K1 ": "  v1  ", "K2": "  v2  ", " K3 ": "v3"})
    result = trim_snapshot(snap)
    assert len(result.trimmed_keys) == 2
    assert len(result.trimmed_values) == 2
    assert result.snapshot.variables.get("K1") == "v1"
    assert result.snapshot.variables.get("K2") == "v2"
    assert result.snapshot.variables.get("K3") == "v3"


def test_trim_empty_snapshot():
    snap = _snap({})
    result = trim_snapshot(snap)
    assert not result.has_changes
    assert result.snapshot.variables == {}
