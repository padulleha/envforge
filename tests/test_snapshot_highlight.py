"""Tests for envforge.snapshot_highlight."""
from __future__ import annotations

import pytest

from envforge.snapshot import Snapshot
from envforge.snapshot_highlight import HighlightResult, highlight_snapshot


def _snap(name: str = "test", **kwargs: str) -> Snapshot:
    return Snapshot(name=name, variables=dict(kwargs))


# --- HighlightResult ---

def test_highlight_result_bool_true():
    r = HighlightResult("s", highlighted={"A": "1"}, patterns=["A"])
    assert bool(r) is True


def test_highlight_result_bool_false():
    r = HighlightResult("s", highlighted={}, patterns=["X"])
    assert bool(r) is False


def test_highlight_result_summary_no_match():
    r = HighlightResult("mysnap", highlighted={}, patterns=["MISSING_*"])
    assert "mysnap" in r.summary()
    assert "no keys matched" in r.summary()


def test_highlight_result_summary_with_match():
    r = HighlightResult("mysnap", highlighted={"A": "1", "B": "2"}, patterns=["*"])
    assert "2 key(s)" in r.summary()


def test_format_text_no_match_returns_summary():
    r = HighlightResult("s", highlighted={}, patterns=["Z*"])
    assert "no keys matched" in r.format_text()


def test_format_text_shows_keys_and_values():
    r = HighlightResult("s", highlighted={"FOO": "bar"}, patterns=["FOO"])
    text = r.format_text()
    assert "FOO" in text
    assert "bar" in text


def test_format_text_mask_hides_values():
    r = HighlightResult("s", highlighted={"SECRET": "abc123"}, patterns=["SECRET"])
    text = r.format_text(mask_values=True)
    assert "***" in text
    assert "abc123" not in text


# --- highlight_snapshot ---

def test_highlight_exact_key():
    snap = _snap("s", FOO="1", BAR="2")
    result = highlight_snapshot(snap, ["FOO"])
    assert "FOO" in result.highlighted
    assert "BAR" not in result.highlighted


def test_highlight_glob_pattern():
    snap = _snap("s", AWS_KEY="k", AWS_SECRET="s", OTHER="o")
    result = highlight_snapshot(snap, ["AWS_*"])
    assert "AWS_KEY" in result.highlighted
    assert "AWS_SECRET" in result.highlighted
    assert "OTHER" not in result.highlighted


def test_highlight_multiple_patterns():
    snap = _snap("s", DB_HOST="h", DB_PASS="p", APP_ENV="prod")
    result = highlight_snapshot(snap, ["DB_*", "APP_*"])
    assert len(result.highlighted) == 3


def test_highlight_case_insensitive_default():
    snap = _snap("s", aws_key="val")
    result = highlight_snapshot(snap, ["AWS_*"])
    assert "aws_key" in result.highlighted


def test_highlight_case_sensitive_no_match():
    snap = _snap("s", aws_key="val")
    result = highlight_snapshot(snap, ["AWS_*"], case_sensitive=True)
    assert not result.highlighted


def test_highlight_no_patterns_returns_empty():
    snap = _snap("s", FOO="1")
    result = highlight_snapshot(snap, [])
    assert not result.highlighted


def test_highlight_empty_snapshot():
    snap = _snap("empty")
    result = highlight_snapshot(snap, ["*"])
    assert not result.highlighted


def test_highlight_result_snapshot_name_preserved():
    snap = _snap("myproject")
    result = highlight_snapshot(snap, ["*"])
    assert result.snapshot_name == "myproject"


def test_highlight_patterns_stored_on_result():
    snap = _snap("s", X="1")
    result = highlight_snapshot(snap, ["X", "Y*"])
    assert "X" in result.patterns
    assert "Y*" in result.patterns
