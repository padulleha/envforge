"""Tests for envforge.pin module."""

import pytest

from envforge.pin import (
    PinnedKey,
    add_pin,
    remove_pin,
    apply_pins,
    list_pins,
    format_pins,
)


def test_pinned_key_roundtrip():
    pk = PinnedKey(key="FOO", value="bar", reason="testing")
    assert PinnedKey.from_dict(pk.to_dict()) == pk


def test_pinned_key_defaults():
    pk = PinnedKey.from_dict({"key": "X", "value": "1"})
    assert pk.reason == ""


def test_add_pin_new_key():
    pins = add_pin([], "FOO", "bar")
    assert len(pins) == 1
    assert pins[0]["key"] == "FOO"
    assert pins[0]["value"] == "bar"


def test_add_pin_updates_existing():
    pins = add_pin([], "FOO", "old")
    pins = add_pin(pins, "FOO", "new", reason="updated")
    assert len(pins) == 1
    assert pins[0]["value"] == "new"
    assert pins[0]["reason"] == "updated"


def test_add_pin_sorted():
    pins = add_pin([], "Z", "1")
    pins = add_pin(pins, "A", "2")
    assert pins[0]["key"] == "A"
    assert pins[1]["key"] == "Z"


def test_add_pin_empty_key_raises():
    with pytest.raises(ValueError, match="empty"):
        add_pin([], "", "value")


def test_remove_pin_present():
    pins = add_pin([], "FOO", "bar")
    pins = remove_pin(pins, "FOO")
    assert pins == []


def test_remove_pin_missing_raises():
    with pytest.raises(KeyError, match="FOO"):
        remove_pin([], "FOO")


def test_apply_pins_overrides():
    env = {"FOO": "original", "BAR": "keep"}
    pins = [{"key": "FOO", "value": "pinned", "reason": ""}]
    result = apply_pins(env, pins)
    assert result["FOO"] == "pinned"
    assert result["BAR"] == "keep"


def test_apply_pins_adds_missing_key():
    env = {"BAR": "x"}
    pins = [{"key": "NEW", "value": "y", "reason": ""}]
    result = apply_pins(env, pins)
    assert result["NEW"] == "y"


def test_apply_pins_does_not_mutate_original():
    env = {"FOO": "original"}
    pins = [{"key": "FOO", "value": "pinned", "reason": ""}]
    apply_pins(env, pins)
    assert env["FOO"] == "original"


def test_list_pins_returns_objects():
    pins = add_pin([], "FOO", "bar", reason="r")
    result = list_pins(pins)
    assert len(result) == 1
    assert isinstance(result[0], PinnedKey)
    assert result[0].reason == "r"


def test_format_pins_empty():
    assert format_pins([]) == "(no pinned keys)"


def test_format_pins_contains_key_and_value():
    pins = add_pin([], "FOO", "bar", reason="why")
    output = format_pins(pins)
    assert "FOO" in output
    assert "bar" in output
    assert "why" in output


def test_format_pins_no_reason_no_hash():
    pins = add_pin([], "FOO", "bar")
    output = format_pins(pins)
    assert "#" not in output
