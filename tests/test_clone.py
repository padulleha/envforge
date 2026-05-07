"""Tests for envforge.clone."""

from __future__ import annotations

import pytest

from envforge.snapshot import Snapshot
from envforge.clone import CloneError, CloneResult, clone_snapshot


# ---------------------------------------------------------------------------
# Minimal fake store
# ---------------------------------------------------------------------------

class _FakeStore:
    def __init__(self, snapshots=None):
        self._data = {s.name: s for s in (snapshots or [])}

    def get(self, name):
        return self._data.get(name)

    def save(self, snap):
        self._data[snap.name] = snap


def _snap(name, vars=None, tags=None, description=""):
    return Snapshot(
        name=name,
        vars=vars or {"KEY": "val"},
        tags=tags or [],
        description=description,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_clone_copies_all_keys():
    store = _FakeStore([_snap("src", vars={"A": "1", "B": "2"})])
    result = clone_snapshot(store, "src", "dst")
    assert isinstance(result, CloneResult)
    assert set(result.keys_copied) == {"A", "B"}
    assert store.get("dst") is not None
    assert store.get("dst").vars == {"A": "1", "B": "2"}


def test_clone_copies_selected_keys():
    store = _FakeStore([_snap("src", vars={"A": "1", "B": "2", "C": "3"})])
    result = clone_snapshot(store, "src", "dst", keys=["A", "C"])
    assert result.keys_copied == ["A", "C"]
    assert store.get("dst").vars == {"A": "1", "C": "3"}


def test_clone_preserves_tags_and_description():
    src = _snap("src", tags=["prod", "web"], description="hello")
    store = _FakeStore([src])
    clone_snapshot(store, "src", "dst")
    dst = store.get("dst")
    assert dst.tags == ["prod", "web"]
    assert dst.description == "hello"


def test_clone_same_name_raises():
    store = _FakeStore([_snap("src")])
    with pytest.raises(CloneError, match="must differ"):
        clone_snapshot(store, "src", "src")


def test_clone_missing_source_raises():
    store = _FakeStore()
    with pytest.raises(CloneError, match="not found"):
        clone_snapshot(store, "ghost", "dst")


def test_clone_target_exists_raises_without_overwrite():
    store = _FakeStore([_snap("src"), _snap("dst")])
    with pytest.raises(CloneError, match="already exists"):
        clone_snapshot(store, "src", "dst")


def test_clone_target_exists_succeeds_with_overwrite():
    store = _FakeStore([_snap("src", vars={"X": "new"}), _snap("dst", vars={"X": "old"})])
    clone_snapshot(store, "src", "dst", overwrite=True)
    assert store.get("dst").vars == {"X": "new"}


def test_clone_missing_key_raises():
    store = _FakeStore([_snap("src", vars={"A": "1"})])
    with pytest.raises(CloneError, match="not present"):
        clone_snapshot(store, "src", "dst", keys=["A", "MISSING"])


def test_clone_result_str():
    result = CloneResult(source_name="src", target_name="dst", keys_copied=["A", "B"])
    text = str(result)
    assert "src" in text
    assert "dst" in text
    assert "2" in text
