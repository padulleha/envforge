"""Tests for envforge.cli_score."""
from __future__ import annotations

import argparse
from unittest.mock import MagicMock

import pytest

from envforge.cli_score import cmd_score, register_score_commands
from envforge.snapshot import Snapshot


def _snap(name: str, variables: dict | None = None) -> Snapshot:
    return Snapshot(name=name, variables=variables or {"KEY": "val"})


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"names": [], "verbose": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _make_store(*snaps: Snapshot):
    store = MagicMock()
    store.list.return_value = [s.name for s in snaps]
    store.get.side_effect = lambda name: next((s for s in snaps if s.name == name), None)
    return store


# --- register ---

def test_register_adds_score_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    register_score_commands(sub)
    args = parser.parse_args(["score"])
    assert hasattr(args, "func")


def test_register_verbose_flag():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    register_score_commands(sub)
    args = parser.parse_args(["score", "-v"])
    assert args.verbose is True


# --- cmd_score ---

def test_score_no_snapshots_returns_error(capsys):
    store = _make_store()
    args = _make_args()
    rc = cmd_score(args, store)
    assert rc == 1
    captured = capsys.readouterr()
    assert "No snapshots" in captured.err


def test_score_single_snapshot_prints_summary(capsys):
    snap = _snap("mysnap")
    store = _make_store(snap)
    args = _make_args()
    rc = cmd_score(args, store)
    assert rc == 0
    out = capsys.readouterr().out
    assert "mysnap" in out


def test_score_explicit_names(capsys):
    snap = _snap("alpha")
    store = _make_store(snap)
    args = _make_args(names=["alpha"])
    rc = cmd_score(args, store)
    assert rc == 0
    assert "alpha" in capsys.readouterr().out


def test_score_missing_name_warns(capsys):
    store = _make_store()
    store.list.return_value = []
    args = _make_args(names=["ghost"])
    store.get.return_value = None
    rc = cmd_score(args, store)
    assert rc == 1
    assert "ghost" in capsys.readouterr().err


def test_score_verbose_shows_breakdown(capsys):
    snap = _snap("s1")
    store = _make_store(snap)
    args = _make_args(verbose=True)
    rc = cmd_score(args, store)
    assert rc == 0
    out = capsys.readouterr().out
    assert "Keys" in out


def test_score_sorted_by_score_descending(capsys):
    low = Snapshot(name="low", variables={})
    high = Snapshot(name="high", variables={f"K{i}": str(i) for i in range(20)})
    store = _make_store(low, high)
    args = _make_args()
    cmd_score(args, store)
    out = capsys.readouterr().out
    assert out.index("high") < out.index("low")
