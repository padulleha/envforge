"""Tests for envforge.snapshot_patch."""

import pytest

from envforge.snapshot import Snapshot
from envforge.snapshot_patch import PatchResult, apply_patch


def _snap(variables=None, tags=None):
    return Snapshot(
        name="test-snap",
        variables=variables or {"A": "1", "B": "2"},
        tags=tags or [],
    )


# ---------------------------------------------------------------------------
# PatchResult helpers
# ---------------------------------------------------------------------------

def test_patch_result_str_no_changes():
    r = PatchResult(name="s")
    assert "no changes" in str(r)


def test_patch_result_str_shows_added():
    r = PatchResult(name="s", added=["X"])
    assert "added: X" in str(r)


def test_patch_result_str_shows_all_categories():
    r = PatchResult(name="s", added=["X"], updated=["A"], removed=["B"], skipped=["C"])
    text = str(r)
    assert "added" in text
    assert "updated" in text
    assert "removed" in text
    assert "skipped" in text


def test_patch_result_has_changes_true():
    r = PatchResult(name="s", added=["X"])
    assert r.has_changes is True


def test_patch_result_has_changes_false_skipped_only():
    r = PatchResult(name="s", skipped=["X"])
    assert r.has_changes is False


# ---------------------------------------------------------------------------
# apply_patch — set_keys
# ---------------------------------------------------------------------------

def test_patch_adds_new_key():
    snap = _snap()
    new_snap, result = apply_patch(snap, set_keys={"C": "3"})
    assert new_snap.variables["C"] == "3"
    assert "C" in result.added


def test_patch_updates_existing_key():
    snap = _snap()
    new_snap, result = apply_patch(snap, set_keys={"A": "99"})
    assert new_snap.variables["A"] == "99"
    assert "A" in result.updated


def test_patch_skips_existing_key_when_no_overwrite():
    snap = _snap()
    new_snap, result = apply_patch(snap, set_keys={"A": "99"}, overwrite=False)
    assert new_snap.variables["A"] == "1"  # unchanged
    assert "A" in result.skipped
    assert "A" not in result.updated


def test_patch_does_not_mutate_original():
    snap = _snap()
    apply_patch(snap, set_keys={"A": "99"})
    assert snap.variables["A"] == "1"


# ---------------------------------------------------------------------------
# apply_patch — delete_keys
# ---------------------------------------------------------------------------

def test_patch_removes_existing_key():
    snap = _snap()
    new_snap, result = apply_patch(snap, delete_keys=["A"])
    assert "A" not in new_snap.variables
    assert "A" in result.removed


def test_patch_skips_missing_delete_key():
    snap = _snap()
    _, result = apply_patch(snap, delete_keys=["Z"])
    assert "Z" in result.skipped


# ---------------------------------------------------------------------------
# apply_patch — combined
# ---------------------------------------------------------------------------

def test_patch_set_and_delete_together():
    snap = _snap()
    new_snap, result = apply_patch(snap, set_keys={"C": "3"}, delete_keys=["B"])
    assert "C" in new_snap.variables
    assert "B" not in new_snap.variables
    assert result.has_changes


def test_patch_preserves_tags_and_description():
    snap = Snapshot(name="s", variables={"A": "1"}, tags=["prod"], description="hello")
    new_snap, _ = apply_patch(snap, set_keys={"B": "2"})
    assert new_snap.tags == ["prod"]
    assert new_snap.description == "hello"


def test_patch_empty_inputs_returns_identical_vars():
    snap = _snap()
    new_snap, result = apply_patch(snap)
    assert new_snap.variables == snap.variables
    assert not result.has_changes
