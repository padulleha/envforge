"""Tests for envforge.rename."""

from __future__ import annotations

import pytest

from envforge.rename import RenameError, RenameResult, rename_snapshot
from envforge.snapshot import Snapshot


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _snap(name: str, **vars_: str) -> Snapshot:
    s = Snapshot(name=name, variables=vars_)
    return s


class _FakeStore:
    """Minimal in-memory store compatible with rename_snapshot."""

    def __init__(self, snaps=None):
        self._data: dict[str, Snapshot] = {s.name: s for s in (snaps or [])}
        self.deleted: list[str] = []

    def get(self, name: str):
        return self._data.get(name)

    def save(self, snap: Snapshot):
        self._data[snap.name] = snap

    def delete(self, name: str):
        self._data.pop(name, None)
        self.deleted.append(name)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_rename_basic():
    store = _FakeStore([_snap("alpha", FOO="bar")])
    result = rename_snapshot(store, "alpha", "beta")
    assert result.success
    assert result.old_name == "alpha"
    assert result.new_name == "beta"
    assert store.get("beta") is not None
    assert store.get("alpha") is None
    assert "alpha" in store.deleted


def test_rename_preserves_variables():
    store = _FakeStore([_snap("alpha", KEY="value", OTHER="123")])
    rename_snapshot(store, "alpha", "beta")
    renamed = store.get("beta")
    assert renamed.variables["KEY"] == "value"
    assert renamed.variables["OTHER"] == "123"


def test_rename_missing_source_raises():
    store = _FakeStore()
    with pytest.raises(RenameError, match="not found"):
        rename_snapshot(store, "ghost", "new_name")


def test_rename_empty_new_name_raises():
    store = _FakeStore([_snap("alpha")])
    with pytest.raises(RenameError, match="non-empty"):
        rename_snapshot(store, "alpha", "   ")


def test_rename_same_name_is_noop():
    store = _FakeStore([_snap("alpha")])
    result = rename_snapshot(store, "alpha", "alpha")
    assert result.success
    assert "alpha" not in store.deleted


def test_rename_conflict_without_overwrite_raises():
    store = _FakeStore([_snap("alpha"), _snap("beta")])
    with pytest.raises(RenameError, match="already exists"):
        rename_snapshot(store, "alpha", "beta")


def test_rename_conflict_with_overwrite_succeeds():
    store = _FakeStore([_snap("alpha", A="1"), _snap("beta", B="2")])
    result = rename_snapshot(store, "alpha", "beta", overwrite=True)
    assert result.success
    assert store.get("beta").variables.get("A") == "1"


def test_rename_result_str_success():
    r = RenameResult("old", "new", True)
    assert "old" in str(r) and "new" in str(r)


def test_rename_result_str_failure():
    r = RenameResult("old", "new", False, "boom")
    assert "boom" in str(r)
