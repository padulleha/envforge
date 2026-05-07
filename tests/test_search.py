"""Tests for envforge.search and envforge.cli_search."""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

import pytest

from envforge.search import SearchResult, search_snapshots
from envforge.snapshot import Snapshot


def _snap(variables: dict) -> Snapshot:
    return Snapshot(name="test", variables=variables)


SNAPS = {
    "dev": _snap({"DATABASE_URL": "postgres://localhost/dev", "DEBUG": "true", "PORT": "5000"}),
    "prod": _snap({"DATABASE_URL": "postgres://prod-host/app", "DEBUG": "false", "PORT": "443"}),
    "staging": _snap({"API_KEY": "abc123", "PORT": "8080"}),
}


def test_search_by_key_glob():
    results = search_snapshots(SNAPS, key_pattern="DATABASE*")
    names = {r.snapshot_name for r in results}
    assert names == {"dev", "prod"}


def test_search_by_value_glob():
    results = search_snapshots(SNAPS, value_pattern="*localhost*")
    assert len(results) == 1
    assert results[0].snapshot_name == "dev"


def test_search_by_key_and_value():
    results = search_snapshots(SNAPS, key_pattern="DEBUG", value_pattern="true")
    assert len(results) == 1
    assert results[0].snapshot_name == "dev"
    assert "DEBUG" in results[0].matched_keys


def test_search_no_match_returns_empty():
    results = search_snapshots(SNAPS, key_pattern="NONEXISTENT_KEY")
    assert results == []


def test_search_requires_at_least_one_pattern():
    with pytest.raises(ValueError):
        search_snapshots(SNAPS)


def test_search_regex_key():
    results = search_snapshots(SNAPS, key_pattern=r"^PORT$", use_regex=True)
    names = {r.snapshot_name for r in results}
    assert names == {"dev", "prod", "staging"}


def test_search_regex_value():
    results = search_snapshots(SNAPS, value_pattern=r"^\d+$", use_regex=True)
    names = {r.snapshot_name for r in results}
    assert "dev" in names
    assert "prod" in names
    assert "staging" in names


def test_search_result_bool_true():
    r = SearchResult(snapshot_name="x", matched_keys=["A"])
    assert bool(r) is True


def test_search_result_bool_false():
    r = SearchResult(snapshot_name="x", matched_keys=[])
    assert bool(r) is False


def test_search_result_summary():
    r = SearchResult(snapshot_name="mysnap", matched_keys=["FOO", "BAR"])
    s = r.summary()
    assert "mysnap" in s
    assert "FOO" in s
    assert "BAR" in s


def test_matched_keys_are_sorted():
    snaps = {"s": _snap({"Z_KEY": "1", "A_KEY": "2", "M_KEY": "3"})}
    results = search_snapshots(snaps, key_pattern="*KEY*")
    assert results[0].matched_keys == ["A_KEY", "M_KEY", "Z_KEY"]
