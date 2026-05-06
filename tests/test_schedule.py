"""Tests for envforge.schedule module."""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta

import pytest

from envforge.schedule import ScheduleRule, ScheduleStore


# ---------------------------------------------------------------------------
# ScheduleRule unit tests
# ---------------------------------------------------------------------------

def test_rule_roundtrip():
    rule = ScheduleRule(name="dev", keys=["PATH", "HOME"], interval_minutes=30, tags=["ci"])
    restored = ScheduleRule.from_dict(rule.to_dict())
    assert restored.name == "dev"
    assert restored.keys == ["PATH", "HOME"]
    assert restored.interval_minutes == 30
    assert restored.tags == ["ci"]


def test_is_due_never_run():
    rule = ScheduleRule(name="x", interval_minutes=60)
    assert rule.is_due() is True


def test_is_due_recent():
    now = datetime.utcnow()
    rule = ScheduleRule(name="x", interval_minutes=60, last_run=(now - timedelta(minutes=10)).isoformat())
    assert rule.is_due(now) is False


def test_is_due_elapsed():
    now = datetime.utcnow()
    rule = ScheduleRule(name="x", interval_minutes=60, last_run=(now - timedelta(minutes=61)).isoformat())
    assert rule.is_due(now) is True


def test_mark_run_sets_last_run():
    rule = ScheduleRule(name="x")
    assert rule.last_run is None
    now = datetime.utcnow()
    rule.mark_run(now)
    assert rule.last_run == now.isoformat()
    assert rule.is_due(now) is False


# ---------------------------------------------------------------------------
# ScheduleStore tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def store_path(tmp_path):
    return str(tmp_path / "schedule.json")


def test_store_empty_on_missing_file(store_path):
    ss = ScheduleStore(store_path)
    assert ss.rules == []


def test_store_add_and_persist(store_path):
    ss = ScheduleStore(store_path)
    rule = ScheduleRule(name="prod", interval_minutes=120)
    ss.add(rule)
    ss2 = ScheduleStore(store_path)
    assert len(ss2.rules) == 1
    assert ss2.rules[0].name == "prod"


def test_store_add_overwrites_same_name(store_path):
    ss = ScheduleStore(store_path)
    ss.add(ScheduleRule(name="a", interval_minutes=30))
    ss.add(ScheduleRule(name="a", interval_minutes=90))
    assert len(ss.rules) == 1
    assert ss.rules[0].interval_minutes == 90


def test_store_remove_existing(store_path):
    ss = ScheduleStore(store_path)
    ss.add(ScheduleRule(name="a"))
    result = ss.remove("a")
    assert result is True
    assert ss.get("a") is None


def test_store_remove_missing(store_path):
    ss = ScheduleStore(store_path)
    result = ss.remove("nonexistent")
    assert result is False


def test_store_due_rules(store_path):
    now = datetime.utcnow()
    ss = ScheduleStore(store_path)
    ss.add(ScheduleRule(name="due", interval_minutes=60))  # never run -> due
    ss.add(ScheduleRule(
        name="not_due",
        interval_minutes=60,
        last_run=(now - timedelta(minutes=5)).isoformat(),
    ))
    due = ss.due_rules(now)
    assert len(due) == 1
    assert due[0].name == "due"


def test_store_get_returns_none_for_missing(store_path):
    ss = ScheduleStore(store_path)
    assert ss.get("ghost") is None
