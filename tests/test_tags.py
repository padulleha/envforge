"""Tests for tag management (envforge/tags.py and envforge/cli_tags.py)."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from envforge.tags import add_tag, remove_tag, filter_by_tag, format_tags
from envforge.cli_tags import cmd_tag_add, cmd_tag_remove, cmd_tag_list, cmd_tag_filter


# ---------------------------------------------------------------------------
# Pure tag helpers
# ---------------------------------------------------------------------------

def test_add_tag_basic():
    assert add_tag([], "prod") == ["prod"]


def test_add_tag_deduped():
    assert add_tag(["prod"], "prod") == ["prod"]


def test_add_tag_sorted():
    assert add_tag(["prod"], "dev") == ["dev", "prod"]


def test_add_tag_empty_raises():
    with pytest.raises(ValueError):
        add_tag([], "")


def test_remove_tag_present():
    assert remove_tag(["dev", "prod"], "dev") == ["prod"]


def test_remove_tag_absent_is_silent():
    assert remove_tag(["prod"], "missing") == ["prod"]


def test_format_tags_empty():
    assert format_tags([]) == "(no tags)"


def test_format_tags_multiple():
    result = format_tags(["dev", "prod"])
    assert "#dev" in result and "#prod" in result


# ---------------------------------------------------------------------------
# filter_by_tag
# ---------------------------------------------------------------------------

def _make_store(snapshots: dict):
    store = MagicMock()
    store.list.return_value = list(snapshots.keys())
    store.get.side_effect = lambda name: snapshots.get(name)
    return store


def _snap(tags):
    s = MagicMock()
    s.tags = tags
    return s


def test_filter_by_tag_match():
    store = _make_store({"a": _snap(["prod"]), "b": _snap(["dev"])})
    assert filter_by_tag(["a", "b"], "prod", store) == ["a"]


def test_filter_by_tag_no_match():
    store = _make_store({"a": _snap(["dev"])})
    assert filter_by_tag(["a"], "prod", store) == []


# ---------------------------------------------------------------------------
# CLI commands (smoke tests)
# ---------------------------------------------------------------------------

def test_cmd_tag_add_updates_snap(capsys):
    snap = _snap([])
    snap.tags = []
    store = MagicMock()
    store.get.return_value = snap
    args = MagicMock(name="mysnap", tag="prod")
    args.name = "mysnap"
    args.tag = "prod"
    cmd_tag_add(args, store)
    assert "prod" in snap.tags
    store.save.assert_called_once_with(snap)


def test_cmd_tag_add_missing_snap(capsys):
    store = MagicMock()
    store.get.return_value = None
    args = MagicMock()
    args.name = "ghost"
    args.tag = "x"
    cmd_tag_add(args, store)
    out = capsys.readouterr().out
    assert "not found" in out


def test_cmd_tag_filter_no_match(capsys):
    store = _make_store({"a": _snap(["dev"])})
    args = MagicMock()
    args.tag = "prod"
    cmd_tag_filter(args, store)
    out = capsys.readouterr().out
    assert "No snapshots" in out
