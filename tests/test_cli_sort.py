"""Tests for envforge.cli_sort."""
from __future__ import annotations

import argparse
from unittest.mock import MagicMock, patch

import pytest

from envforge.cli_sort import cmd_sort, register_sort_commands
from envforge.snapshot import Snapshot
from envforge.snapshot_sort import SortKey, SortOrder


def _snap(name: str, variables: dict | None = None, description: str = "") -> Snapshot:
    s = Snapshot(name=name, variables=variables or {}, description=description)
    s.created_at = "2024-01-01"
    return s


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = dict(store=None, sort_key=SortKey.NAME.value, order=SortOrder.ASC.value)
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _make_store(*snaps: Snapshot):
    store = MagicMock()
    store.list.return_value = [s.name for s in snaps]
    store.get.side_effect = lambda name: next((s for s in snaps if s.name == name), None)
    return store


def test_sort_empty_store(capsys):
    store = _make_store()
    with patch("envforge.cli_sort.get_store", return_value=store):
        rc = cmd_sort(_make_args())
    assert rc == 0
    out = capsys.readouterr().out
    assert "No snapshots" in out


def test_sort_lists_names(capsys):
    snaps = [_snap("zebra"), _snap("alpha"), _snap("mango")]
    store = _make_store(*snaps)
    with patch("envforge.cli_sort.get_store", return_value=store):
        rc = cmd_sort(_make_args())
    assert rc == 0
    out = capsys.readouterr().out
    lines = [l for l in out.splitlines() if l.strip()]
    name_lines = [l for l in lines if any(s.name in l for s in snaps)]
    names_in_order = [l.split()[0].strip() for l in name_lines]
    assert names_in_order == ["alpha", "mango", "zebra"]


def test_sort_by_key_count_desc(capsys):
    snaps = [
        _snap("small", {"A": "1"}),
        _snap("big", {"A": "1", "B": "2", "C": "3"}),
    ]
    store = _make_store(*snaps)
    args = _make_args(sort_key=SortKey.KEY_COUNT.value, order=SortOrder.DESC.value)
    with patch("envforge.cli_sort.get_store", return_value=store):
        rc = cmd_sort(args)
    assert rc == 0
    out = capsys.readouterr().out
    idx_big = out.index("big")
    idx_small = out.index("small")
    assert idx_big < idx_small


def test_sort_invalid_key_returns_error(capsys):
    store = _make_store(_snap("a"))
    args = _make_args(sort_key="invalid_key")
    with patch("envforge.cli_sort.get_store", return_value=store):
        rc = cmd_sort(args)
    assert rc == 1
    assert "Error" in capsys.readouterr().out


def test_sort_invalid_order_returns_error(capsys):
    store = _make_store(_snap("a"))
    args = _make_args(order="sideways")
    with patch("envforge.cli_sort.get_store", return_value=store):
        rc = cmd_sort(args)
    assert rc == 1


def test_register_sort_commands():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    register_sort_commands(subparsers)
    parsed = parser.parse_args(["sort", "--key", "key_count", "--order", "desc"])
    assert parsed.sort_key == "key_count"
    assert parsed.order == "desc"
