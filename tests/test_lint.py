"""Tests for envforge.lint module."""

import pytest

from envforge.snapshot import Snapshot
from envforge.lint import lint_snapshot, LintIssue, LintResult


def _make_snap(variables: dict) -> Snapshot:
    return Snapshot(name="test", variables=variables)


# ---------------------------------------------------------------------------
# LintResult helpers
# ---------------------------------------------------------------------------

def test_lint_result_no_issues_summary():
    result = LintResult()
    assert result.summary() == "No issues found."
    assert not result.has_errors
    assert not result.has_warnings


def test_lint_result_summary_counts():
    result = LintResult(issues=[
        LintIssue("error", "A", "msg"),
        LintIssue("warning", "B", "msg"),
        LintIssue("warning", "C", "msg"),
        LintIssue("info", "D", "msg"),
    ])
    summary = result.summary()
    assert "1 error" in summary
    assert "2 warning" in summary
    assert "1 info" in summary


def test_lint_issue_str_format():
    issue = LintIssue("warning", "MY_KEY", "some message")
    text = str(issue)
    assert "[WARNING]" in text
    assert "MY_KEY" in text
    assert "some message" in text


# ---------------------------------------------------------------------------
# Empty snapshot
# ---------------------------------------------------------------------------

def test_empty_snapshot_warns():
    result = lint_snapshot(_make_snap({}))
    assert result.has_warnings
    assert any("no variables" in i.message.lower() for i in result.issues)


# ---------------------------------------------------------------------------
# Empty value detection
# ---------------------------------------------------------------------------

def test_empty_value_flagged():
    result = lint_snapshot(_make_snap({"MY_VAR": "", "OTHER": "ok"}))
    keys_with_issues = [i.key for i in result.issues]
    assert "MY_VAR" in keys_with_issues
    assert "OTHER" not in keys_with_issues


# ---------------------------------------------------------------------------
# Sensitive key detection
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("key", [
    "AWS_SECRET_ACCESS_KEY",
    "DB_PASSWORD",
    "GITHUB_TOKEN",
    "MY_API_KEY",
    "STRIPE_SECRET",
    "AUTH_HEADER",
])
def test_sensitive_keys_flagged(key):
    result = lint_snapshot(_make_snap({key: "somevalue"}))
    sensitive_issues = [i for i in result.issues if i.key == key]
    assert sensitive_issues, f"Expected warning for key {key!r}"
    assert any("sensitive" in i.message.lower() for i in sensitive_issues)


def test_non_sensitive_key_not_flagged():
    result = lint_snapshot(_make_snap({"PYTHONPATH": "/usr/lib/python"}))
    assert not result.has_warnings
    assert not result.has_errors


# ---------------------------------------------------------------------------
# Large value detection
# ---------------------------------------------------------------------------

def test_large_value_flagged():
    big_value = "x" * 600
    result = lint_snapshot(_make_snap({"BIG_VAR": big_value}))
    info_issues = [i for i in result.issues if i.severity == "info" and i.key == "BIG_VAR"]
    assert info_issues


def test_normal_value_not_flagged_as_large():
    result = lint_snapshot(_make_snap({"NORMAL": "short value"}))
    large_issues = [i for i in result.issues if "large" in i.message.lower()]
    assert not large_issues


# ---------------------------------------------------------------------------
# Multiple issues on one key
# ---------------------------------------------------------------------------

def test_multiple_issues_same_key():
    # A sensitive key with an empty value should produce multiple issues
    result = lint_snapshot(_make_snap({"DB_PASSWORD": ""}))
    key_issues = [i for i in result.issues if i.key == "DB_PASSWORD"]
    assert len(key_issues) >= 2
