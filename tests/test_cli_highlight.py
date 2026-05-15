"""Tests for envforge.cli_highlight."""
from __future__ import annotations

import argparse
import sys
from types import SimpleNamespace
from typing import Optional

import pytest

from envforge.snapshot import Snapshot
from envforge.cli_highlight import cmd_highlight, register_highlight_commands


def _snap(name: str = "mysnap", **kwargs: str) -> Snapshot:
    return Snapshot(name=name, variables=dict(kwargs))


class _FakeStore:
    def __init__(self, snap: Optional[Snapshot] = None):
        self._snap = snap

    def get(self, name: str) -> Optional[Snapshot]:
        if self._snap and self._snap.name == name:
            return self._snap
        return None


def _make_args(**kwargs) -> SimpleNamespace:
    defaults = dict(
        name="mysnap",
        pattern=["*"],
        case_sensitive=False,
        mask=False,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_highlight_missing_snapshot_returns_error(capsys):
    store = _FakeStore(snap=None)
    args = _make_args(name="ghost")
    rc = cmd_highlight(args, store)
    assert rc == 1
    captured = capsys.readouterr()
    assert "ghost" in captured.err


def test_highlight_no_patterns_returns_error(capsys):
    store = _FakeStore(snap=_snap("mysnap", FOO="bar"))
    args = _make_args(pattern=[])
    rc = cmd_highlight(args, store)
    assert rc == 1
    captured = capsys.readouterr()
    assert "pattern" in captured.err


def test_highlight_no_match_prints_summary(capsys):
    store = _FakeStore(snap=_snap("mysnap", FOO="bar"))
    args = _make_args(pattern=["NOTHING_*"])
    rc = cmd_highlight(args, store)
    assert rc == 0
    captured = capsys.readouterr()
    assert "no keys matched" in captured.out


def test_highlight_match_prints_key_value(capsys):
    store = _FakeStore(snap=_snap("mysnap", AWS_KEY="secret"))
    args = _make_args(pattern=["AWS_*"])
    rc = cmd_highlight(args, store)
    assert rc == 0
    captured = capsys.readouterr()
    assert "AWS_KEY" in captured.out
    assert "secret" in captured.out


def test_highlight_mask_hides_values(capsys):
    store = _FakeStore(snap=_snap("mysnap", DB_PASS="hunter2"))
    args = _make_args(pattern=["DB_*"], mask=True)
    rc = cmd_highlight(args, store)
    assert rc == 0
    captured = capsys.readouterr()
    assert "hunter2" not in captured.out
    assert "***" in captured.out


def test_register_highlight_commands_adds_subcommand():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers()
    register_highlight_commands(subs, get_store=lambda a: None)
    parsed = parser.parse_args(["highlight", "mysnap", "AWS_*"])
    assert parsed.name == "mysnap"
    assert parsed.pattern == ["AWS_*"]


def test_register_highlight_mask_flag():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers()
    register_highlight_commands(subs, get_store=lambda a: None)
    parsed = parser.parse_args(["highlight", "s", "*", "--mask"])
    assert parsed.mask is True


def test_register_highlight_case_sensitive_flag():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers()
    register_highlight_commands(subs, get_store=lambda a: None)
    parsed = parser.parse_args(["highlight", "s", "*", "--case-sensitive"])
    assert parsed.case_sensitive is True
