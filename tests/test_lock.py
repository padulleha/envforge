"""Tests for envforge.lock and envforge.cli_lock."""
from __future__ import annotations

import argparse
import json
import pytest
from pathlib import Path

from envforge.lock import (
    LockedSnapshot,
    add_lock,
    remove_lock,
    is_locked,
    get_lock,
    format_locks,
)
from envforge.cli_lock import (
    _locks_path,
    _load_locks,
    _save_locks,
    cmd_lock_add,
    cmd_lock_remove,
    cmd_lock_list,
)


# ---------------------------------------------------------------------------
# Unit tests for lock.py
# ---------------------------------------------------------------------------

def test_locked_snapshot_roundtrip():
    lk = LockedSnapshot(name="prod", reason="stable release")
    assert LockedSnapshot.from_dict(lk.to_dict()) == lk


def test_locked_snapshot_defaults():
    lk = LockedSnapshot.from_dict({"name": "dev"})
    assert lk.reason is None


def test_add_lock_new():
    locks = add_lock([], "prod", reason="do not touch")
    assert len(locks) == 1
    assert locks[0].name == "prod"
    assert locks[0].reason == "do not touch"


def test_add_lock_updates_existing():
    locks = add_lock([], "prod", reason="v1")
    locks = add_lock(locks, "prod", reason="v2")
    assert len(locks) == 1
    assert locks[0].reason == "v2"


def test_add_lock_sorted():
    locks = add_lock([], "zebra")
    locks = add_lock(locks, "alpha")
    assert locks[0].name == "alpha"
    assert locks[1].name == "zebra"


def test_add_lock_empty_name_raises():
    with pytest.raises(ValueError):
        add_lock([], "")


def test_remove_lock_present():
    locks = add_lock([], "prod")
    locks = remove_lock(locks, "prod")
    assert locks == []


def test_remove_lock_absent_is_noop():
    locks = add_lock([], "prod")
    result = remove_lock(locks, "staging")
    assert len(result) == 1


def test_is_locked_true_and_false():
    locks = add_lock([], "prod")
    assert is_locked(locks, "prod") is True
    assert is_locked(locks, "dev") is False


def test_get_lock_returns_entry():
    locks = add_lock([], "prod", reason="stable")
    entry = get_lock(locks, "prod")
    assert entry is not None
    assert entry.reason == "stable"


def test_get_lock_missing_returns_none():
    assert get_lock([], "missing") is None


def test_format_locks_empty():
    assert "no locked" in format_locks([])


def test_format_locks_shows_name_and_reason():
    locks = add_lock([], "prod", reason="stable")
    text = format_locks(locks)
    assert "prod" in text
    assert "stable" in text


# ---------------------------------------------------------------------------
# CLI integration tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_store(tmp_path: Path) -> str:
    store_file = tmp_path / "store.json"
    store_file.write_text("{}")
    return str(store_file)


def _make_args(store: str, **kwargs) -> argparse.Namespace:
    return argparse.Namespace(store=store, **kwargs)


def test_cmd_lock_add_creates_lock(tmp_store):
    args = _make_args(tmp_store, name="prod", reason=None)
    rc = cmd_lock_add(args)
    assert rc == 0
    locks = _load_locks(tmp_store)
    assert is_locked(locks, "prod")


def test_cmd_lock_add_already_locked(tmp_store):
    args = _make_args(tmp_store, name="prod", reason=None)
    cmd_lock_add(args)
    rc = cmd_lock_add(args)
    assert rc == 1


def test_cmd_lock_remove_unlocks(tmp_store):
    add_args = _make_args(tmp_store, name="prod", reason=None)
    cmd_lock_add(add_args)
    rm_args = _make_args(tmp_store, name="prod")
    rc = cmd_lock_remove(rm_args)
    assert rc == 0
    assert not is_locked(_load_locks(tmp_store), "prod")


def test_cmd_lock_remove_not_locked(tmp_store):
    args = _make_args(tmp_store, name="ghost")
    rc = cmd_lock_remove(args)
    assert rc == 1


def test_cmd_lock_list_empty(tmp_store, capsys):
    args = _make_args(tmp_store)
    cmd_lock_list(args)
    out = capsys.readouterr().out
    assert "no locked" in out


def test_cmd_lock_list_shows_entry(tmp_store, capsys):
    add_args = _make_args(tmp_store, name="prod", reason="stable")
    cmd_lock_add(add_args)
    cmd_lock_list(_make_args(tmp_store))
    out = capsys.readouterr().out
    assert "prod" in out
