"""Integration-style roundtrip tests for bookmark persistence."""
from __future__ import annotations

import json
from pathlib import Path

from envforge.snapshot_bookmark import Bookmark, add_bookmark, get_bookmark
from envforge.cli_bookmark import _bookmarks_path, _load_bookmarks, _save_bookmarks


def test_save_and_load_roundtrip(tmp_path):
    store_file = tmp_path / "store.json"
    store_file.write_text("{}")
    store_path = str(store_file)

    bms = add_bookmark([], "bm1", "project_a", ["DB_URL", "API_KEY"], description="prod vars")
    bms = add_bookmark(bms, "bm2", "project_b", ["SECRET"])
    _save_bookmarks(store_path, bms)

    loaded = _load_bookmarks(store_path)
    assert len(loaded) == 2
    assert loaded[0].name == "bm1"
    assert loaded[1].name == "bm2"


def test_load_missing_file_returns_empty(tmp_path):
    store_file = tmp_path / "store.json"
    store_file.write_text("{}")
    result = _load_bookmarks(str(store_file))
    assert result == []


def test_bookmarks_path_is_sibling(tmp_path):
    store_file = tmp_path / "store.json"
    store_file.write_text("{}")
    p = _bookmarks_path(str(store_file))
    assert p.parent == tmp_path
    assert p.name == "bookmarks.json"


def test_overwrite_bookmark_persists_new_keys(tmp_path):
    store_file = tmp_path / "store.json"
    store_file.write_text("{}")
    store_path = str(store_file)

    bms = add_bookmark([], "bm1", "snap", ["A"])
    _save_bookmarks(store_path, bms)

    bms = _load_bookmarks(store_path)
    bms = add_bookmark(bms, "bm1", "snap", ["A", "B", "C"])
    _save_bookmarks(store_path, bms)

    reloaded = _load_bookmarks(store_path)
    found = get_bookmark(reloaded, "bm1")
    assert found is not None
    assert set(found.keys) == {"A", "B", "C"}


def test_json_file_is_valid_list(tmp_path):
    store_file = tmp_path / "store.json"
    store_file.write_text("{}")
    store_path = str(store_file)

    bms = add_bookmark([], "x", "s", ["K"])
    _save_bookmarks(store_path, bms)

    raw = json.loads((tmp_path / "bookmarks.json").read_text())
    assert isinstance(raw, list)
    assert raw[0]["name"] == "x"
    assert "keys" in raw[0]
    assert "snapshot_name" in raw[0]
