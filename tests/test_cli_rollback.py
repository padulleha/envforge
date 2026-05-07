"""Tests for envforge.cli_rollback."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

import pytest

from envforge.snapshot import Snapshot
from envforge.store import SnapshotStore
from envforge.history import SnapshotHistory, HistoryEntry
from envforge.store_history import save_history
from envforge.cli_rollback import cmd_rollback_list, cmd_rollback_apply


@pytest.fixture()
def tmp_store(tmp_path):
    return str(tmp_path / "store.json")


def _make_args(tmp_store, **kwargs):
    ns = argparse.Namespace(store=tmp_store, **kwargs)
    return ns


def _make_snap(name, vals):
    return Snapshot(name=name, variables=vals)


def _save_snap(tmp_store, snap):
    store = SnapshotStore(tmp_store)
    store.save(snap)


def _save_hist(tmp_store, entries):
    h = SnapshotHistory(entries=list(entries))
    save_history(tmp_store, h)


def test_rollback_list_empty(tmp_store, capsys):
    _save_hist(tmp_store, [])
    args = _make_args(tmp_store, name="mysnap", limit=10)
    rc = cmd_rollback_list(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "No rollback points" in out


def test_rollback_list_shows_points(tmp_store, capsys):
    snap = _make_snap("mysnap", {"A": "1"})
    _save_snap(tmp_store, snap)
    entry = HistoryEntry(
        timestamp="2024-06-01T12:00:00",
        action="capture",
        name="mysnap",
        snapshot_data=snap.to_dict(),
    )
    _save_hist(tmp_store, [entry])
    args = _make_args(tmp_store, name="mysnap", limit=10)
    rc = cmd_rollback_list(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "[0]" in out
    assert "capture" in out


def test_rollback_apply_invalid_index(tmp_store, capsys):
    _save_hist(tmp_store, [])
    args = _make_args(tmp_store, name="mysnap", index=5)
    rc = cmd_rollback_apply(args)
    assert rc == 1
    err = capsys.readouterr().err
    assert "not found" in err


def test_rollback_apply_restores_snapshot(tmp_store, capsys):
    snap = _make_snap("mysnap", {"X": "old_value"})
    _save_snap(tmp_store, snap)
    entry = HistoryEntry(
        timestamp="2024-06-01T12:00:00",
        action="capture",
        name="mysnap",
        snapshot_data=snap.to_dict(),
    )
    _save_hist(tmp_store, [entry])
    # overwrite with new value
    snap2 = _make_snap("mysnap", {"X": "new_value"})
    _save_snap(tmp_store, snap2)

    args = _make_args(tmp_store, name="mysnap", index=0)
    rc = cmd_rollback_apply(args)
    assert rc == 0

    store = SnapshotStore(tmp_store)
    restored = store.get("mysnap")
    assert restored.variables["X"] == "old_value"
    out = capsys.readouterr().out
    assert "Rolled back" in out
