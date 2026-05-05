"""Tests for envforge.history and envforge.store_history."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from envforge.history import HistoryEntry, SnapshotHistory
from envforge.store_history import load_history, save_history, record_and_save


# ---------------------------------------------------------------------------
# HistoryEntry
# ---------------------------------------------------------------------------

def test_entry_to_dict_roundtrip():
    e = HistoryEntry(action="captured", snapshot_name="dev", detail="3 vars")
    d = e.to_dict()
    e2 = HistoryEntry.from_dict(d)
    assert e2.action == "captured"
    assert e2.snapshot_name == "dev"
    assert e2.detail == "3 vars"
    assert e2.timestamp == pytest.approx(e.timestamp)


def test_entry_format_contains_action_and_name():
    e = HistoryEntry(action="applied", snapshot_name="prod", timestamp=0.0)
    text = e.format()
    assert "applied" in text
    assert "prod" in text


def test_entry_format_no_detail():
    e = HistoryEntry(action="deleted", snapshot_name="old", timestamp=0.0)
    assert "(" not in e.format()


# ---------------------------------------------------------------------------
# SnapshotHistory
# ---------------------------------------------------------------------------

def test_record_appends_entry():
    h = SnapshotHistory()
    h.record("captured", "dev")
    assert len(h._entries) == 1
    assert h._entries[0].action == "captured"


def test_for_snapshot_filters_correctly():
    h = SnapshotHistory()
    h.record("captured", "dev")
    h.record("applied", "prod")
    h.record("applied", "dev")
    entries = h.for_snapshot("dev")
    assert len(entries) == 2
    assert all(e.snapshot_name == "dev" for e in entries)


def test_recent_returns_n_most_recent():
    h = SnapshotHistory()
    for i in range(25):
        e = HistoryEntry(action="captured", snapshot_name=f"snap{i}", timestamp=float(i))
        h._entries.append(e)
    recent = h.recent(n=10)
    assert len(recent) == 10
    # most recent first
    assert recent[0].snapshot_name == "snap24"


def test_history_serialisation_roundtrip():
    h = SnapshotHistory()
    h.record("captured", "dev", detail="5 vars")
    h.record("applied", "dev")
    h2 = SnapshotHistory.from_list(h.to_list())
    assert len(h2._entries) == 2
    assert h2._entries[0].detail == "5 vars"


# ---------------------------------------------------------------------------
# store_history helpers
# ---------------------------------------------------------------------------

def test_load_history_missing_file(tmp_path):
    h = load_history(tmp_path)
    assert isinstance(h, SnapshotHistory)
    assert h._entries == []


def test_save_and_load_history(tmp_path):
    h = SnapshotHistory()
    h.record("captured", "mysnap")
    save_history(tmp_path, h)
    assert (tmp_path / "history.json").exists()
    h2 = load_history(tmp_path)
    assert len(h2._entries) == 1
    assert h2._entries[0].snapshot_name == "mysnap"


def test_record_and_save_creates_entry(tmp_path):
    record_and_save(tmp_path, "deleted", "old_snap", detail="manual")
    h = load_history(tmp_path)
    assert len(h._entries) == 1
    assert h._entries[0].action == "deleted"
    assert h._entries[0].detail == "manual"


def test_record_and_save_accumulates(tmp_path):
    record_and_save(tmp_path, "captured", "env1")
    record_and_save(tmp_path, "applied", "env1")
    h = load_history(tmp_path)
    assert len(h._entries) == 2
