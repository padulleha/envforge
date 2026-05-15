"""Tests for envforge.cli_bookmark."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from envforge.snapshot import Snapshot
from envforge.cli_bookmark import (
    cmd_bookmark_add,
    cmd_bookmark_list,
    cmd_bookmark_remove,
    cmd_bookmark_show,
)


class _FakeStore:
    def __init__(self, snaps=None):
        self._snaps = snaps or {}

    def get(self, name):
        return self._snaps.get(name)


def _snap(name="snap", vars=None):
    s = Snapshot(name=name, variables=vars or {"A": "1", "B": "2"})
    return s


def _make_args(tmp_path, **kwargs):
    store_file = tmp_path / "store.json"
    store_file.write_text("{}")
    defaults = {"store": str(store_file)}
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_bookmark_add_creates_file(tmp_path):
    store = _FakeStore({"snap": _snap()})
    args = _make_args(tmp_path, name="bm1", snapshot="snap", keys=["A"], description="")
    rc = cmd_bookmark_add(args, store)
    assert rc == 0
    bm_file = tmp_path / "bookmarks.json"
    assert bm_file.exists()
    data = json.loads(bm_file.read_text())
    assert data[0]["name"] == "bm1"


def test_bookmark_add_missing_snapshot_returns_error(tmp_path):
    store = _FakeStore({})
    args = _make_args(tmp_path, name="bm1", snapshot="missing", keys=["A"], description="")
    rc = cmd_bookmark_add(args, store)
    assert rc == 1


def test_bookmark_add_defaults_to_all_keys(tmp_path):
    store = _FakeStore({"snap": _snap(vars={"X": "1", "Y": "2", "Z": "3"})})
    args = _make_args(tmp_path, name="bm1", snapshot="snap", keys=None, description="")
    rc = cmd_bookmark_add(args, store)
    assert rc == 0
    bm_file = tmp_path / "bookmarks.json"
    data = json.loads(bm_file.read_text())
    assert set(data[0]["keys"]) == {"X", "Y", "Z"}


def test_bookmark_remove_existing(tmp_path):
    store = _FakeStore({"snap": _snap()})
    args_add = _make_args(tmp_path, name="bm1", snapshot="snap", keys=["A"], description="")
    cmd_bookmark_add(args_add, store)
    args_rm = _make_args(tmp_path, name="bm1")
    rc = cmd_bookmark_remove(args_rm, store)
    assert rc == 0
    bm_file = tmp_path / "bookmarks.json"
    data = json.loads(bm_file.read_text())
    assert data == []


def test_bookmark_remove_missing_returns_error(tmp_path):
    store = _FakeStore({})
    args = _make_args(tmp_path, name="ghost")
    rc = cmd_bookmark_remove(args, store)
    assert rc == 1


def test_bookmark_show_existing(tmp_path, capsys):
    store = _FakeStore({"snap": _snap()})
    args_add = _make_args(tmp_path, name="bm1", snapshot="snap", keys=["A", "B"], description="my desc")
    cmd_bookmark_add(args_add, store)
    args_show = _make_args(tmp_path, name="bm1")
    rc = cmd_bookmark_show(args_show, store)
    assert rc == 0
    out = capsys.readouterr().out
    assert "bm1" in out
    assert "snap" in out


def test_bookmark_show_missing_returns_error(tmp_path):
    store = _FakeStore({})
    args = _make_args(tmp_path, name="nope")
    rc = cmd_bookmark_show(args, store)
    assert rc == 1


def test_bookmark_list_empty(tmp_path, capsys):
    store = _FakeStore({})
    args = _make_args(tmp_path, snapshot=None)
    rc = cmd_bookmark_list(args, store)
    assert rc == 0
    assert "No bookmarks" in capsys.readouterr().out


def test_bookmark_list_filter_by_snapshot(tmp_path, capsys):
    store = _FakeStore({"s1": _snap("s1"), "s2": _snap("s2")})
    cmd_bookmark_add(_make_args(tmp_path, name="b1", snapshot="s1", keys=["A"], description=""), store)
    cmd_bookmark_add(_make_args(tmp_path, name="b2", snapshot="s2", keys=["A"], description=""), store)
    args = _make_args(tmp_path, snapshot="s1")
    rc = cmd_bookmark_list(args, store)
    assert rc == 0
    out = capsys.readouterr().out
    assert "b1" in out
    assert "b2" not in out
