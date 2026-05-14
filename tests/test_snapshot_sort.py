"""Tests for envforge.snapshot_sort."""
from __future__ import annotations

import pytest

from envforge.snapshot import Snapshot
from envforge.snapshot_sort import (
    SortCriteria,
    SortKey,
    SortOrder,
    SortResult,
    sort_snapshots,
)


def _snap(name: str, variables: dict | None = None, description: str = "", created_at: str = "") -> Snapshot:
    s = Snapshot(name=name, variables=variables or {}, description=description)
    s.created_at = created_at
    return s


def test_sort_criteria_defaults():
    c = SortCriteria()
    assert c.key == SortKey.NAME
    assert c.order == SortOrder.ASC


def test_sort_criteria_roundtrip():
    c = SortCriteria(key=SortKey.KEY_COUNT, order=SortOrder.DESC)
    assert SortCriteria.from_dict(c.to_dict()) == c


def test_sort_by_name_asc():
    snaps = [_snap("zebra"), _snap("alpha"), _snap("mango")]
    result = sort_snapshots(snaps)
    assert [s.name for s in result.snapshots] == ["alpha", "mango", "zebra"]


def test_sort_by_name_desc():
    snaps = [_snap("zebra"), _snap("alpha"), _snap("mango")]
    criteria = SortCriteria(key=SortKey.NAME, order=SortOrder.DESC)
    result = sort_snapshots(snaps, criteria)
    assert [s.name for s in result.snapshots] == ["zebra", "mango", "alpha"]


def test_sort_by_key_count_asc():
    snaps = [
        _snap("big", {"A": "1", "B": "2", "C": "3"}),
        _snap("small", {"X": "1"}),
        _snap("medium", {"P": "1", "Q": "2"}),
    ]
    criteria = SortCriteria(key=SortKey.KEY_COUNT, order=SortOrder.ASC)
    result = sort_snapshots(snaps, criteria)
    assert [s.name for s in result.snapshots] == ["small", "medium", "big"]


def test_sort_by_key_count_desc():
    snaps = [
        _snap("big", {"A": "1", "B": "2", "C": "3"}),
        _snap("small", {"X": "1"}),
    ]
    criteria = SortCriteria(key=SortKey.KEY_COUNT, order=SortOrder.DESC)
    result = sort_snapshots(snaps, criteria)
    assert result.snapshots[0].name == "big"


def test_sort_by_created_asc():
    snaps = [
        _snap("c", created_at="2024-03-01"),
        _snap("a", created_at="2024-01-01"),
        _snap("b", created_at="2024-02-01"),
    ]
    criteria = SortCriteria(key=SortKey.CREATED, order=SortOrder.ASC)
    result = sort_snapshots(snaps, criteria)
    assert [s.name for s in result.snapshots] == ["a", "b", "c"]


def test_sort_by_description_asc():
    snaps = [
        _snap("x", description="zeta env"),
        _snap("y", description="alpha env"),
    ]
    criteria = SortCriteria(key=SortKey.DESCRIPTION, order=SortOrder.ASC)
    result = sort_snapshots(snaps, criteria)
    assert result.snapshots[0].name == "y"


def test_sort_result_summary():
    snaps = [_snap("a"), _snap("b")]
    criteria = SortCriteria(key=SortKey.NAME, order=SortOrder.ASC)
    result = sort_snapshots(snaps, criteria)
    assert "2" in result.summary()
    assert "name" in result.summary()
    assert "asc" in result.summary()


def test_sort_empty_list():
    result = sort_snapshots([])
    assert result.snapshots == []
    assert result.original_count == 0


def test_sort_default_criteria_is_name_asc():
    snaps = [_snap("z"), _snap("a")]
    result = sort_snapshots(snaps)
    assert result.snapshots[0].name == "a"
    assert result.criteria.key == SortKey.NAME
