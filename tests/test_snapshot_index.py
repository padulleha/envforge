"""Tests for envforge.snapshot_index."""
from __future__ import annotations

import pytest

from envforge.snapshot import Snapshot
from envforge.snapshot_index import IndexEntry, SnapshotIndex, build_index


def _snap(name: str, variables: dict, tags: list | None = None, description: str = "") -> Snapshot:
    meta: dict = {}
    if tags:
        meta["tags"] = tags
    if description:
        meta["description"] = description
    s = Snapshot(name=name, variables=variables, metadata=meta)
    return s


@pytest.fixture()
def populated_index() -> SnapshotIndex:
    snaps = [
        _snap("prod", {"AWS_KEY": "abc", "DB_HOST": "prod-db"}, tags=["production"], description="Production env"),
        _snap("staging", {"AWS_KEY": "xyz", "DB_HOST": "stage-db", "DEBUG": "1"}, tags=["staging"]),
        _snap("local", {"DEBUG": "1", "PORT": "8080"}, description="Local dev environment"),
    ]
    return build_index(snaps)


def test_build_index_size(populated_index: SnapshotIndex) -> None:
    assert populated_index.size() == 3


def test_find_by_key_exact(populated_index: SnapshotIndex) -> None:
    results = populated_index.find_by_key("AWS_KEY")
    assert set(results) == {"prod", "staging"}


def test_find_by_key_glob(populated_index: SnapshotIndex) -> None:
    results = populated_index.find_by_key("AWS_*")
    assert set(results) == {"prod", "staging"}


def test_find_by_key_no_match(populated_index: SnapshotIndex) -> None:
    results = populated_index.find_by_key("NONEXISTENT")
    assert results == []


def test_find_by_tag_present(populated_index: SnapshotIndex) -> None:
    results = populated_index.find_by_tag("production")
    assert results == ["prod"]


def test_find_by_tag_absent(populated_index: SnapshotIndex) -> None:
    results = populated_index.find_by_tag("nightly")
    assert results == []


def test_find_by_description_substring(populated_index: SnapshotIndex) -> None:
    results = populated_index.find_by_description("env")
    assert set(results) == {"prod", "local"}


def test_find_by_description_case_insensitive(populated_index: SnapshotIndex) -> None:
    results = populated_index.find_by_description("PRODUCTION")
    assert "prod" in results


def test_find_by_description_no_match(populated_index: SnapshotIndex) -> None:
    results = populated_index.find_by_description("zzz")
    assert results == []


def test_all_keys(populated_index: SnapshotIndex) -> None:
    keys = populated_index.all_keys()
    assert {"AWS_KEY", "DB_HOST", "DEBUG", "PORT"} == keys


def test_get_existing_entry(populated_index: SnapshotIndex) -> None:
    entry = populated_index.get("local")
    assert entry is not None
    assert entry.name == "local"
    assert "PORT" in entry.keys


def test_get_missing_entry(populated_index: SnapshotIndex) -> None:
    assert populated_index.get("ghost") is None


def test_build_empty_index() -> None:
    idx = build_index([])
    assert idx.size() == 0
    assert idx.all_keys() == set()


def test_rebuild_replaces_old_data() -> None:
    snap1 = _snap("a", {"X": "1"})
    snap2 = _snap("b", {"Y": "2"})
    idx = build_index([snap1])
    assert idx.size() == 1
    idx.build([snap2])
    assert idx.size() == 1
    assert idx.get("a") is None
    assert idx.get("b") is not None


def test_index_entry_has_tag() -> None:
    entry = IndexEntry(name="x", tags=["foo", "bar"])
    assert entry.has_tag("foo")
    assert not entry.has_tag("baz")
