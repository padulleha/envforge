"""Tests for envforge.cli_chain module."""
import json
import types
from pathlib import Path

import pytest

from envforge.chain import SnapshotChain
from envforge.cli_chain import (
    _chains_path,
    _load_chains,
    _save_chains,
    cmd_chain_add,
    cmd_chain_list,
    cmd_chain_remove,
    cmd_chain_apply,
)


@pytest.fixture()
def tmp_store(tmp_path):
    store_file = tmp_path / "store.json"
    store_file.write_text("{}")

    class FakeStore:
        path = str(store_file)
        _snaps = {}

        def get(self, name):
            return self._snaps.get(name)

    return FakeStore()


def _make_args(store, **kwargs):
    ns = types.SimpleNamespace()
    ns._store = store
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def _get_store_patch(store):
    """Return a patcher that makes get_store return store."""
    import envforge.cli_chain as mod
    original = None

    class Ctx:
        def __enter__(self):
            nonlocal original
            import envforge.cli as cli_mod
            original = cli_mod.get_store
            cli_mod.get_store = lambda _: store
            return self

        def __exit__(self, *a):
            import envforge.cli as cli_mod
            cli_mod.get_store = original

    return Ctx()


def test_chain_add_creates_file(tmp_store):
    args = _make_args(tmp_store, chain_name="ci", steps=["snap1", "snap2"], description="")
    with _get_store_patch(tmp_store):
        rc = cmd_chain_add(args)
    assert rc == 0
    chains = _load_chains(tmp_store.path)
    assert len(chains) == 1
    assert chains[0].name == "ci"


def test_chain_add_empty_name_returns_error(tmp_store):
    args = _make_args(tmp_store, chain_name="", steps=["s1"], description="")
    with _get_store_patch(tmp_store):
        rc = cmd_chain_add(args)
    assert rc == 1


def test_chain_remove_existing(tmp_store):
    chain = SnapshotChain(name="ci", steps=["s1"])
    _save_chains(tmp_store.path, [chain])
    args = _make_args(tmp_store, chain_name="ci")
    with _get_store_patch(tmp_store):
        rc = cmd_chain_remove(args)
    assert rc == 0
    assert _load_chains(tmp_store.path) == []


def test_chain_remove_missing_returns_error(tmp_store):
    args = _make_args(tmp_store, chain_name="ghost")
    with _get_store_patch(tmp_store):
        rc = cmd_chain_remove(args)
    assert rc == 1


def test_chain_list_empty(tmp_store, capsys):
    args = _make_args(tmp_store)
    with _get_store_patch(tmp_store):
        rc = cmd_chain_list(args)
    assert rc == 0
    assert "No chains" in capsys.readouterr().out


def test_chain_list_shows_entries(tmp_store, capsys):
    chains = [SnapshotChain(name="deploy", steps=["a", "b"])]
    _save_chains(tmp_store.path, chains)
    args = _make_args(tmp_store)
    with _get_store_patch(tmp_store):
        cmd_chain_list(args)
    out = capsys.readouterr().out
    assert "deploy" in out


def test_chain_apply_missing_chain_returns_error(tmp_store):
    args = _make_args(tmp_store, chain_name="nope", no_overwrite=False)
    with _get_store_patch(tmp_store):
        rc = cmd_chain_apply(args)
    assert rc == 1


def test_chain_apply_missing_snapshot_returns_error(tmp_store):
    chain = SnapshotChain(name="c", steps=["missing_snap"])
    _save_chains(tmp_store.path, [chain])
    args = _make_args(tmp_store, chain_name="c", no_overwrite=False)
    with _get_store_patch(tmp_store):
        rc = cmd_chain_apply(args)
    assert rc == 1
