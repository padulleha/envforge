"""Tests for envforge.rollback."""

from __future__ import annotations

import pytest

from envforge.snapshot import Snapshot
from envforge.history import SnapshotHistory, HistoryEntry
from envforge.rollback import get_rollback_points, rollback_to, RollbackPoint


def _make_snap(name: str, vals: dict) -> Snapshot:
    s = Snapshot(name=name, variables=vals)
    return s


def _make_history(entries):
    h = SnapshotHistory(entries=list(entries))
    return h


def _entry(name, action="capture", snap=None):
    return HistoryEntry(
        timestamp="2024-06-01T12:00:00",
        action=action,
        name=name,
        snapshot_data=snap.to_dict() if snap else None,
    )


def test_get_rollback_points_empty():
    h = _make_history([])
    points = get_rollback_points("mysnap", h)
    assert points == []


def test_get_rollback_points_skips_no_data():
    h = _make_history([_entry("mysnap", snap=None)])
    points = get_rollback_points("mysnap", h)
    assert points == []


def test_get_rollback_points_returns_restorable():
    snap = _make_snap("mysnap", {"A": "1"})
    h = _make_history([_entry("mysnap", snap=snap)])
    points = get_rollback_points("mysnap", h)
    assert len(points) == 1
    assert isinstance(points[0], RollbackPoint)
    assert points[0].index == 0
    assert points[0].snapshot.variables == {"A": "1"}


def test_get_rollback_points_newest_first():
    s1 = _make_snap("mysnap", {"A": "1"})
    s2 = _make_snap("mysnap", {"A": "2"})
    e1 = _entry("mysnap", snap=s1)
    e1 = HistoryEntry(timestamp="2024-06-01T10:00:00", action="capture", name="mysnap", snapshot_data=s1.to_dict())
    e2 = HistoryEntry(timestamp="2024-06-01T11:00:00", action="capture", name="mysnap", snapshot_data=s2.to_dict())
    h = _make_history([e1, e2])
    points = get_rollback_points("mysnap", h)
    # newest (e2) should be index 0
    assert points[0].snapshot.variables == {"A": "2"}
    assert points[1].snapshot.variables == {"A": "1"}


def test_get_rollback_points_respects_limit():
    snaps = [_make_snap("s", {"X": str(i)}) for i in range(5)]
    entries = [
        HistoryEntry(timestamp=f"2024-06-01T0{i}:00:00", action="capture", name="s", snapshot_data=snaps[i].to_dict())
        for i in range(5)
    ]
    h = _make_history(entries)
    points = get_rollback_points("s", h, limit=3)
    assert len(points) == 3


def test_rollback_to_valid_index():
    snap = _make_snap("mysnap", {"K": "v"})
    h = _make_history([
        HistoryEntry(timestamp="2024-06-01T12:00:00", action="capture", name="mysnap", snapshot_data=snap.to_dict())
    ])
    result = rollback_to("mysnap", 0, h)
    assert result is not None
    assert result.variables == {"K": "v"}


def test_rollback_to_invalid_index():
    h = _make_history([])
    result = rollback_to("mysnap", 99, h)
    assert result is None


def test_rollback_point_format():
    snap = _make_snap("s", {})
    entry = HistoryEntry(timestamp="2024-06-01T15:30:00", action="capture", name="s", detail="auto", snapshot_data=snap.to_dict())
    point = RollbackPoint(index=2, entry=entry, snapshot=snap)
    fmt = point.format()
    assert "[2]" in fmt
    assert "capture" in fmt
    assert "auto" in fmt
