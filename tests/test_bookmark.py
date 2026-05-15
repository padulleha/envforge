"""Tests for envforge.snapshot_bookmark."""
from __future__ import annotations

import pytest

from envforge.snapshot_bookmark import (
    Bookmark,
    BookmarkError,
    add_bookmark,
    get_bookmark,
    list_bookmarks_for,
    remove_bookmark,
)


def _bm(name="bm1", snapshot="snap", keys=None):
    return Bookmark(
        name=name,
        snapshot_name=snapshot,
        keys=keys or ["A", "B"],
        description="",
        created_at="2024-01-01T00:00:00",
    )


def test_bookmark_roundtrip():
    bm = _bm()
    assert Bookmark.from_dict(bm.to_dict()) == bm


def test_bookmark_defaults():
    bm = Bookmark.from_dict({"name": "x", "snapshot_name": "s", "keys": ["K"]})
    assert bm.description == ""
    assert bm.created_at == ""


def test_add_bookmark_new():
    result = add_bookmark([], "bm1", "snap", ["A", "B"])
    assert len(result) == 1
    assert result[0].name == "bm1"


def test_add_bookmark_updates_existing():
    existing = add_bookmark([], "bm1", "snap", ["A"])
    updated = add_bookmark(existing, "bm1", "snap", ["A", "B", "C"])
    assert len(updated) == 1
    assert set(updated[0].keys) == {"A", "B", "C"}


def test_add_bookmark_sorted():
    bms = add_bookmark([], "z_bm", "snap", ["X"])
    bms = add_bookmark(bms, "a_bm", "snap", ["Y"])
    assert bms[0].name == "a_bm"
    assert bms[1].name == "z_bm"


def test_add_bookmark_empty_name_raises():
    with pytest.raises(BookmarkError, match="name must not be empty"):
        add_bookmark([], "", "snap", ["A"])


def test_add_bookmark_empty_keys_raises():
    with pytest.raises(BookmarkError, match="at least one key"):
        add_bookmark([], "bm", "snap", [])


def test_remove_bookmark_present():
    bms = add_bookmark([], "bm1", "snap", ["A"])
    bms = remove_bookmark(bms, "bm1")
    assert bms == []


def test_remove_bookmark_missing_raises():
    with pytest.raises(BookmarkError, match="not found"):
        remove_bookmark([], "ghost")


def test_get_bookmark_found():
    bms = add_bookmark([], "bm1", "snap", ["A"])
    found = get_bookmark(bms, "bm1")
    assert found is not None
    assert found.name == "bm1"


def test_get_bookmark_not_found():
    assert get_bookmark([], "nope") is None


def test_list_bookmarks_for_filters():
    bms = add_bookmark([], "b1", "snap_a", ["A"])
    bms = add_bookmark(bms, "b2", "snap_b", ["B"])
    bms = add_bookmark(bms, "b3", "snap_a", ["C"])
    result = list_bookmarks_for(bms, "snap_a")
    assert len(result) == 2
    assert all(b.snapshot_name == "snap_a" for b in result)


def test_format_contains_name_and_snapshot():
    bm = _bm(name="mybm", snapshot="mysnap", keys=["X", "Y"])
    text = bm.format()
    assert "mybm" in text
    assert "mysnap" in text
    assert "X" in text


def test_format_with_description():
    bm = _bm()
    bm.description = "important vars"
    assert "important vars" in bm.format()


def test_to_dict_keys_sorted():
    bm = _bm(keys=["Z", "A", "M"])
    assert bm.to_dict()["keys"] == ["A", "M", "Z"]
