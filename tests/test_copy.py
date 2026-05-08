"""Tests for envforge.copy and envforge.cli_copy."""

from __future__ import annotations

import argparse
import pytest

from envforge.snapshot import Snapshot
from envforge.copy import CopyError, CopyResult, copy_snapshot
from envforge.cli_copy import cmd_copy


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _snap(name: str, vars: dict | None = None, tags: list | None = None) -> Snapshot:
    s = Snapshot(name=name, variables=vars or {"KEY": "val"})
    if tags:
        s.tags = tags
    return s


class _FakeStore:
    def __init__(self, snaps=None):
        self._snaps: dict[str, Snapshot] = {s.name: s for s in (snaps or [])}

    def get(self, name: str):
        return self._snaps.get(name)

    def save(self, snap: Snapshot):
        self._snaps[snap.name] = snap


# ---------------------------------------------------------------------------
# copy_snapshot unit tests
# ---------------------------------------------------------------------------

def test_copy_creates_new_snapshot():
    store = _FakeStore([_snap("prod")])
    result = copy_snapshot(store, "prod", "prod-backup")
    assert store.get("prod-backup") is not None
    assert isinstance(result, CopyResult)
    assert result.source_name == "prod"
    assert result.dest_name == "prod-backup"
    assert result.overwritten is False


def test_copy_preserves_variables():
    store = _FakeStore([_snap("prod", vars={"A": "1", "B": "2"})])
    copy_snapshot(store, "prod", "staging")
    assert store.get("staging").variables == {"A": "1", "B": "2"}


def test_copy_assigns_correct_name():
    store = _FakeStore([_snap("alpha")])
    copy_snapshot(store, "alpha", "beta")
    assert store.get("beta").name == "beta"


def test_copy_missing_source_raises():
    store = _FakeStore()
    with pytest.raises(CopyError, match="not found"):
        copy_snapshot(store, "ghost", "dest")


def test_copy_same_name_raises():
    store = _FakeStore([_snap("env")])
    with pytest.raises(CopyError, match="must differ"):
        copy_snapshot(store, "env", "env")


def test_copy_dest_exists_no_overwrite_raises():
    store = _FakeStore([_snap("a"), _snap("b")])
    with pytest.raises(CopyError, match="already exists"):
        copy_snapshot(store, "a", "b")


def test_copy_dest_exists_with_overwrite_succeeds():
    store = _FakeStore([_snap("a", vars={"X": "new"}), _snap("b", vars={"X": "old"})])
    result = copy_snapshot(store, "a", "b", overwrite=True)
    assert result.overwritten is True
    assert store.get("b").variables == {"X": "new"}


def test_copy_adds_tag():
    store = _FakeStore([_snap("src")])
    copy_snapshot(store, "src", "dst", tag="backup")
    assert "backup" in store.get("dst").tags


def test_copy_preserves_existing_tags():
    src = _snap("src", tags=["prod"])
    store = _FakeStore([src])
    copy_snapshot(store, "src", "dst", tag="copy")
    tags = store.get("dst").tags
    assert "prod" in tags
    assert "copy" in tags


def test_copy_result_str_created():
    r = CopyResult(source_name="a", dest_name="b", overwritten=False)
    assert "created" in str(r)


def test_copy_result_str_overwritten():
    r = CopyResult(source_name="a", dest_name="b", overwritten=True)
    assert "overwritten" in str(r)


# ---------------------------------------------------------------------------
# cmd_copy CLI tests
# ---------------------------------------------------------------------------

def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"source": "src", "dest": "dst", "overwrite": False, "tag": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_copy_success(capsys):
    store = _FakeStore([_snap("src")])
    rc = cmd_copy(_make_args(), store)
    assert rc == 0
    out = capsys.readouterr().out
    assert "src" in out and "dst" in out


def test_cmd_copy_error_returns_1(capsys):
    store = _FakeStore()  # source missing
    rc = cmd_copy(_make_args(), store)
    assert rc == 1
    assert "Error" in capsys.readouterr().out
