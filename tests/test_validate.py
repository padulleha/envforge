"""Tests for envforge.validate."""

import pytest

from envforge.snapshot import Snapshot
from envforge.validate import (
    ValidationIssue,
    ValidationResult,
    validate_snapshot,
)


def _make_snap(**variables) -> Snapshot:
    return Snapshot(name="test", variables=dict(variables))


# ---------------------------------------------------------------------------
# ValidationIssue / ValidationResult helpers
# ---------------------------------------------------------------------------

def test_issue_str_format():
    issue = ValidationIssue(key="FOO", message="bad value", severity="error")
    assert "[ERROR]" in str(issue)
    assert "FOO" in str(issue)
    assert "bad value" in str(issue)


def test_result_is_valid_no_issues():
    r = ValidationResult()
    assert r.is_valid


def test_result_is_invalid_with_error():
    r = ValidationResult(issues=[ValidationIssue("K", "msg", "error")])
    assert not r.is_valid


def test_result_is_valid_with_only_warning():
    r = ValidationResult(issues=[ValidationIssue("K", "msg", "warning")])
    assert r.is_valid


def test_result_summary_no_issues():
    r = ValidationResult()
    assert "valid" in r.summary().lower()


def test_result_summary_counts():
    r = ValidationResult(
        issues=[
            ValidationIssue("A", "e", "error"),
            ValidationIssue("B", "w", "warning"),
        ]
    )
    assert "1 error" in r.summary()
    assert "1 warning" in r.summary()


def test_format_text_no_issues():
    r = ValidationResult()
    assert r.format_text() == r.summary()


def test_format_text_lists_issues():
    r = ValidationResult(issues=[ValidationIssue("X", "oops", "error")])
    text = r.format_text()
    assert "X" in text
    assert "oops" in text


# ---------------------------------------------------------------------------
# validate_snapshot
# ---------------------------------------------------------------------------

def test_valid_snapshot_passes():
    snap = _make_snap(MY_VAR="hello", ANOTHER_VAR="world")
    result = validate_snapshot(snap)
    assert result.is_valid
    assert not result.issues


def test_empty_snapshot_warns():
    snap = _make_snap()
    result = validate_snapshot(snap)
    assert result.warnings
    assert result.is_valid  # warning, not error


def test_invalid_key_name_raises_error():
    snap = _make_snap(**{"1INVALID": "val"})
    result = validate_snapshot(snap)
    assert not result.is_valid
    assert any("1INVALID" in i.key for i in result.errors)


def test_key_with_hyphen_raises_error():
    snap = _make_snap(**{"MY-VAR": "val"})
    result = validate_snapshot(snap)
    assert not result.is_valid


def test_value_too_long_warns():
    snap = _make_snap(BIG_VAR="x" * 10)
    result = validate_snapshot(snap, max_value_length=5)
    assert any(i.severity == "warning" and "BIG_VAR" in i.key for i in result.issues)


def test_forbidden_prefix_raises_error():
    snap = _make_snap(SECRET_TOKEN="abc", NORMAL_VAR="ok")
    result = validate_snapshot(snap, forbidden_prefixes=["SECRET_"])
    assert not result.is_valid
    assert any("SECRET_TOKEN" in i.key for i in result.errors)
    # NORMAL_VAR should be fine
    assert not any("NORMAL_VAR" in i.key for i in result.errors)


def test_multiple_issues_collected():
    snap = _make_snap(**{"bad-key": "x" * 10, "GOOD_KEY": "fine"})
    result = validate_snapshot(snap, max_value_length=5)
    keys_with_issues = {i.key for i in result.issues}
    assert "bad-key" in keys_with_issues
    assert "GOOD_KEY" in keys_with_issues
