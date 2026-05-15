"""Tests for envforge.snapshot_pivot."""
from __future__ import annotations

import pytest

from envforge.snapshot import Snapshot
from envforge.snapshot_pivot import PivotResult, PivotRow, pivot_snapshot


def _snap(**kwargs) -> Snapshot:
    return Snapshot(name="test", variables=dict(kwargs))


# ---------------------------------------------------------------------------
# PivotRow / PivotResult helpers
# ---------------------------------------------------------------------------

def test_pivot_row_to_dict():
    row = PivotRow(prefix="DB", keys=["DB_HOST"], values={"DB_HOST": "localhost"})
    d = row.to_dict()
    assert d["prefix"] == "DB"
    assert "DB_HOST" in d["keys"]
    assert d["values"]["DB_HOST"] == "localhost"


def test_pivot_result_has_groups_true():
    row = PivotRow(prefix="APP", keys=["APP_ENV"], values={"APP_ENV": "prod"})
    result = PivotResult(rows=[row])
    assert result.has_groups is True


def test_pivot_result_has_groups_false():
    result = PivotResult(rows=[], ungrouped={"PLAIN": "val"})
    assert result.has_groups is False


def test_pivot_result_summary_groups_only():
    row = PivotRow(prefix="X", keys=["X_A"], values={"X_A": "1"})
    result = PivotResult(rows=[row])
    assert "1 prefix group" in result.summary()
    assert "ungrouped" not in result.summary()


def test_pivot_result_summary_with_ungrouped():
    row = PivotRow(prefix="X", keys=["X_A"], values={"X_A": "1"})
    result = PivotResult(rows=[row], ungrouped={"PLAIN": "v"})
    assert "ungrouped" in result.summary()


# ---------------------------------------------------------------------------
# pivot_snapshot — auto prefix detection
# ---------------------------------------------------------------------------

def test_pivot_groups_by_underscore_prefix():
    snap = _snap(DB_HOST="localhost", DB_PORT="5432", APP_ENV="prod")
    result = pivot_snapshot(snap)
    prefixes = {r.prefix for r in result.rows}
    assert "DB" in prefixes
    assert "APP" in prefixes


def test_pivot_ungrouped_keys_without_separator():
    snap = _snap(PLAIN="value", DB_HOST="localhost")
    result = pivot_snapshot(snap)
    assert "PLAIN" in result.ungrouped


def test_pivot_empty_snapshot():
    snap = _snap()
    result = pivot_snapshot(snap)
    assert result.rows == []
    assert result.ungrouped == {}


def test_pivot_custom_separator():
    snap = _snap(**{"DB.HOST": "h", "DB.PORT": "5432", "PLAIN": "v"})
    result = pivot_snapshot(snap, separator=".")
    prefixes = {r.prefix for r in result.rows}
    assert "DB" in prefixes
    assert "PLAIN" in result.ungrouped


def test_pivot_min_prefix_length_filters_short():
    # Key "A_B" has prefix "A" (length 1); with min_prefix_length=2 it goes ungrouped
    snap = _snap(A_B="1", AB_C="2")
    result = pivot_snapshot(snap, min_prefix_length=2)
    prefixes = {r.prefix for r in result.rows}
    assert "A" not in prefixes
    assert "A_B" in result.ungrouped


# ---------------------------------------------------------------------------
# pivot_snapshot — explicit prefixes
# ---------------------------------------------------------------------------

def test_pivot_explicit_prefixes_only_groups_those():
    snap = _snap(DB_HOST="h", APP_ENV="prod", OTHER_KEY="x")
    result = pivot_snapshot(snap, prefixes=["DB"])
    prefixes = {r.prefix for r in result.rows}
    assert "DB" in prefixes
    assert "APP" not in prefixes
    assert "APP_ENV" in result.ungrouped
    assert "OTHER_KEY" in result.ungrouped


def test_pivot_explicit_prefixes_multiple():
    snap = _snap(DB_HOST="h", APP_ENV="prod", CACHE_TTL="60")
    result = pivot_snapshot(snap, prefixes=["DB", "APP"])
    prefixes = {r.prefix for r in result.rows}
    assert {"DB", "APP"} == prefixes
    assert "CACHE_TTL" in result.ungrouped


# ---------------------------------------------------------------------------
# format_text
# ---------------------------------------------------------------------------

def test_format_text_contains_prefix_header():
    snap = _snap(DB_HOST="localhost", DB_PORT="5432")
    result = pivot_snapshot(snap)
    text = result.format_text()
    assert "[DB]" in text


def test_format_text_contains_ungrouped_section():
    snap = _snap(DB_HOST="h", PLAIN="v")
    result = pivot_snapshot(snap)
    text = result.format_text()
    assert "[ungrouped]" in text
    assert "PLAIN" in text


def test_format_text_empty_is_empty_string():
    snap = _snap()
    result = pivot_snapshot(snap)
    assert result.format_text() == ""
