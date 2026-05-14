"""Tests for envforge.batch module."""
from __future__ import annotations

import os
import pytest

from envforge.batch import BatchResult, batch_apply, batch_capture, batch_delete
from envforge.snapshot import Snapshot


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _snap(name: str, data: dict | None = None) -> Snapshot:
    s = Snapshot(name=name, variables=data or {"KEY": "val"})
    return s


class _FakeStore:
    def __init__(self, snapshots: dict | None = None):
        self._data: dict[str, Snapshot] = dict(snapshots or {})
        self.deleted: list[str] = []

    def get(self, name: str):
        return self._data.get(name)

    def save(self, snap: Snapshot):
        self._data[snap.name] = snap

    def delete(self, name: str):
        self._data.pop(name, None)
        self.deleted.append(name)


# ---------------------------------------------------------------------------
# BatchResult
# ---------------------------------------------------------------------------

def test_batch_result_all_succeeded_true():
    r = BatchResult(succeeded=["a", "b"])
    assert r.all_succeeded is True


def test_batch_result_all_succeeded_false():
    r = BatchResult(succeeded=["a"], failed=["b"], errors={"b": "oops"})
    assert r.all_succeeded is False


def test_batch_result_str_ok_only():
    r = BatchResult(succeeded=["x"])
    assert "OK" in str(r) and "x" in str(r)


def test_batch_result_str_empty():
    r = BatchResult()
    assert str(r) == "No operations performed"


def test_batch_result_all_succeeded_empty():
    """A result with no operations should not be considered all_succeeded."""
    r = BatchResult()
    assert r.all_succeeded is False


# ---------------------------------------------------------------------------
# batch_capture
# ---------------------------------------------------------------------------

def test_batch_capture_saves_all(monkeypatch):
    monkeypatch.setenv("BATCH_TEST_VAR", "hello")
    store = _FakeStore()
    result = batch_capture(store, ["snap1", "snap2"])
    assert result.all_succeeded
    assert store.get("snap1") is not None
    assert store.get("snap2") is not None


def test_batch_capture_partial_failure(monkeypatch):
    store = _FakeStore()
    # Force failure by making store.save raise for one name
    original_save = store.save
    def _bad_save(snap):
        if snap.name == "bad":
            raise RuntimeError("disk full")
        original_save(snap)
    store.save = _bad_save

    result = batch_capture(store, ["good", "bad"])
    assert "good" in result.succeeded
    assert "bad" in result.failed
    assert "disk full" in result.errors["bad"]


# ---------------------------------------------------------------------------
# batch_apply
# ---------------------------------------------------------------------------

def test_batch_apply_sets_env(monkeypatch):
    store = _FakeStore({"s1": _snap("s1", {"BA_KEY": "v1"}),
                        "s2": _snap("s2", {"BA_KEY2": "v2"})})
    monkeypatch.delenv("BA_KEY", raising=False)
    monkeypatch.delenv("BA_KEY2", raising=False)
    result = batch_apply(store, ["s1", "s2"])
    assert result.all_succeeded
    assert os.environ.get("BA_KEY") == "v1"
    assert os.environ.get("BA_KEY2") == "v2"


def test_batch_apply_missing_snapshot():
    """Applying a snapshot that does not exist should record a failure."""
    store = _FakeStore()
    result = batch_apply(store, ["nonexistent"])
    assert "nonexistent" in result.failed
    assert result.all_succeeded is False


# ---------------------------------------------------------------------------
# batch_delete
# ---------------------------------------------------------------------------

def test_batch_delete_removes_snapshots():
    store = _FakeStore({"d1": _snap("d1"), "d2": _snap("d2")})
    result = batch_delete(store, ["d1", "d2"])
    assert result.all_succeeded
    assert "d1" in store.deleted
    assert "d2" in store.deleted


def test_batch_delete_partial_failure():
    """A store error during delete should be captured as a failure."""
    store = _FakeStore({"ok": _snap("ok"), "bad": _snap("bad")})
    original_delete = store.delete
    def _bad_delete(name):
        if name == "bad":
            raise OSError("permission denied")
        original_delete(name)
    store.delete = _bad_delete

    result = batch_delete(store, ["ok", "bad"])
    assert "ok" in result.succeeded
    assert "bad" in result.failed
    assert "permission denied" in result.errors["bad"]
