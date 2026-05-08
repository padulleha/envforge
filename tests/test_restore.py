"""Tests for envforge.restore and envforge.cli_restore."""

from __future__ import annotations

import argparse
import pytest

from envforge.snapshot import Snapshot
from envforge.restore import (
    RestoreError,
    RestoreResult,
    backup_snapshot,
    make_backup_name,
    restore_snapshot,
)
from envforge.cli_restore import cmd_backup, cmd_restore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeStore:
    def __init__(self, snaps=None):
        self._snaps: dict[str, Snapshot] = dict(snaps or {})
        self.saved: list[Snapshot] = []

    def get(self, name: str):
        return self._snaps.get(name)

    def save(self, snap: Snapshot):
        self._snaps[snap.name] = snap
        self.saved.append(snap)


def _snap(name: str, **vars_) -> Snapshot:
    return Snapshot(name=name, variables=vars_ or {"KEY": "val"})


# ---------------------------------------------------------------------------
# make_backup_name
# ---------------------------------------------------------------------------

def test_make_backup_name():
    assert make_backup_name("prod") == "prod.__backup__"


# ---------------------------------------------------------------------------
# backup_snapshot
# ---------------------------------------------------------------------------

def test_backup_snapshot_creates_copy():
    store = _FakeStore({"prod": _snap("prod", A="1", B="2")})
    backup_name = backup_snapshot(store, "prod")
    assert backup_name == "prod.__backup__"
    backup = store.get(backup_name)
    assert backup is not None
    assert backup.variables == {"A": "1", "B": "2"}


def test_backup_snapshot_missing_raises():
    store = _FakeStore()
    with pytest.raises(RestoreError, match="not found"):
        backup_snapshot(store, "missing")


# ---------------------------------------------------------------------------
# restore_snapshot
# ---------------------------------------------------------------------------

def test_restore_snapshot_overwrites_variables():
    original = _snap("prod", A="old")
    backup = _snap("prod.__backup__", A="new", B="extra")
    store = _FakeStore({"prod": original, "prod.__backup__": backup})
    result = restore_snapshot(store, "prod")
    assert isinstance(result, RestoreResult)
    assert result.keys_restored == 2
    restored = store.get("prod")
    assert restored.variables == {"A": "new", "B": "extra"}


def test_restore_snapshot_preserves_tags_and_description():
    original = Snapshot(name="prod", variables={}, tags=["live"], description="my desc")
    backup = _snap("prod.__backup__", X="1")
    store = _FakeStore({"prod": original, "prod.__backup__": backup})
    restore_snapshot(store, "prod")
    restored = store.get("prod")
    assert restored.tags == ["live"]
    assert restored.description == "my desc"


def test_restore_snapshot_explicit_backup_name():
    original = _snap("prod", A="old")
    custom = _snap("prod.v1", A="v1val")
    store = _FakeStore({"prod": original, "prod.v1": custom})
    result = restore_snapshot(store, "prod", backup_name="prod.v1")
    assert result.restored_from == "prod.v1"


def test_restore_snapshot_missing_backup_raises():
    store = _FakeStore({"prod": _snap("prod")})
    with pytest.raises(RestoreError, match="not found"):
        restore_snapshot(store, "prod")


# ---------------------------------------------------------------------------
# RestoreResult.__str__
# ---------------------------------------------------------------------------

def test_restore_result_str_contains_name_and_keys():
    result = RestoreResult(snapshot_name="prod", restored_from="prod.__backup__", keys_restored=5)
    text = str(result)
    assert "prod" in text
    assert "5 keys" in text


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def _make_args(**kwargs) -> argparse.Namespace:
    return argparse.Namespace(**kwargs)


def test_cmd_backup_success(capsys):
    store = _FakeStore({"dev": _snap("dev")})
    rc = cmd_backup(_make_args(name="dev"), store)
    assert rc == 0
    out = capsys.readouterr().out
    assert "dev.__backup__" in out


def test_cmd_backup_missing_snapshot(capsys):
    store = _FakeStore()
    rc = cmd_backup(_make_args(name="ghost"), store)
    assert rc == 1
    err = capsys.readouterr().err
    assert "Error" in err


def test_cmd_restore_success(capsys):
    store = _FakeStore({
        "dev": _snap("dev", A="old"),
        "dev.__backup__": _snap("dev.__backup__", A="new"),
    })
    rc = cmd_restore(_make_args(name="dev", from_backup=None), store)
    assert rc == 0
    out = capsys.readouterr().out
    assert "dev" in out


def test_cmd_restore_no_backup(capsys):
    store = _FakeStore({"dev": _snap("dev")})
    rc = cmd_restore(_make_args(name="dev", from_backup=None), store)
    assert rc == 1
