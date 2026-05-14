"""Tests for envforge.snapshot_filter."""
from __future__ import annotations

import pytest

from envforge.snapshot import Snapshot
from envforge.snapshot_filter import (
    FilterCriteria,
    FilterResult,
    filter_snapshot,
    filter_snapshots,
)


def _snap(name: str, variables: dict, tags: list | None = None) -> Snapshot:
    meta = {}
    if tags:
        meta["tags"] = tags
    return Snapshot(name=name, variables=variables, metadata=meta)


# --- FilterResult ---

def test_filter_result_bool_true():
    s = _snap("s", {"A": "1"})
    r = FilterResult(snapshot=s, matched_keys=["A"])
    assert bool(r) is True


def test_filter_result_bool_false():
    s = _snap("s", {})
    r = FilterResult(snapshot=s, matched_keys=[])
    assert bool(r) is False


def test_filter_result_summary():
    s = _snap("mysnap", {"X": "1", "Y": "2"})
    r = FilterResult(snapshot=s, matched_keys=["X", "Y"])
    assert "mysnap" in r.summary()
    assert "2" in r.summary()


# --- filter_snapshot ---

def test_no_criteria_matches_all_keys():
    s = _snap("s", {"A": "1", "B": "2"})
    result = filter_snapshot(s, FilterCriteria())
    assert result is not None
    # no key/value pattern means matched_keys may be empty but snapshot passes


def test_key_pattern_filters_keys():
    s = _snap("s", {"APP_HOST": "localhost", "DB_HOST": "db", "PORT": "8080"})
    result = filter_snapshot(s, FilterCriteria(key_pattern="*_HOST"))
    assert result is not None
    assert set(result.matched_keys) == {"APP_HOST", "DB_HOST"}


def test_value_pattern_filters_values():
    s = _snap("s", {"A": "prod-1", "B": "dev-2", "C": "prod-3"})
    result = filter_snapshot(s, FilterCriteria(value_pattern="prod-*"))
    assert result is not None
    assert set(result.matched_keys) == {"A", "C"}


def test_key_and_value_pattern_combined():
    s = _snap("s", {"APP_ENV": "prod", "APP_DEBUG": "false", "DB_ENV": "prod"})
    result = filter_snapshot(s, FilterCriteria(key_pattern="APP_*", value_pattern="prod"))
    assert result is not None
    assert result.matched_keys == ["APP_ENV"]


def test_name_pattern_excludes_non_matching():
    s = _snap("staging-v2", {"X": "1"})
    result = filter_snapshot(s, FilterCriteria(name_pattern="prod-*"))
    assert result is None


def test_name_pattern_includes_matching():
    s = _snap("prod-2024", {"X": "1"})
    result = filter_snapshot(s, FilterCriteria(name_pattern="prod-*"))
    assert result is not None


def test_tag_filter_excludes_missing_tag():
    s = _snap("s", {"X": "1"}, tags=["dev"])
    result = filter_snapshot(s, FilterCriteria(tags=["prod"]))
    assert result is None


def test_tag_filter_includes_matching_tag():
    s = _snap("s", {"X": "1"}, tags=["prod", "us-east"])
    result = filter_snapshot(s, FilterCriteria(tags=["prod"]))
    assert result is not None


def test_min_keys_excludes_small_snapshot():
    s = _snap("s", {"A": "1"})
    result = filter_snapshot(s, FilterCriteria(min_keys=3))
    assert result is None


def test_max_keys_excludes_large_snapshot():
    s = _snap("s", {"A": "1", "B": "2", "C": "3", "D": "4"})
    result = filter_snapshot(s, FilterCriteria(max_keys=2))
    assert result is None


def test_key_pattern_no_match_returns_none():
    s = _snap("s", {"FOO": "bar"})
    result = filter_snapshot(s, FilterCriteria(key_pattern="MISSING_*"))
    assert result is None


# --- filter_snapshots ---

def test_filter_snapshots_returns_only_matches():
    snaps = [
        _snap("prod", {"ENV": "production"}),
        _snap("dev", {"ENV": "development"}),
        _snap("staging", {"ENV": "production"}),
    ]
    results = filter_snapshots(snaps, FilterCriteria(value_pattern="production"))
    names = [r.snapshot.name for r in results]
    assert "prod" in names
    assert "staging" in names
    assert "dev" not in names


def test_filter_snapshots_empty_list():
    results = filter_snapshots([], FilterCriteria(key_pattern="*"))
    assert results == []


def test_filter_snapshots_no_criteria_returns_all():
    snaps = [_snap(f"s{i}", {"K": "v"}) for i in range(4)]
    results = filter_snapshots(snaps, FilterCriteria())
    assert len(results) == 4
