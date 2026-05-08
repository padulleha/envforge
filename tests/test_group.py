"""Tests for envforge.group."""
from __future__ import annotations

import pytest

from envforge.group import (
    SnapshotGroup,
    add_to_group,
    format_groups,
    get_group,
    groups_for_snapshot,
    remove_from_group,
)


# ---------------------------------------------------------------------------
# SnapshotGroup dataclass
# ---------------------------------------------------------------------------

def test_group_roundtrip():
    g = SnapshotGroup(name="prod", description="Production envs", members=["web", "api"])
    assert SnapshotGroup.from_dict(g.to_dict()) == g


def test_group_defaults():
    g = SnapshotGroup(name="dev")
    assert g.description == ""
    assert g.members == []


def test_to_dict_members_sorted():
    g = SnapshotGroup(name="x", members=["b", "a"])
    assert g.to_dict()["members"] == ["a", "b"]


# ---------------------------------------------------------------------------
# add_to_group
# ---------------------------------------------------------------------------

def test_add_to_group_creates_new_group():
    groups = add_to_group([], "prod", "web")
    assert len(groups) == 1
    assert groups[0].name == "prod"
    assert "web" in groups[0].members


def test_add_to_group_existing_group_appends():
    groups = [SnapshotGroup(name="prod", members=["api"])]
    groups = add_to_group(groups, "prod", "web")
    assert set(groups[0].members) == {"api", "web"}


def test_add_to_group_no_duplicates():
    groups = [SnapshotGroup(name="prod", members=["api"])]
    groups = add_to_group(groups, "prod", "api")
    assert groups[0].members.count("api") == 1


def test_add_to_group_sorted_members():
    groups = add_to_group([], "g", "z")
    groups = add_to_group(groups, "g", "a")
    assert groups[0].members == ["a", "z"]


def test_add_to_group_groups_sorted_by_name():
    groups = add_to_group([], "z", "s1")
    groups = add_to_group(groups, "a", "s2")
    assert groups[0].name == "a"


def test_add_to_group_empty_group_name_raises():
    with pytest.raises(ValueError):
        add_to_group([], "", "snap")


def test_add_to_group_empty_snapshot_name_raises():
    with pytest.raises(ValueError):
        add_to_group([], "grp", "")


# ---------------------------------------------------------------------------
# remove_from_group
# ---------------------------------------------------------------------------

def test_remove_from_group_present():
    groups = [SnapshotGroup(name="prod", members=["api", "web"])]
    groups = remove_from_group(groups, "prod", "api")
    assert "api" not in groups[0].members


def test_remove_from_group_absent_noop():
    groups = [SnapshotGroup(name="prod", members=["web"])]
    groups = remove_from_group(groups, "prod", "missing")
    assert groups[0].members == ["web"]


def test_remove_from_nonexistent_group_noop():
    groups = [SnapshotGroup(name="prod", members=["web"])]
    result = remove_from_group(groups, "staging", "web")
    assert len(result) == 1


# ---------------------------------------------------------------------------
# get_group / groups_for_snapshot
# ---------------------------------------------------------------------------

def test_get_group_found():
    groups = [SnapshotGroup(name="prod"), SnapshotGroup(name="dev")]
    assert get_group(groups, "dev").name == "dev"


def test_get_group_not_found():
    assert get_group([], "x") is None


def test_groups_for_snapshot():
    groups = [
        SnapshotGroup(name="prod", members=["web", "api"]),
        SnapshotGroup(name="dev", members=["web"]),
        SnapshotGroup(name="other", members=["api"]),
    ]
    result = groups_for_snapshot(groups, "web")
    names = [g.name for g in result]
    assert "prod" in names and "dev" in names and "other" not in names


# ---------------------------------------------------------------------------
# format_groups
# ---------------------------------------------------------------------------

def test_format_groups_empty():
    assert format_groups([]) == "(no groups)"


def test_format_groups_contains_name_and_members():
    groups = [SnapshotGroup(name="prod", members=["api", "web"])]
    out = format_groups(groups)
    assert "prod" in out
    assert "api" in out
    assert "web" in out


def test_format_groups_shows_description():
    groups = [SnapshotGroup(name="prod", description="Live", members=["api"])]
    assert "Live" in format_groups(groups)


def test_format_groups_empty_group_label():
    groups = [SnapshotGroup(name="empty")]
    assert "(empty)" in format_groups(groups)
