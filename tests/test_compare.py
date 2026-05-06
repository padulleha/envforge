"""Tests for envforge.compare module."""
from __future__ import annotations

import pytest

from envforge.compare import compare_snapshots, CompareReport
from envforge.snapshot import Snapshot


def _snap(name: str, variables: dict) -> Snapshot:
    s = Snapshot(name=name)
    s.variables = dict(variables)
    return s


def test_compare_identical_snapshots():
    a = _snap("a", {"X": "1", "Y": "2"})
    b = _snap("b", {"X": "1", "Y": "2"})
    report = compare_snapshots(a, b)
    assert not report.has_differences
    assert sorted(report.unchanged) == ["X", "Y"]
    assert report.summary() == "No differences"


def test_compare_added_keys():
    a = _snap("a", {"X": "1"})
    b = _snap("b", {"X": "1", "NEW": "hello"})
    report = compare_snapshots(a, b)
    assert report.has_differences
    assert "NEW" in report.added
    assert report.added["NEW"] == "hello"
    assert not report.removed
    assert not report.changed


def test_compare_removed_keys():
    a = _snap("a", {"X": "1", "OLD": "bye"})
    b = _snap("b", {"X": "1"})
    report = compare_snapshots(a, b)
    assert report.has_differences
    assert "OLD" in report.removed
    assert report.removed["OLD"] == "bye"
    assert not report.added


def test_compare_changed_keys():
    a = _snap("a", {"X": "old"})
    b = _snap("b", {"X": "new"})
    report = compare_snapshots(a, b)
    assert report.has_differences
    assert "X" in report.changed
    assert report.changed["X"] == ("old", "new")


def test_compare_mixed():
    a = _snap("a", {"KEEP": "same", "REMOVE": "gone", "CHANGE": "v1"})
    b = _snap("b", {"KEEP": "same", "ADD": "new", "CHANGE": "v2"})
    report = compare_snapshots(a, b)
    assert report.has_differences
    assert "ADD" in report.added
    assert "REMOVE" in report.removed
    assert "CHANGE" in report.changed
    assert "KEEP" in report.unchanged


def test_compare_custom_names():
    a = _snap("snap-a", {})
    b = _snap("snap-b", {})
    report = compare_snapshots(a, b, base_name="custom-base", other_name="custom-other")
    assert report.base_name == "custom-base"
    assert report.other_name == "custom-other"


def test_summary_counts():
    a = _snap("a", {"A": "1", "B": "2"})
    b = _snap("b", {"B": "changed", "C": "3"})
    report = compare_snapshots(a, b)
    summary = report.summary()
    assert "+1" in summary
    assert "-1" in summary
    assert "~1" in summary


def test_format_text_contains_markers():
    a = _snap("a", {"X": "1", "Y": "old"})
    b = _snap("b", {"Y": "new", "Z": "3"})
    report = compare_snapshots(a, b)
    text = report.format_text()
    assert "+ Z" in text
    assert "- X" in text
    assert "~ Y" in text


def test_format_text_show_unchanged():
    a = _snap("a", {"SAME": "v"})
    b = _snap("b", {"SAME": "v"})
    report = compare_snapshots(a, b)
    text_without = report.format_text(show_unchanged=False)
    text_with = report.format_text(show_unchanged=True)
    assert "SAME" not in text_without
    assert "SAME" in text_with
