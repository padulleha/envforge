"""Tests for envforge/clone_cli.py."""
from __future__ import annotations

import argparse
import pytest

from envforge.snapshot import Snapshot
from envforge.store import SnapshotStore
from envforge.clone_cli import cmd_clone, register_clone_commands


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _snap(name: str, vars: dict | None = None) -> Snapshot:
    s = Snapshot(name=name, variables=vars or {"KEY": "val"})
    return s


def _make_args(tmp_path, **kwargs) -> argparse.Namespace:
    defaults = dict(
        store_path=str(tmp_path / "store.json"),
        source="base",
        dest="copy",
        overwrite=False,
        tag=None,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


@pytest.fixture()
def tmp_store(tmp_path):
    store = SnapshotStore(str(tmp_path / "store.json"))
    store.save(_snap("base", {"FOO": "bar", "BAZ": "qux"}))
    return store, tmp_path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_clone_creates_new_snapshot(tmp_store):
    store, tmp_path = tmp_store
    args = _make_args(tmp_path, source="base", dest="copy")
    rc = cmd_clone(args)
    assert rc == 0
    cloned = store.get("copy")
    assert cloned is not None
    assert cloned.variables == {"FOO": "bar", "BAZ": "qux"}


def test_clone_missing_source_returns_error(tmp_store):
    store, tmp_path = tmp_store
    args = _make_args(tmp_path, source="nonexistent", dest="copy")
    rc = cmd_clone(args)
    assert rc == 1


def test_clone_dest_exists_without_overwrite_returns_error(tmp_store):
    store, tmp_path = tmp_store
    store.save(_snap("copy", {"X": "1"}))
    args = _make_args(tmp_path, source="base", dest="copy", overwrite=False)
    rc = cmd_clone(args)
    assert rc == 1


def test_clone_dest_exists_with_overwrite_succeeds(tmp_store):
    store, tmp_path = tmp_store
    store.save(_snap("copy", {"X": "1"}))
    args = _make_args(tmp_path, source="base", dest="copy", overwrite=True)
    rc = cmd_clone(args)
    assert rc == 0
    cloned = store.get("copy")
    assert cloned.variables == {"FOO": "bar", "BAZ": "qux"}


def test_clone_with_tag_applies_tag(tmp_store):
    store, tmp_path = tmp_store
    args = _make_args(tmp_path, source="base", dest="tagged_copy", tag="prod")
    rc = cmd_clone(args)
    assert rc == 0
    cloned = store.get("tagged_copy")
    assert "prod" in (cloned.tags or [])


def test_register_clone_commands_adds_subparser():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    register_clone_commands(sub)
    args = parser.parse_args(["clone", "src", "dst"])
    assert args.source == "src"
    assert args.dest == "dst"
    assert args.overwrite is False
    assert args.tag is None
