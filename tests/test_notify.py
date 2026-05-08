"""Tests for envforge.notify and envforge.cli_notify."""
from __future__ import annotations

import json
import types
from pathlib import Path

import pytest

from envforge.notify import (
    NotificationRule,
    dispatch,
    get_handler,
    register_handler,
)
from envforge.cli_notify import (
    _load_rules,
    _rules_path,
    cmd_notify_add,
    cmd_notify_list,
    cmd_notify_remove,
)


# ---------------------------------------------------------------------------
# NotificationRule unit tests
# ---------------------------------------------------------------------------

def test_rule_roundtrip():
    rule = NotificationRule(event="capture", handler="shell", snapshot_filter="prod-*", detail="echo {event}")
    assert NotificationRule.from_dict(rule.to_dict()) == rule


def test_rule_defaults():
    rule = NotificationRule(event="apply", handler="shell")
    assert rule.snapshot_filter is None
    assert rule.detail == ""


def test_rule_matches_event_and_glob():
    rule = NotificationRule(event="capture", handler="shell", snapshot_filter="prod-*")
    assert rule.matches("capture", "prod-api")
    assert not rule.matches("capture", "dev-api")
    assert not rule.matches("apply", "prod-api")


def test_rule_matches_no_filter():
    rule = NotificationRule(event="delete", handler="shell")
    assert rule.matches("delete", "anything")
    assert not rule.matches("capture", "anything")


# ---------------------------------------------------------------------------
# dispatch tests
# ---------------------------------------------------------------------------

def test_dispatch_invokes_matching_handler():
    calls = []
    register_handler("_test_handler", lambda e, s, d: calls.append((e, s, d)))
    rules = [NotificationRule(event="capture", handler="_test_handler")]
    invoked = dispatch(rules, "capture", "my-snap")
    assert invoked == ["_test_handler"]
    assert calls == [("capture", "my-snap", None)]


def test_dispatch_skips_non_matching():
    calls = []
    register_handler("_test2", lambda e, s, d: calls.append(e))
    rules = [NotificationRule(event="apply", handler="_test2")]
    dispatch(rules, "capture", "snap")
    assert calls == []


def test_dispatch_unknown_handler_is_skipped():
    rules = [NotificationRule(event="capture", handler="__nonexistent__")]
    invoked = dispatch(rules, "capture", "snap")
    assert invoked == []


# ---------------------------------------------------------------------------
# CLI command tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_store(tmp_path):
    store_file = tmp_path / "store" / "snapshots.json"
    store_file.parent.mkdir(parents=True)
    store_file.write_text("{}")
    return str(store_file)


def _make_args(store, **kwargs):
    ns = types.SimpleNamespace(store=store)
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def test_notify_add_creates_rule(tmp_store):
    args = _make_args(tmp_store, event="capture", handler="shell", filter=None, detail="echo hi")
    rc = cmd_notify_add(args)
    assert rc == 0
    rules = _load_rules(tmp_store)
    assert len(rules) == 1
    assert rules[0].event == "capture"
    assert rules[0].handler == "shell"
    assert rules[0].detail == "echo hi"


def test_notify_list_empty(tmp_store, capsys):
    args = _make_args(tmp_store)
    rc = cmd_notify_list(args)
    assert rc == 0
    assert "No notification rules" in capsys.readouterr().out


def test_notify_remove_existing(tmp_store):
    add_args = _make_args(tmp_store, event="apply", handler="shell", filter=None, detail="")
    cmd_notify_add(add_args)
    rm_args = _make_args(tmp_store, event="apply", handler="shell")
    rc = cmd_notify_remove(rm_args)
    assert rc == 0
    assert _load_rules(tmp_store) == []


def test_notify_remove_missing_returns_error(tmp_store):
    args = _make_args(tmp_store, event="delete", handler="shell")
    rc = cmd_notify_remove(args)
    assert rc == 1
