"""Tests for envforge.snapshot_summary and envforge.cli_summary."""
from __future__ import annotations

import argparse
from unittest.mock import MagicMock, patch

import pytest

from envforge.snapshot import Snapshot
from envforge.snapshot_summary import (
    SnapshotSummary,
    multi_summary,
    summarise,
)


def _snap(name: str, variables: dict | None = None, **kwargs) -> Snapshot:
    s = Snapshot(name=name, variables=variables or {})
    for k, v in kwargs.items():
        setattr(s, k, v)
    return s


# --- SnapshotSummary.one_line ---

def test_one_line_basic():
    s = SnapshotSummary(name="dev", key_count=3)
    assert "dev" in s.one_line()
    assert "3 keys" in s.one_line()


def test_one_line_with_tags():
    s = SnapshotSummary(name="dev", key_count=2, tags=["ci", "prod"])
    line = s.one_line()
    assert "ci" in line
    assert "prod" in line


def test_one_line_with_description():
    s = SnapshotSummary(name="dev", key_count=1, description="My env")
    assert "My env" in s.one_line()


def test_one_line_no_tags_no_description():
    s = SnapshotSummary(name="x", key_count=0)
    assert "[" not in s.one_line()
    assert "—" not in s.one_line()


# --- SnapshotSummary.detail ---

def test_detail_contains_name_and_keys():
    s = SnapshotSummary(name="staging", key_count=5)
    d = s.detail()
    assert "staging" in d
    assert "5" in d


def test_detail_shows_none_for_empty_tags():
    s = SnapshotSummary(name="x", key_count=0)
    assert "(none)" in s.detail()


def test_detail_includes_created_at():
    s = SnapshotSummary(name="x", key_count=0, created_at="2024-01-01T00:00:00")
    assert "2024-01-01" in s.detail()


# --- summarise ---

def test_summarise_key_count():
    snap = _snap("dev", {"A": "1", "B": "2"})
    s = summarise(snap)
    assert s.key_count == 2
    assert s.name == "dev"


def test_summarise_with_tags():
    snap = _snap("dev", {"A": "1"})
    snap.tags = ["ci", "prod"]
    s = summarise(snap)
    assert "ci" in s.tags


def test_summarise_no_tags_attr():
    snap = _snap("dev", {})
    if hasattr(snap, "tags"):
        del snap.__dict__["tags"]
    s = summarise(snap)
    assert s.tags == []


# --- multi_summary ---

def test_multi_summary_empty():
    assert multi_summary([]) == "No snapshots found."


def test_multi_summary_one_line_per_snapshot():
    snaps = [_snap("a", {"X": "1"}), _snap("b", {"Y": "2", "Z": "3"})]
    out = multi_summary(snaps)
    assert "a" in out
    assert "b" in out
    assert len(out.splitlines()) == 2


def test_multi_summary_detail_mode():
    snaps = [_snap("a", {"X": "1"}), _snap("b", {})]
    out = multi_summary(snaps, detail=True)
    # detail mode separates blocks with blank lines
    assert "\n\n" in out
