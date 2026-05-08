"""Tests for envforge.prune."""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

import pytest

from envforge.prune import PruneError, PruneResult, prune_by_age, prune_by_count
from envforge.snapshot import Snapshot


# ---------------------------------------------------------------------------
# Minimal fake store
# ---------------------------------------------------------------------------

class _FakeStore:
    def __init__(self, snaps: Dict[str, Snapshot]):
        self._snaps = dict(snaps)

    def list(self):
        return list(self._snaps.keys())

    def get(self, name: str) -> Optional[Snapshot]:
        return self._snaps.get(name)

    def delete(self, name: str) -> None:
        self._snaps.pop(name, None)


def _snap(name: str, days_ago: int = 0) -> Snapshot:
    created = datetime.now(tz=timezone.utc) - timedelta(days=days_ago)
    s = Snapshot(name=name, variables={"K": "V"})
    s.created_at = created
    return s


# ---------------------------------------------------------------------------
# PruneResult
# ---------------------------------------------------------------------------

def test_prune_result_str_no_removed():
    r = PruneResult(kept=["a", "b"])
    assert "No snapshots pruned" in str(r)


def test_prune_result_str_with_removed():
    r = PruneResult(removed=["old1", "old2"], kept=["new"])
    text = str(r)
    assert "2" in text
    assert "old1" in text
    assert "old2" in text


# ---------------------------------------------------------------------------
# prune_by_age
# ---------------------------------------------------------------------------

def test_prune_by_age_removes_old():
    store = _FakeStore({
        "old": _snap("old", days_ago=10),
        "new": _snap("new", days_ago=1),
    })
    result = prune_by_age(store, max_age_days=5)
    assert "old" in result.removed
    assert "new" in result.kept
    assert store.get("old") is None
    assert store.get("new") is not None


def test_prune_by_age_dry_run_does_not_delete():
    store = _FakeStore({"old": _snap("old", days_ago=20)})
    result = prune_by_age(store, max_age_days=5, dry_run=True)
    assert "old" in result.removed
    assert store.get("old") is not None  # not actually deleted


def test_prune_by_age_nothing_to_prune():
    store = _FakeStore({"fresh": _snap("fresh", days_ago=0)})
    result = prune_by_age(store, max_age_days=30)
    assert result.removed == []
    assert "fresh" in result.kept


def test_prune_by_age_invalid_days_raises():
    store = _FakeStore({})
    with pytest.raises(PruneError):
        prune_by_age(store, max_age_days=0)


# ---------------------------------------------------------------------------
# prune_by_count
# ---------------------------------------------------------------------------

def test_prune_by_count_keeps_newest():
    store = _FakeStore({
        "a": _snap("a", days_ago=5),
        "b": _snap("b", days_ago=3),
        "c": _snap("c", days_ago=1),
    })
    result = prune_by_count(store, keep=2)
    assert "a" in result.removed
    assert "b" in result.kept
    assert "c" in result.kept
    assert store.get("a") is None


def test_prune_by_count_dry_run():
    store = _FakeStore({
        "x": _snap("x", days_ago=10),
        "y": _snap("y", days_ago=1),
    })
    result = prune_by_count(store, keep=1, dry_run=True)
    assert "x" in result.removed
    assert store.get("x") is not None  # not deleted in dry_run


def test_prune_by_count_keep_more_than_existing():
    store = _FakeStore({"only": _snap("only", days_ago=0)})
    result = prune_by_count(store, keep=5)
    assert result.removed == []
    assert "only" in result.kept


def test_prune_by_count_invalid_keep_raises():
    store = _FakeStore({})
    with pytest.raises(PruneError):
        prune_by_count(store, keep=-1)
