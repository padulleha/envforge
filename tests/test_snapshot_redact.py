"""Tests for envforge.snapshot_redact."""
import pytest

from envforge.snapshot import Snapshot
from envforge.snapshot_redact import (
    DEFAULT_PLACEHOLDER,
    RedactResult,
    redact_snapshot,
)


def _snap(name: str = "test", **vars_: str) -> Snapshot:
    return Snapshot(name=name, variables=dict(vars_))


# ---------------------------------------------------------------------------
# RedactResult.__str__
# ---------------------------------------------------------------------------

def test_redact_result_str_no_redactions():
    snap = _snap("s", FOO="bar")
    result = RedactResult(snapshot=snap, redacted_keys=[])
    assert str(result) == "No keys redacted."


def test_redact_result_str_shows_keys():
    snap = _snap("s", FOO="bar")
    result = RedactResult(snapshot=snap, redacted_keys=["FOO", "BAR"])
    assert "FOO" in str(result)
    assert "BAR" in str(result)
    assert "2" in str(result)


def test_redact_result_has_redactions_true():
    snap = _snap("s", FOO="bar")
    result = RedactResult(snapshot=snap, redacted_keys=["FOO"])
    assert result.has_redactions is True


def test_redact_result_has_redactions_false():
    snap = _snap("s", FOO="bar")
    result = RedactResult(snapshot=snap, redacted_keys=[])
    assert result.has_redactions is False


# ---------------------------------------------------------------------------
# redact_snapshot
# ---------------------------------------------------------------------------

def test_redact_replaces_specified_keys():
    snap = _snap("env", SECRET="hunter2", PUBLIC="hello")
    result = redact_snapshot(snap, keys=["SECRET"])
    assert result.snapshot.variables["SECRET"] == DEFAULT_PLACEHOLDER
    assert result.snapshot.variables["PUBLIC"] == "hello"


def test_redact_records_redacted_keys():
    snap = _snap("env", A="1", B="2", C="3")
    result = redact_snapshot(snap, keys=["A", "C"])
    assert result.redacted_keys == ["A", "C"]


def test_redact_ignores_missing_keys():
    snap = _snap("env", FOO="bar")
    result = redact_snapshot(snap, keys=["MISSING"])
    assert result.redacted_keys == []
    assert result.snapshot.variables["FOO"] == "bar"


def test_redact_custom_placeholder():
    snap = _snap("env", TOKEN="abc123")
    result = redact_snapshot(snap, keys=["TOKEN"], placeholder="***")
    assert result.snapshot.variables["TOKEN"] == "***"
    assert result.placeholder == "***"


def test_redact_default_name_suffix():
    snap = _snap("myenv", X="1")
    result = redact_snapshot(snap, keys=["X"])
    assert result.snapshot.name == "myenv-redacted"


def test_redact_custom_name():
    snap = _snap("myenv", X="1")
    result = redact_snapshot(snap, keys=["X"], new_name="safe-env")
    assert result.snapshot.name == "safe-env"


def test_redact_preserves_tags_and_description():
    snap = Snapshot(
        name="env",
        variables={"K": "v"},
        description="my desc",
        tags=["prod", "infra"],
    )
    result = redact_snapshot(snap, keys=["K"])
    assert result.snapshot.description == "my desc"
    assert "prod" in result.snapshot.tags


def test_redact_empty_keys_list_changes_nothing():
    snap = _snap("env", FOO="bar", BAZ="qux")
    result = redact_snapshot(snap, keys=[])
    assert result.snapshot.variables == {"FOO": "bar", "BAZ": "qux"}
    assert result.redacted_keys == []


def test_redact_result_keys_are_sorted():
    snap = _snap("env", Z="1", A="2", M="3")
    result = redact_snapshot(snap, keys=["Z", "A", "M"])
    assert result.redacted_keys == ["A", "M", "Z"]
