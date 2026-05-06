"""Tests for envforge.cli_compare module."""
from __future__ import annotations

import argparse
import json
from unittest.mock import MagicMock

import pytest

from envforge.cli_compare import cmd_compare, register_compare_commands
from envforge.snapshot import Snapshot


def _snap(name: str, variables: dict) -> Snapshot:
    s = Snapshot(name=name)
    s.variables = dict(variables)
    return s


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "base": "snap-a",
        "other": "snap-b",
        "format": "text",
        "show_unchanged": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _make_store(base_snap, other_snap):
    store = MagicMock()
    store.get.side_effect = lambda name: {
        base_snap.name: base_snap,
        other_snap.name: other_snap,
    }.get(name)
    return store


def test_compare_missing_base(capsys):
    store = MagicMock()
    store.get.return_value = None
    args = _make_args(base="missing", other="snap-b")
    rc = cmd_compare(args, store)
    assert rc == 1
    captured = capsys.readouterr()
    assert "missing" in captured.err


def test_compare_missing_other(capsys):
    store = MagicMock()
    a = _snap("snap-a", {})
    store.get.side_effect = lambda n: a if n == "snap-a" else None
    args = _make_args(base="snap-a", other="missing")
    rc = cmd_compare(args, store)
    assert rc == 1


def test_compare_no_differences_returns_zero(capsys):
    a = _snap("snap-a", {"X": "1"})
    b = _snap("snap-b", {"X": "1"})
    store = _make_store(a, b)
    args = _make_args(base="snap-a", other="snap-b")
    rc = cmd_compare(args, store)
    assert rc == 0


def test_compare_with_differences_returns_two(capsys):
    a = _snap("snap-a", {"X": "1"})
    b = _snap("snap-b", {"X": "2"})
    store = _make_store(a, b)
    args = _make_args(base="snap-a", other="snap-b")
    rc = cmd_compare(args, store)
    assert rc == 2


def test_compare_text_output(capsys):
    a = _snap("snap-a", {"A": "old"})
    b = _snap("snap-b", {"A": "new", "B": "extra"})
    store = _make_store(a, b)
    args = _make_args(base="snap-a", other="snap-b", format="text")
    cmd_compare(args, store)
    out = capsys.readouterr().out
    assert "snap-a" in out
    assert "snap-b" in out


def test_compare_summary_format(capsys):
    a = _snap("snap-a", {"X": "1"})
    b = _snap("snap-b", {"X": "2"})
    store = _make_store(a, b)
    args = _make_args(base="snap-a", other="snap-b", format="summary")
    cmd_compare(args, store)
    out = capsys.readouterr().out
    assert "changed" in out


def test_compare_json_format(capsys):
    a = _snap("snap-a", {"X": "1"})
    b = _snap("snap-b", {"X": "1", "Y": "new"})
    store = _make_store(a, b)
    args = _make_args(base="snap-a", other="snap-b", format="json")
    cmd_compare(args, store)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["base"] == "snap-a"
    assert data["other"] == "snap-b"
    assert "Y" in data["added"]


def test_register_compare_commands():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    register_compare_commands(sub)
    args = parser.parse_args(["compare", "snap-a", "snap-b", "--format", "json"])
    assert args.base == "snap-a"
    assert args.other == "snap-b"
    assert args.format == "json"
