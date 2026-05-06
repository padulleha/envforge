"""Tests for envforge.cli_alias CLI commands."""

import argparse
import json
import os
import pytest

from envforge.store import SnapshotStore
from envforge.cli_alias import (
    cmd_alias_add,
    cmd_alias_remove,
    cmd_alias_list,
    cmd_alias_resolve,
)


@pytest.fixture
def tmp_store(tmp_path):
    path = tmp_path / "store.json"
    store = SnapshotStore(str(path))
    return store


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"alias": "prod", "snapshot": "production-2024", "description": ""}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_alias_add_creates_alias(tmp_store, capsys):
    args = _make_args(alias="prod", snapshot="production-2024", description="")
    rc = cmd_alias_add(args, tmp_store)
    assert rc == 0
    out = capsys.readouterr().out
    assert "prod" in out
    assert "production-2024" in out


def test_alias_add_persists(tmp_store):
    args = _make_args(alias="dev", snapshot="dev-local", description="")
    cmd_alias_add(args, tmp_store)
    aliases = tmp_store.meta.get("aliases", [])
    assert any(a["alias"] == "dev" for a in aliases)


def test_alias_add_empty_name_returns_error(tmp_store, capsys):
    args = _make_args(alias="", snapshot="snap")
    rc = cmd_alias_add(args, tmp_store)
    assert rc == 1
    assert "Error" in capsys.readouterr().err


def test_alias_remove_existing(tmp_store, capsys):
    cmd_alias_add(_make_args(alias="prod", snapshot="production-2024"), tmp_store)
    rc = cmd_alias_remove(argparse.Namespace(alias="prod"), tmp_store)
    assert rc == 0
    aliases = tmp_store.meta.get("aliases", [])
    assert not any(a["alias"] == "prod" for a in aliases)


def test_alias_remove_missing_returns_error(tmp_store, capsys):
    rc = cmd_alias_remove(argparse.Namespace(alias="ghost"), tmp_store)
    assert rc == 1
    assert "Error" in capsys.readouterr().err


def test_alias_list_empty(tmp_store, capsys):
    rc = cmd_alias_list(argparse.Namespace(), tmp_store)
    assert rc == 0
    assert "no aliases" in capsys.readouterr().out


def test_alias_list_shows_entries(tmp_store, capsys):
    cmd_alias_add(_make_args(alias="prod", snapshot="production-2024"), tmp_store)
    cmd_alias_list(argparse.Namespace(), tmp_store)
    out = capsys.readouterr().out
    assert "prod" in out
    assert "production-2024" in out


def test_alias_resolve_found(tmp_store, capsys):
    cmd_alias_add(_make_args(alias="prod", snapshot="production-2024"), tmp_store)
    rc = cmd_alias_resolve(argparse.Namespace(alias="prod"), tmp_store)
    assert rc == 0
    assert "production-2024" in capsys.readouterr().out


def test_alias_resolve_missing(tmp_store, capsys):
    rc = cmd_alias_resolve(argparse.Namespace(alias="ghost"), tmp_store)
    assert rc == 1
    assert "Error" in capsys.readouterr().err
