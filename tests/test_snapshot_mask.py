"""Tests for envforge.snapshot_mask."""
import pytest

from envforge.snapshot import Snapshot
from envforge.snapshot_mask import (
    MASK_PLACEHOLDER,
    MaskResult,
    _is_sensitive,
    mask_snapshot,
)


def _snap(vars: dict, name: str = "test") -> Snapshot:
    return Snapshot(name=name, vars=vars)


# ---------------------------------------------------------------------------
# _is_sensitive
# ---------------------------------------------------------------------------

def test_is_sensitive_secret_pattern():
    assert _is_sensitive("AWS_SECRET_KEY", ["*SECRET*"]) is True


def test_is_sensitive_case_insensitive():
    assert _is_sensitive("db_password", ["*PASSWORD*"]) is True


def test_is_sensitive_no_match():
    assert _is_sensitive("HOME", ["*SECRET*", "*TOKEN*"]) is False


# ---------------------------------------------------------------------------
# mask_snapshot – basic behaviour
# ---------------------------------------------------------------------------

def test_mask_replaces_sensitive_values():
    snap = _snap({"API_KEY": "abc123", "HOME": "/home/user"})
    result = mask_snapshot(snap)
    assert result.masked.vars["API_KEY"] == MASK_PLACEHOLDER
    assert result.masked.vars["HOME"] == "/home/user"


def test_mask_records_masked_keys():
    snap = _snap({"DB_PASSWORD": "secret", "PORT": "5432"})
    result = mask_snapshot(snap)
    assert "DB_PASSWORD" in result.masked_keys
    assert "PORT" not in result.masked_keys


def test_mask_no_sensitive_keys():
    snap = _snap({"HOME": "/home/user", "SHELL": "/bin/bash"})
    result = mask_snapshot(snap)
    assert result.masked_keys == []
    assert result.has_masked is False


def test_mask_original_snapshot_unchanged():
    snap = _snap({"SECRET_TOKEN": "topsecret"})
    result = mask_snapshot(snap)
    assert result.original.vars["SECRET_TOKEN"] == "topsecret"


def test_mask_preserves_metadata():
    snap = Snapshot(name="mysnap", vars={"KEY": "val"}, tags=["prod"], description="desc")
    result = mask_snapshot(snap)
    assert result.masked.name == "mysnap"
    assert result.masked.tags == ["prod"]
    assert result.masked.description == "desc"


# ---------------------------------------------------------------------------
# extra_patterns and custom placeholder
# ---------------------------------------------------------------------------

def test_mask_extra_patterns():
    snap = _snap({"MY_CERT": "data", "HOME": "/home"})
    result = mask_snapshot(snap, extra_patterns=["*CERT*"])
    assert result.masked.vars["MY_CERT"] == MASK_PLACEHOLDER
    assert result.masked.vars["HOME"] == "/home"


def test_mask_custom_placeholder():
    snap = _snap({"PASSWORD": "hunter2"})
    result = mask_snapshot(snap, placeholder="<REDACTED>")
    assert result.masked.vars["PASSWORD"] == "<REDACTED>"


# ---------------------------------------------------------------------------
# MaskResult.__str__
# ---------------------------------------------------------------------------

def test_mask_result_str_no_masked():
    snap = _snap({"HOME": "/home"})
    result = mask_snapshot(snap)
    assert "No keys masked" in str(result)


def test_mask_result_str_with_masked():
    snap = _snap({"API_KEY": "x", "DB_PASSWORD": "y"})
    result = mask_snapshot(snap)
    text = str(result)
    assert "2 key(s)" in text
    assert "API_KEY" in text
    assert "DB_PASSWORD" in text
