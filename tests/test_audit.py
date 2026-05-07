"""Tests for envforge.audit."""

import pytest
from envforge.audit import AuditEntry, AuditLog


# ---------------------------------------------------------------------------
# AuditEntry
# ---------------------------------------------------------------------------

def test_entry_roundtrip():
    entry = AuditEntry(
        action="apply",
        snapshot_name="prod",
        timestamp="2024-01-01T00:00:00+00:00",
        user="alice",
        hostname="box1",
        detail="forced",
    )
    restored = AuditEntry.from_dict(entry.to_dict())
    assert restored.action == entry.action
    assert restored.snapshot_name == entry.snapshot_name
    assert restored.timestamp == entry.timestamp
    assert restored.user == entry.user
    assert restored.hostname == entry.hostname
    assert restored.detail == entry.detail


def test_entry_roundtrip_no_detail():
    entry = AuditEntry(
        action="capture",
        snapshot_name="dev",
        timestamp="2024-06-15T12:00:00+00:00",
        user="bob",
        hostname="laptop",
    )
    d = entry.to_dict()
    assert "detail" not in d
    restored = AuditEntry.from_dict(d)
    assert restored.detail is None


def test_entry_format_contains_action_and_name():
    entry = AuditEntry(
        action="delete",
        snapshot_name="old",
        timestamp="2024-03-10T08:30:00+00:00",
        user="carol",
        hostname="srv",
    )
    text = entry.format()
    assert "DELETE" in text
    assert "old" in text
    assert "carol@srv" in text


def test_entry_format_includes_detail():
    entry = AuditEntry(
        action="apply",
        snapshot_name="staging",
        timestamp="2024-03-10T08:30:00+00:00",
        user="dave",
        hostname="ci",
        detail="no-overwrite",
    )
    assert "no-overwrite" in entry.format()


# ---------------------------------------------------------------------------
# AuditLog
# ---------------------------------------------------------------------------

def test_record_appends_entry():
    log = AuditLog()
    entry = log.record("apply", "prod")
    assert len(log.entries) == 1
    assert entry.action == "apply"
    assert entry.snapshot_name == "prod"


def test_record_sets_user_and_host():
    log = AuditLog()
    entry = log.record("capture", "dev")
    assert entry.user != ""
    assert entry.hostname != ""


def test_record_stores_detail():
    log = AuditLog()
    entry = log.record("apply", "prod", detail="overwrite=False")
    assert entry.detail == "overwrite=False"


def test_for_snapshot_filters():
    log = AuditLog()
    log.record("apply", "prod")
    log.record("apply", "dev")
    log.record("capture", "prod")
    prod_entries = log.for_snapshot("prod")
    assert len(prod_entries) == 2
    assert all(e.snapshot_name == "prod" for e in prod_entries)


def test_audit_log_roundtrip():
    log = AuditLog()
    log.record("apply", "prod", detail="test")
    log.record("delete", "old")
    restored = AuditLog.from_dict(log.to_dict())
    assert len(restored.entries) == 2
    assert restored.entries[0].action == "apply"
    assert restored.entries[1].snapshot_name == "old"


def test_audit_log_empty_roundtrip():
    log = AuditLog()
    restored = AuditLog.from_dict(log.to_dict())
    assert restored.entries == []
