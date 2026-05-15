"""Tests for envforge.cli_label."""
import json
import types
from pathlib import Path

import pytest

from envforge.snapshot_label import LabelSet
from envforge.cli_label import (
    _labels_path,
    _load_labels,
    _save_labels,
    cmd_label_add,
    cmd_label_remove,
    cmd_label_list,
    cmd_label_filter,
)


# ── helpers ──────────────────────────────────────────────────────────────────

class _FakeStore:
    def __init__(self, tmp_path: Path):
        self.path = str(tmp_path / "store.json")
        Path(self.path).touch()


def _make_args(**kwargs):
    ns = types.SimpleNamespace(**kwargs)
    return ns


@pytest.fixture
def store(tmp_path):
    return _FakeStore(tmp_path)


# ── _labels_path / round-trip ─────────────────────────────────────────────────

def test_labels_path_is_sibling(store):
    p = _labels_path(store.path)
    assert p.name == "labels.json"
    assert p.parent == Path(store.path).parent


def test_load_missing_file_returns_empty(store):
    assert _load_labels(store.path) == []


def test_save_and_load_roundtrip(store):
    sets = [LabelSet("snap1", {"env": "prod"})]
    _save_labels(store.path, sets)
    loaded = _load_labels(store.path)
    assert len(loaded) == 1
    assert loaded[0].snapshot_name == "snap1"
    assert loaded[0].labels["env"] == "prod"


def test_json_file_is_valid_list(store):
    _save_labels(store.path, [LabelSet("x", {"k": "v"})])
    raw = json.loads(_labels_path(store.path).read_text())
    assert isinstance(raw, list)


# ── cmd_label_add ─────────────────────────────────────────────────────────────

def test_label_add_creates_file(store, capsys):
    args = _make_args(name="snap1", key="env", value="dev")
    rc = cmd_label_add(args, store)
    assert rc == 0
    assert _labels_path(store.path).exists()
    captured = capsys.readouterr()
    assert "env=dev" in captured.out


def test_label_add_empty_key_returns_error(store, capsys):
    args = _make_args(name="snap1", key="", value="dev")
    rc = cmd_label_add(args, store)
    assert rc == 1
    assert "Error" in capsys.readouterr().out


# ── cmd_label_remove ──────────────────────────────────────────────────────────

def test_label_remove_succeeds(store, capsys):
    _save_labels(store.path, [LabelSet("snap1", {"env": "dev"})])
    args = _make_args(name="snap1", key="env")
    rc = cmd_label_remove(args, store)
    assert rc == 0
    loaded = _load_labels(store.path)
    assert "env" not in loaded[0].labels


# ── cmd_label_list ────────────────────────────────────────────────────────────

def test_label_list_no_labels(store, capsys):
    args = _make_args(name="ghost")
    rc = cmd_label_list(args, store)
    assert rc == 0
    assert "No labels" in capsys.readouterr().out


def test_label_list_shows_labels(store, capsys):
    _save_labels(store.path, [LabelSet("snap1", {"tier": "prod"})])
    args = _make_args(name="snap1")
    cmd_label_list(args, store)
    assert "tier=prod" in capsys.readouterr().out


# ── cmd_label_filter ──────────────────────────────────────────────────────────

def test_label_filter_no_match(store, capsys):
    args = _make_args(key="missing", value=None)
    rc = cmd_label_filter(args, store)
    assert rc == 0
    assert "No snapshots" in capsys.readouterr().out


def test_label_filter_matches(store, capsys):
    _save_labels(store.path, [
        LabelSet("a", {"env": "prod"}),
        LabelSet("b", {"env": "dev"}),
    ])
    args = _make_args(key="env", value="prod")
    cmd_label_filter(args, store)
    out = capsys.readouterr().out
    assert "a" in out
    assert "b" not in out
