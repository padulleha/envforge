"""Tests for envforge.cli_history sub-commands."""

from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from envforge.history import HistoryEntry, SnapshotHistory
from envforge.cli_history import cmd_history_list, cmd_history_show, register_history_commands


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_args(store_dir: Path, **kwargs) -> argparse.Namespace:
    ns = argparse.Namespace(store=str(store_dir))
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def _make_history(*actions_names):
    h = SnapshotHistory()
    for action, name in actions_names:
        h.record(action, name)
    return h


# ---------------------------------------------------------------------------
# cmd_history_list
# ---------------------------------------------------------------------------

def test_history_list_empty(tmp_path, capsys):
    args = _make_args(tmp_path, limit=20)
    with patch("envforge.cli_history.get_store") as mock_gs:
        mock_store = MagicMock()
        mock_store.store_dir = tmp_path
        mock_gs.return_value = mock_store
        cmd_history_list(args)
    out = capsys.readouterr().out
    assert "No history" in out


def test_history_list_shows_entries(tmp_path, capsys):
    from envforge.store_history import save_history
    h = _make_history(("captured", "dev"), ("applied", "dev"))
    save_history(tmp_path, h)

    args = _make_args(tmp_path, limit=20)
    with patch("envforge.cli_history.get_store") as mock_gs:
        mock_store = MagicMock()
        mock_store.store_dir = tmp_path
        mock_gs.return_value = mock_store
        cmd_history_list(args)
    out = capsys.readouterr().out
    assert "captured" in out
    assert "applied" in out
    assert "dev" in out


def test_history_list_respects_limit(tmp_path, capsys):
    from envforge.store_history import save_history
    h = SnapshotHistory()
    for i in range(10):
        h.record("captured", f"snap{i}")
    save_history(tmp_path, h)

    args = _make_args(tmp_path, limit=3)
    with patch("envforge.cli_history.get_store") as mock_gs:
        mock_store = MagicMock()
        mock_store.store_dir = tmp_path
        mock_gs.return_value = mock_store
        cmd_history_list(args)
    out = capsys.readouterr().out
    assert out.count("captured") == 3


# ---------------------------------------------------------------------------
# cmd_history_show
# ---------------------------------------------------------------------------

def test_history_show_no_entries(tmp_path, capsys):
    args = _make_args(tmp_path, name="ghost")
    with patch("envforge.cli_history.get_store") as mock_gs:
        mock_store = MagicMock()
        mock_store.store_dir = tmp_path
        mock_gs.return_value = mock_store
        cmd_history_show(args)
    out = capsys.readouterr().out
    assert "ghost" in out


def test_history_show_filters_by_name(tmp_path, capsys):
    from envforge.store_history import save_history
    h = _make_history(("captured", "dev"), ("applied", "prod"), ("deleted", "dev"))
    save_history(tmp_path, h)

    args = _make_args(tmp_path, name="dev")
    with patch("envforge.cli_history.get_store") as mock_gs:
        mock_store = MagicMock()
        mock_store.store_dir = tmp_path
        mock_gs.return_value = mock_store
        cmd_history_show(args)
    out = capsys.readouterr().out
    assert "captured" in out
    assert "deleted" in out
    assert "prod" not in out


# ---------------------------------------------------------------------------
# register_history_commands
# ---------------------------------------------------------------------------

def test_register_history_commands_adds_parsers():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    register_history_commands(sub)
    args = parser.parse_args(["history", "--limit", "5"])
    assert args.limit == 5
    assert args.func is cmd_history_list
