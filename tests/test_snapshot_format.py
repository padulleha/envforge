"""Tests for envforge.snapshot_format."""
from __future__ import annotations

import pytest

from envforge.snapshot import Snapshot
from envforge.snapshot_format import (
    FormatOptions,
    _infer_type,
    _truncate,
    format_compact,
    format_table,
)


def _snap(name: str = "test", **variables: str) -> Snapshot:
    s = Snapshot(name=name)
    s.variables = dict(variables)
    return s


# --- unit helpers ---

def test_truncate_short_string_unchanged():
    assert _truncate("hello", 10) == "hello"


def test_truncate_long_string_ends_with_ellipsis():
    result = _truncate("abcdefghij", 7)
    assert result == "abcd..."
    assert len(result) == 7


def test_truncate_exact_length_unchanged():
    assert _truncate("hello", 5) == "hello"


def test_infer_type_bool_true():
    assert _infer_type("true") == "bool"
    assert _infer_type("True") == "bool"


def test_infer_type_bool_false():
    assert _infer_type("false") == "bool"


def test_infer_type_int():
    assert _infer_type("42") == "int"
    assert _infer_type("-7") == "int"


def test_infer_type_float():
    assert _infer_type("3.14") == "float"


def test_infer_type_str():
    assert _infer_type("hello") == "str"


# --- FormatOptions roundtrip ---

def test_format_options_roundtrip():
    opts = FormatOptions(max_value_length=40, show_index=False, show_types=True, title="My Title")
    restored = FormatOptions.from_dict(opts.to_dict())
    assert restored.max_value_length == 40
    assert restored.show_index is False
    assert restored.show_types is True
    assert restored.title == "My Title"


def test_format_options_defaults():
    opts = FormatOptions.from_dict({})
    assert opts.max_value_length == 60
    assert opts.show_index is True
    assert opts.show_types is False
    assert opts.title is None


# --- format_compact ---

def test_compact_empty_snapshot_returns_empty_string():
    snap = _snap("empty")
    assert format_compact(snap) == ""


def test_compact_output_contains_key_value_pairs():
    snap = _snap("s", FOO="bar", BAZ="qux")
    result = format_compact(snap)
    assert "FOO=bar" in result
    assert "BAZ=qux" in result


def test_compact_output_is_sorted():
    snap = _snap("s", Z="last", A="first")
    lines = format_compact(snap).splitlines()
    assert lines[0].startswith("A=")
    assert lines[1].startswith("Z=")


# --- format_table ---

def test_table_empty_snapshot_returns_message():
    snap = _snap("empty")
    result = format_table(snap)
    assert "no variables" in result


def test_table_contains_key_and_value():
    snap = _snap("s", MY_VAR="hello")
    result = format_table(snap)
    assert "MY_VAR" in result
    assert "hello" in result


def test_table_contains_header_row():
    snap = _snap("s", X="1")
    result = format_table(snap)
    assert "KEY" in result
    assert "VALUE" in result


def test_table_custom_title():
    snap = _snap("s", X="1")
    opts = FormatOptions(title="Custom Title")
    result = format_table(snap, opts)
    assert "Custom Title" in result


def test_table_show_types_adds_type_column():
    snap = _snap("s", PORT="8080", DEBUG="true")
    opts = FormatOptions(show_types=True)
    result = format_table(snap, opts)
    assert "TYPE" in result
    assert "int" in result
    assert "bool" in result


def test_table_value_truncated_when_long():
    snap = _snap("s", LONG="x" * 100)
    opts = FormatOptions(max_value_length=20)
    result = format_table(snap, opts)
    assert "..." in result


def test_table_no_index_omits_numbers():
    snap = _snap("s", A="1", B="2")
    opts = FormatOptions(show_index=False)
    result = format_table(snap, opts)
    # Row numbers would appear as leading digits before the pipe
    for line in result.splitlines():
        stripped = line.strip()
        if stripped.startswith("|"):
            # Should not have a leading number before the first pipe
            assert not line[0].isdigit()
