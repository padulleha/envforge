"""Tests for envforge.watch and envforge.cli_watch."""
from __future__ import annotations

import os
import time
import argparse
import pytest
from unittest.mock import patch

from envforge.watch import WatchEvent, poll_once, snapshot_to_baseline
from envforge.snapshot import Snapshot


# ---------------------------------------------------------------------------
# WatchEvent
# ---------------------------------------------------------------------------

def test_watch_event_has_changes_true():
    e = WatchEvent(timestamp=0.0, added={"A": "1"})
    assert e.has_changes()


def test_watch_event_has_changes_false():
    e = WatchEvent(timestamp=0.0)
    assert not e.has_changes()


def test_watch_event_roundtrip():
    e = WatchEvent(
        timestamp=1234567890.0,
        added={"NEW": "val"},
        removed={"OLD": "gone"},
        changed={"X": ("a", "b")},
    )
    restored = WatchEvent.from_dict(e.to_dict())
    assert restored.timestamp == e.timestamp
    assert restored.added == e.added
    assert restored.removed == e.removed
    assert restored.changed == e.changed


def test_watch_event_format_contains_symbols():
    e = WatchEvent(
        timestamp=time.time(),
        added={"A": "1"},
        removed={"B": "2"},
        changed={"C": ("old", "new")},
    )
    text = e.format()
    assert "+ A=1" in text
    assert "- B=2" in text
    assert "~ C" in text


# ---------------------------------------------------------------------------
# poll_once
# ---------------------------------------------------------------------------

def test_poll_once_detects_added():
    baseline = {"EXISTING": "yes"}
    with patch.dict(os.environ, {"EXISTING": "yes", "BRAND_NEW": "hello"}, clear=False):
        event = poll_once(baseline)
    assert "BRAND_NEW" in event.added


def test_poll_once_detects_removed():
    baseline = {"GONE_KEY": "value"}
    env_without = {k: v for k, v in os.environ.items() if k != "GONE_KEY"}
    with patch.dict(os.environ, env_without, clear=True):
        event = poll_once(baseline)
    assert "GONE_KEY" in event.removed


def test_poll_once_detects_changed():
    baseline = {"MY_VAR": "old"}
    with patch.dict(os.environ, {"MY_VAR": "new"}, clear=False):
        event = poll_once(baseline, keys=["MY_VAR"])
    assert "MY_VAR" in event.changed
    assert event.changed["MY_VAR"] == ("old", "new")


def test_poll_once_key_filter():
    baseline = {"A": "1", "B": "2"}
    with patch.dict(os.environ, {"A": "changed", "B": "2"}, clear=True):
        event = poll_once(baseline, keys=["B"])
    assert not event.has_changes()


# ---------------------------------------------------------------------------
# snapshot_to_baseline
# ---------------------------------------------------------------------------

def test_snapshot_to_baseline():
    snap = Snapshot.capture(name="test", keys=["PATH"])
    baseline = snapshot_to_baseline(snap)
    assert isinstance(baseline, dict)
    assert "PATH" in baseline


# ---------------------------------------------------------------------------
# cli_watch (unit, no real sleep)
# ---------------------------------------------------------------------------

def _make_args(**kwargs):
    defaults = {"snapshot": None, "interval": 1, "count": 1, "keys": None, "store": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_watch_missing_snapshot(tmp_path):
    from envforge.store import SnapshotStore
    from envforge.cli_watch import cmd_watch
    store = SnapshotStore(str(tmp_path / "store.json"))
    args = _make_args(snapshot="nonexistent")
    result = cmd_watch(args, store=store)
    assert result == 1


def test_cmd_watch_no_snapshot_runs(tmp_path):
    from envforge.store import SnapshotStore
    from envforge.cli_watch import cmd_watch
    store = SnapshotStore(str(tmp_path / "store.json"))
    args = _make_args(count=1, interval=0)
    with patch("time.sleep"):
        result = cmd_watch(args, store=store)
    assert result == 0
