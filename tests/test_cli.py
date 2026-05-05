"""Tests for the envforge CLI."""

import os
import json
import pytest
from unittest.mock import patch
from argparse import Namespace

from envforge.cli import build_parser, cmd_capture, cmd_apply, cmd_list, cmd_delete, cmd_show
from envforge.store import SnapshotStore
from envforge.snapshot import Snapshot


@pytest.fixture
def tmp_store(tmp_path):
    store_path = str(tmp_path / "snapshots.json")
    with patch("envforge.cli.get_store", return_value=SnapshotStore(store_path)):
        yield SnapshotStore(store_path)


def make_args(**kwargs):
    defaults = {"name": "test", "keys": None, "description": "", "no_overwrite": False, "mask": False}
    defaults.update(kwargs)
    return Namespace(**defaults)


def test_parser_capture():
    parser = build_parser()
    args = parser.parse_args(["capture", "mysnap", "--description", "hello"])
    assert args.command == "capture"
    assert args.name == "mysnap"
    assert args.description == "hello"


def test_parser_apply():
    parser = build_parser()
    args = parser.parse_args(["apply", "mysnap", "--no-overwrite"])
    assert args.command == "apply"
    assert args.no_overwrite is True


def test_parser_list():
    parser = build_parser()
    args = parser.parse_args(["list"])
    assert args.command == "list"


def test_cmd_capture_saves_snapshot(tmp_store, capsys):
    with patch("envforge.cli.get_store", return_value=tmp_store):
        args = make_args(name="snap1", keys=["PATH"])
        result = cmd_capture(args)
    assert result == 0
    assert tmp_store.get("snap1") is not None
    captured = capsys.readouterr()
    assert "snap1" in captured.out


def test_cmd_apply_missing_snapshot(tmp_store, capsys):
    with patch("envforge.cli.get_store", return_value=tmp_store):
        args = make_args(name="nonexistent")
        result = cmd_apply(args)
    assert result == 1
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_cmd_list_empty(tmp_store, capsys):
    with patch("envforge.cli.get_store", return_value=tmp_store):
        result = cmd_list(make_args())
    assert result == 0
    assert "No snapshots" in capsys.readouterr().out


def test_cmd_list_with_snapshots(tmp_store, capsys):
    snap = Snapshot.capture(name="proj1", keys=["PATH"])
    tmp_store.save(snap)
    with patch("envforge.cli.get_store", return_value=tmp_store):
        result = cmd_list(make_args())
    assert result == 0
    assert "proj1" in capsys.readouterr().out


def test_cmd_delete_existing(tmp_store, capsys):
    snap = Snapshot.capture(name="todelete", keys=["PATH"])
    tmp_store.save(snap)
    with patch("envforge.cli.get_store", return_value=tmp_store):
        result = cmd_delete(make_args(name="todelete"))
    assert result == 0
    assert tmp_store.get("todelete") is None


def test_cmd_show_masks_values(tmp_store, capsys):
    snap = Snapshot(name="secret", variables={"TOKEN": "abc123"})
    tmp_store.save(snap)
    with patch("envforge.cli.get_store", return_value=tmp_store):
        result = cmd_show(make_args(name="secret", mask=True))
    assert result == 0
    out = capsys.readouterr().out
    assert "abc123" not in out
    assert "***" in out
