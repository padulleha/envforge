"""Tests for envforge.cli_batch module."""
from __future__ import annotations

import argparse
import pytest

from envforge.cli_batch import cmd_batch_apply, cmd_batch_capture, cmd_batch_delete
from envforge.snapshot import Snapshot


def _snap(name: str, data: dict | None = None) -> Snapshot:
    return Snapshot(name=name, variables=data or {"K": "v"})


class _FakeStore:
    def __init__(self, snapshots=None):
        self._data: dict = dict(snapshots or {})
        self.saved: list = []
        self.deleted: list = []

    def get(self, name):
        return self._data.get(name)

    def save(self, snap):
        self._data[snap.name] = snap
        self.saved.append(snap.name)

    def delete(self, name):
        self._data.pop(name, None)
        self.deleted.append(name)


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"names": [], "keys": None, "no_overwrite": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# cmd_batch_capture
# ---------------------------------------------------------------------------

def test_cmd_batch_capture_success(monkeypatch, capsys):
    monkeypatch.setenv("CLI_BATCH_VAR", "x")
    store = _FakeStore()
    rc = cmd_batch_capture(_args(names=["a", "b"]), store)
    assert rc == 0
    assert "a" in store.saved and "b" in store.saved
    out = capsys.readouterr().out
    assert "[ok] captured 'a'" in out


def test_cmd_batch_capture_failure_reported(capsys):
    store = _FakeStore()
    original_save = store.save
    def _bad(snap):
        raise RuntimeError("boom")
    store.save = _bad
    rc = cmd_batch_capture(_args(names=["x"]), store)
    assert rc == 1
    out = capsys.readouterr().out
    assert "[error]" in out and "boom" in out


# ---------------------------------------------------------------------------
# cmd_batch_apply
# ---------------------------------------------------------------------------

def test_cmd_batch_apply_success(monkeypatch, capsys):
    monkeypatch.delenv("CLI_BA_K", raising=False)
    store = _FakeStore({"s": _snap("s", {"CLI_BA_K": "1"})})
    rc = cmd_batch_apply(_args(names=["s"]), store)
    assert rc == 0
    out = capsys.readouterr().out
    assert "[ok] applied 's'" in out


def test_cmd_batch_apply_missing(capsys):
    store = _FakeStore()
    rc = cmd_batch_apply(_args(names=["missing"]), store)
    assert rc == 1
    out = capsys.readouterr().out
    assert "[error]" in out


# ---------------------------------------------------------------------------
# cmd_batch_delete
# ---------------------------------------------------------------------------

def test_cmd_batch_delete_success(capsys):
    store = _FakeStore({"d": _snap("d")})
    rc = cmd_batch_delete(_args(names=["d"]), store)
    assert rc == 0
    assert "d" in store.deleted
    out = capsys.readouterr().out
    assert "[ok] deleted 'd'" in out


def test_cmd_batch_delete_missing(capsys):
    store = _FakeStore()
    rc = cmd_batch_delete(_args(names=["ghost"]), store)
    assert rc == 1
    out = capsys.readouterr().out
    assert "[error]" in out
