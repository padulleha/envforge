"""Tests for envforge.cli_rename."""

from __future__ import annotations

import argparse

import pytest

from envforge.cli_rename import cmd_rename, register_rename_commands
from envforge.snapshot import Snapshot


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _snap(name: str, **vars_: str) -> Snapshot:
    return Snapshot(name=name, variables=vars_)


class _FakeStore:
    def __init__(self, snaps=None):
        self._data: dict[str, Snapshot] = {s.name: s for s in (snaps or [])}

    def get(self, name):
        return self._data.get(name)

    def save(self, snap):
        self._data[snap.name] = snap

    def delete(self, name):
        self._data.pop(name, None)


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"old_name": "alpha", "new_name": "beta", "overwrite": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_cmd_rename_success(capsys):
    store = _FakeStore([_snap("alpha", X="1")])
    rc = cmd_rename(_make_args(), store)
    assert rc == 0
    out = capsys.readouterr().out
    assert "alpha" in out and "beta" in out


def test_cmd_rename_missing_source_returns_error(capsys):
    store = _FakeStore()
    rc = cmd_rename(_make_args(old_name="ghost"), store)
    assert rc == 1
    assert "Error" in capsys.readouterr().out


def test_cmd_rename_conflict_no_overwrite_returns_error(capsys):
    store = _FakeStore([_snap("alpha"), _snap("beta")])
    rc = cmd_rename(_make_args(), store)
    assert rc == 1


def test_cmd_rename_conflict_overwrite_succeeds(capsys):
    store = _FakeStore([_snap("alpha", A="1"), _snap("beta", B="2")])
    rc = cmd_rename(_make_args(overwrite=True), store)
    assert rc == 0


def test_register_rename_commands():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    register_rename_commands(sub)
    args = parser.parse_args(["rename", "src", "dst"])
    assert args.old_name == "src"
    assert args.new_name == "dst"
    assert args.overwrite is False


def test_register_rename_commands_overwrite_flag():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    register_rename_commands(sub)
    args = parser.parse_args(["rename", "src", "dst", "--overwrite"])
    assert args.overwrite is True
