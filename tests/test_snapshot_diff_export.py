"""Tests for snapshot_diff_export module."""
from __future__ import annotations

import json

import pytest

from envforge.diff import SnapshotDiff
from envforge.snapshot import Snapshot
from envforge.snapshot_diff_export import DiffExportResult, export_diff


def _snap(name: str, variables: dict) -> Snapshot:
    s = Snapshot(name=name)
    s.variables = dict(variables)
    return s


@pytest.fixture()
def base():
    return _snap("base", {"A": "1", "B": "2", "C": "3"})


@pytest.fixture()
def other():
    return _snap("other", {"A": "1", "B": "99", "D": "4"})


@pytest.fixture()
def diff(base, other):
    return SnapshotDiff(base=base, other=other)


# --- DiffExportResult ---

def test_export_result_fmt_stored(diff):
    r = export_diff(diff, fmt="json")
    assert r.fmt == "json"


def test_export_result_content_is_string(diff):
    r = export_diff(diff, fmt="json")
    assert isinstance(r.content, str)


# --- JSON format ---

def test_json_export_has_added_key(diff):
    r = export_diff(diff, fmt="json")
    data = json.loads(r.content)
    assert "D" in data["added"]
    assert data["added"]["D"] == "4"


def test_json_export_has_removed_key(diff):
    r = export_diff(diff, fmt="json")
    data = json.loads(r.content)
    assert "C" in data["removed"]


def test_json_export_has_changed_key(diff):
    r = export_diff(diff, fmt="json")
    data = json.loads(r.content)
    assert "B" in data["changed"]
    assert data["changed"]["B"]["before"] == "2"
    assert data["changed"]["B"]["after"] == "99"


def test_json_export_unchanged_key_absent(diff):
    r = export_diff(diff, fmt="json")
    data = json.loads(r.content)
    assert "A" not in data["added"]
    assert "A" not in data["removed"]
    assert "A" not in data["changed"]


# --- Markdown format ---

def test_markdown_export_contains_heading(diff):
    r = export_diff(diff, fmt="markdown")
    assert "# Snapshot Diff" in r.content


def test_markdown_export_added_section(diff):
    r = export_diff(diff, fmt="markdown")
    assert "## Added" in r.content
    assert "`D`" in r.content


def test_markdown_export_removed_section(diff):
    r = export_diff(diff, fmt="markdown")
    assert "## Removed" in r.content
    assert "`C`" in r.content


def test_markdown_export_changed_section(diff):
    r = export_diff(diff, fmt="markdown")
    assert "## Changed" in r.content
    assert "→" in r.content


def test_markdown_no_changes_message():
    s = _snap("x", {"A": "1"})
    d = SnapshotDiff(base=s, other=_snap("y", {"A": "1"}))
    r = export_diff(d, fmt="markdown")
    assert "No differences" in r.content


# --- CSV format ---

def test_csv_export_has_header(diff):
    r = export_diff(diff, fmt="csv")
    assert r.content.startswith("change_type,key,before,after")


def test_csv_export_added_row(diff):
    r = export_diff(diff, fmt="csv")
    assert "added,D,,4" in r.content


def test_csv_export_removed_row(diff):
    r = export_diff(diff, fmt="csv")
    assert "removed,C,3," in r.content


def test_csv_export_changed_row(diff):
    r = export_diff(diff, fmt="csv")
    assert "changed,B,2,99" in r.content


# --- Error handling ---

def test_unsupported_format_raises(diff):
    with pytest.raises(ValueError, match="Unsupported"):
        export_diff(diff, fmt="xml")  # type: ignore[arg-type]
