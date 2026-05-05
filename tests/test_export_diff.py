"""Tests for envforge export and diff modules."""

import os
import pytest

from envforge.snapshot import Snapshot
from envforge.export import to_shell_export, to_dotenv
from envforge.diff import diff_snapshots, diff_snapshot_with_env, SnapshotDiff


@pytest.fixture
def snap_a():
    return Snapshot(name="a", variables={"FOO": "bar", "SHARED": "same", "OLD": "gone"})


@pytest.fixture
def snap_b():
    return Snapshot(name="b", variables={"FOO": "baz", "SHARED": "same", "NEW": "arrived"})


# --- Export tests ---

def test_shell_export_bash_contains_export(snap_a):
    result = to_shell_export(snap_a, shell="bash")
    assert "export FOO='bar'" in result
    assert "export SHARED='same'" in result


def test_shell_export_fish_format(snap_a):
    result = to_shell_export(snap_a, shell="fish")
    assert "set -x FOO 'bar'" in result


def test_shell_export_powershell_format(snap_a):
    result = to_shell_export(snap_a, shell="powershell")
    assert "$env:FOO = 'bar'" in result


def test_shell_export_unsupported_shell(snap_a):
    with pytest.raises(ValueError, match="Unsupported shell"):
        to_shell_export(snap_a, shell="tcsh")


def test_shell_export_escapes_single_quotes():
    snap = Snapshot(name="q", variables={"VAR": "it's here"})
    result = to_shell_export(snap, shell="bash")
    assert "it'\"'\"'s here" in result


def test_dotenv_simple(snap_a):
    result = to_dotenv(snap_a)
    assert "FOO=bar" in result
    assert "SHARED=same" in result


def test_dotenv_quotes_values_with_spaces():
    snap = Snapshot(name="s", variables={"MSG": "hello world"})
    result = to_dotenv(snap)
    assert 'MSG="hello world"' in result


def test_dotenv_includes_snapshot_name(snap_a):
    result = to_dotenv(snap_a)
    assert "# envforge snapshot: a" in result


# --- Diff tests ---

def test_diff_added(snap_a, snap_b):
    d = diff_snapshots(snap_a, snap_b)
    assert "NEW" in d.added
    assert d.added["NEW"] == "arrived"


def test_diff_removed(snap_a, snap_b):
    d = diff_snapshots(snap_a, snap_b)
    assert "OLD" in d.removed


def test_diff_changed(snap_a, snap_b):
    d = diff_snapshots(snap_a, snap_b)
    assert "FOO" in d.changed
    assert d.changed["FOO"] == ("bar", "baz")


def test_diff_unchanged(snap_a, snap_b):
    d = diff_snapshots(snap_a, snap_b)
    assert "SHARED" in d.unchanged


def test_diff_has_changes(snap_a, snap_b):
    d = diff_snapshots(snap_a, snap_b)
    assert d.has_changes is True


def test_diff_no_changes():
    snap = Snapshot(name="x", variables={"A": "1"})
    d = diff_snapshots(snap, snap)
    assert not d.has_changes
    assert "No differences" in d.summary()


def test_diff_format_text_masks_values(snap_a, snap_b):
    d = diff_snapshots(snap_a, snap_b)
    text = d.format_text(mask_values=True)
    assert "***" in text
    assert "baz" not in text


def test_diff_with_env():
    snap = Snapshot(name="env_test", variables={"ENVFORGE_TEST_VAR": "expected"})
    fake_env = {"ENVFORGE_TEST_VAR": "different", "EXTRA": "yes"}
    d = diff_snapshot_with_env(snap, env=fake_env)
    assert "ENVFORGE_TEST_VAR" in d.changed
    assert "EXTRA" in d.added
