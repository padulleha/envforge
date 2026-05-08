"""Tests for envforge.expire."""

from datetime import datetime, timedelta, timezone

import pytest

from envforge.expire import (
    ExpiryRecord,
    add_expiry,
    get_expired,
    records_from_dict,
    records_to_dict,
    remove_expiry,
)

_FUTURE = datetime(2099, 1, 1, tzinfo=timezone.utc)
_PAST = datetime(2000, 1, 1, tzinfo=timezone.utc)
_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def _rec(name="snap1", expires_at=_FUTURE, reason="") -> ExpiryRecord:
    return ExpiryRecord(name=name, expires_at=expires_at, reason=reason)


# --- ExpiryRecord ---

def test_is_expired_future():
    assert not _rec(expires_at=_FUTURE).is_expired(now=_NOW)


def test_is_expired_past():
    assert _rec(expires_at=_PAST).is_expired(now=_NOW)


def test_is_expired_exact_boundary():
    assert _rec(expires_at=_NOW).is_expired(now=_NOW)


def test_format_active_contains_name_and_status():
    text = _rec(name="mysnap", expires_at=_FUTURE).format()
    assert "mysnap" in text
    assert "active" in text


def test_format_expired_shows_expired():
    text = _rec(expires_at=_PAST).format()
    assert "EXPIRED" in text


def test_format_includes_reason():
    text = _rec(reason="temp project").format()
    assert "temp project" in text


def test_format_no_reason_no_parens():
    text = _rec(reason="").format()
    assert "(" not in text


# --- Serialization ---

def test_roundtrip():
    original = ExpiryRecord(name="snap", expires_at=_FUTURE, reason="demo")
    restored = ExpiryRecord.from_dict(original.to_dict())
    assert restored.name == original.name
    assert restored.expires_at == original.expires_at
    assert restored.reason == original.reason


def test_roundtrip_no_reason():
    original = ExpiryRecord(name="x", expires_at=_PAST)
    restored = ExpiryRecord.from_dict(original.to_dict())
    assert restored.reason == ""


def test_records_roundtrip():
    recs = [_rec("a", _FUTURE), _rec("b", _PAST, "old")]
    assert records_from_dict(records_to_dict(recs))[1].reason == "old"


# --- add / remove ---

def test_add_expiry_new():
    result = add_expiry([], "snap1", _FUTURE)
    assert len(result) == 1
    assert result[0].name == "snap1"


def test_add_expiry_updates_existing():
    existing = [_rec("snap1", _PAST)]
    result = add_expiry(existing, "snap1", _FUTURE)
    assert len(result) == 1
    assert result[0].expires_at == _FUTURE


def test_add_expiry_sorted():
    records = add_expiry([], "z", _FUTURE)
    records = add_expiry(records, "a", _FUTURE)
    assert records[0].name == "a"


def test_remove_expiry_present():
    records = [_rec("snap1"), _rec("snap2")]
    result = remove_expiry(records, "snap1")
    assert all(r.name != "snap1" for r in result)
    assert len(result) == 1


def test_remove_expiry_missing_is_noop():
    records = [_rec("snap1")]
    result = remove_expiry(records, "nope")
    assert len(result) == 1


# --- get_expired ---

def test_get_expired_returns_only_expired():
    records = [_rec("old", _PAST), _rec("new", _FUTURE)]
    expired = get_expired(records, now=_NOW)
    assert len(expired) == 1
    assert expired[0].name == "old"


def test_get_expired_empty():
    assert get_expired([], now=_NOW) == []


def test_get_expired_all_active():
    records = [_rec("a", _FUTURE), _rec("b", _FUTURE)]
    assert get_expired(records, now=_NOW) == []
