"""Tests for envforge.cli_pin commands."""

import argparse
import pytest

from envforge.snapshot import Snapshot
from envforge.store import SnapshotStore
from envforge.cli_pin import (
    cmd_pin_add,
    cmd_pin_remove,
    cmd_pin_list,
    cmd_pin_apply,
    register_pin_commands,
)


@pytest.fixture
def tmp_store(tmp_path):
    return SnapshotStore(str(tmp_path / "store.json"))


def _make_args(store, **kwargs):
    ns = argparse.Namespace(store=store._path, **kwargs)
    return ns


def _make_snap(name, vars=None):
    snap = Snapshot(name=name, vars=vars or {"FOO": "original"})
    return snap


def test_pin_add_creates_pin(tmp_store, capsys):
    snap = _make_snap("mysnap")
    tmp_store.save(snap)
    args = _make_args(tmp_store, name="mysnap", key="FOO", value="pinned", reason="")
    cmd_pin_add(args)
    updated = tmp_store.get("mysnap")
    assert updated.metadata["pins"][0]["key"] == "FOO"
    assert updated.metadata["pins"][0]["value"] == "pinned"


def test_pin_add_missing_snapshot(tmp_store, capsys):
    args = _make_args(tmp_store, name="ghost", key="K", value="v", reason="")
    cmd_pin_add(args)
    out = capsys.readouterr().out
    assert "not found" in out


def test_pin_remove_existing(tmp_store, capsys):
    snap = _make_snap("mysnap")
    snap.metadata["pins"] = [{"key": "FOO", "value": "pinned", "reason": ""}]
    tmp_store.save(snap)
    args = _make_args(tmp_store, name="mysnap", key="FOO")
    cmd_pin_remove(args)
    updated = tmp_store.get("mysnap")
    assert updated.metadata["pins"] == []


def test_pin_remove_missing_key(tmp_store, capsys):
    snap = _make_snap("mysnap")
    snap.metadata["pins"] = []
    tmp_store.save(snap)
    args = _make_args(tmp_store, name="mysnap", key="MISSING")
    cmd_pin_remove(args)
    out = capsys.readouterr().out
    assert "MISSING" in out


def test_pin_list_output(tmp_store, capsys):
    snap = _make_snap("mysnap")
    snap.metadata["pins"] = [{"key": "FOO", "value": "bar", "reason": "test"}]
    tmp_store.save(snap)
    args = _make_args(tmp_store, name="mysnap")
    cmd_pin_list(args)
    out = capsys.readouterr().out
    assert "FOO" in out
    assert "bar" in out


def test_pin_apply_updates_vars(tmp_store):
    snap = _make_snap("mysnap", vars={"FOO": "original"})
    snap.metadata["pins"] = [{"key": "FOO", "value": "pinned", "reason": ""}]
    tmp_store.save(snap)
    args = _make_args(tmp_store, name="mysnap")
    cmd_pin_apply(args)
    updated = tmp_store.get("mysnap")
    assert updated.vars["FOO"] == "pinned"


def test_pin_apply_no_pins(tmp_store, capsys):
    snap = _make_snap("mysnap")
    snap.metadata["pins"] = []
    tmp_store.save(snap)
    args = _make_args(tmp_store, name="mysnap")
    cmd_pin_apply(args)
    out = capsys.readouterr().out
    assert "No pins" in out


def test_register_pin_commands():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    register_pin_commands(sub)
    args = parser.parse_args(["pin-add", "mysnap", "FOO", "bar"])
    assert args.name == "mysnap"
    assert args.key == "FOO"
    assert args.value == "bar"
