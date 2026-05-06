"""Tests for envforge.alias module."""

import pytest
from envforge.alias import (
    SnapshotAlias,
    add_alias,
    remove_alias,
    resolve_alias,
    format_aliases,
)


def test_alias_roundtrip():
    a = SnapshotAlias(alias="prod", snapshot_name="production-2024", description="live env")
    assert SnapshotAlias.from_dict(a.to_dict()) == a


def test_alias_defaults():
    a = SnapshotAlias.from_dict({"alias": "dev", "snapshot_name": "dev-local"})
    assert a.description == ""


def test_add_alias_new():
    result = add_alias([], "prod", "production-2024")
    assert len(result) == 1
    assert result[0].alias == "prod"
    assert result[0].snapshot_name == "production-2024"


def test_add_alias_updates_existing():
    existing = add_alias([], "prod", "old-snapshot")
    updated = add_alias(existing, "prod", "new-snapshot")
    assert len(updated) == 1
    assert updated[0].snapshot_name == "new-snapshot"


def test_add_alias_sorted():
    aliases = add_alias([], "zebra", "z-snap")
    aliases = add_alias(aliases, "alpha", "a-snap")
    assert [a.alias for a in aliases] == ["alpha", "zebra"]


def test_add_alias_empty_name_raises():
    with pytest.raises(ValueError, match="empty"):
        add_alias([], "", "some-snap")


def test_add_alias_empty_snapshot_raises():
    with pytest.raises(ValueError, match="empty"):
        add_alias([], "prod", "")


def test_remove_alias_present():
    aliases = add_alias([], "prod", "production-2024")
    aliases = remove_alias(aliases, "prod")
    assert aliases == []


def test_remove_alias_missing_raises():
    with pytest.raises(KeyError, match="prod"):
        remove_alias([], "prod")


def test_resolve_alias_found():
    aliases = add_alias([], "prod", "production-2024")
    assert resolve_alias(aliases, "prod") == "production-2024"


def test_resolve_alias_not_found():
    assert resolve_alias([], "missing") is None


def test_format_aliases_empty():
    assert "no aliases" in format_aliases([])


def test_format_aliases_shows_arrow():
    aliases = add_alias([], "prod", "production-2024", description="live")
    output = format_aliases(aliases)
    assert "prod -> production-2024" in output
    assert "live" in output


def test_format_aliases_no_description():
    aliases = add_alias([], "dev", "dev-local")
    output = format_aliases(aliases)
    assert "#" not in output
