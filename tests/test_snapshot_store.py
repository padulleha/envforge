"""Tests for snapshot capture, serialization, and store persistence."""

import os
import json
import tempfile
from pathlib import Path

import pytest

from envforge.snapshot import Snapshot
from envforge.store import SnapshotStore


# --- Snapshot tests ---

def test_capture_all_env_vars(monkeypatch):
    monkeypatch.setenv("TEST_VAR", "hello")
    snap = Snapshot.capture("test")
    assert "TEST_VAR" in snap.variables
    assert snap.variables["TEST_VAR"] == "hello"


def test_capture_specific_keys(monkeypatch):
    monkeypatch.setenv("FOO", "foo_val")
    monkeypatch.setenv("BAR", "bar_val")
    snap = Snapshot.capture("partial", keys=["FOO"])
    assert "FOO" in snap.variables
    assert "BAR" not in snap.variables


def test_apply_sets_env_vars(monkeypatch):
    snap = Snapshot(name="apply_test", variables={"ENVFORGE_X": "42"})
    snap.apply()
    assert os.environ.get("ENVFORGE_X") == "42"


def test_apply_no_overwrite(monkeypatch):
    monkeypatch.setenv("KEEP_ME", "original")
    snap = Snapshot(name="no_overwrite", variables={"KEEP_ME": "new_value"})
    snap.apply(overwrite=False)
    assert os.environ["KEEP_ME"] == "original"


def test_serialization_roundtrip():
    snap = Snapshot(name="roundtrip", variables={"A": "1", "B": "2"}, description="test snap")
    data = snap.to_dict()
    restored = Snapshot.from_dict(data)
    assert restored.name == snap.name
    assert restored.variables == snap.variables
    assert restored.description == snap.description
    assert restored.created_at == snap.created_at


def test_diff():
    snap_a = Snapshot("a", {"X": "1", "Y": "old", "Z": "only_a"})
    snap_b = Snapshot("b", {"X": "1", "Y": "new", "W": "only_b"})
    diff = snap_a.diff(snap_b)
    assert "W" in diff["added"]
    assert "Z" in diff["removed"]
    assert "Y" in diff["changed"]
    assert diff["changed"]["Y"] == {"from": "old", "to": "new"}
    assert "X" not in diff["changed"]


# --- SnapshotStore tests ---

@pytest.fixture
def tmp_store(tmp_path):
    store_file = tmp_path / "snapshots.json"
    return SnapshotStore(store_path=store_file)


def test_save_and_get(tmp_store):
    snap = Snapshot("dev", {"DB_URL": "postgres://localhost/dev"})
    tmp_store.save(snap)
    result = tmp_store.get("dev")
    assert result is not None
    assert result.variables["DB_URL"] == "postgres://localhost/dev"


def test_delete(tmp_store):
    snap = Snapshot("to_delete", {"TMP": "1"})
    tmp_store.save(snap)
    assert tmp_store.exists("to_delete")
    deleted = tmp_store.delete("to_delete")
    assert deleted is True
    assert not tmp_store.exists("to_delete")


def test_delete_nonexistent(tmp_store):
    assert tmp_store.delete("ghost") is False


def test_list_all_sorted(tmp_store):
    snap1 = Snapshot("alpha", {}, created_at="2024-01-01T00:00:00")
    snap2 = Snapshot("beta", {}, created_at="2024-06-01T00:00:00")
    tmp_store.save(snap2)
    tmp_store.save(snap1)
    names = [s.name for s in tmp_store.list_all()]
    assert names == ["alpha", "beta"]


def test_persistence_across_instances(tmp_path):
    store_file = tmp_path / "snapshots.json"
    store1 = SnapshotStore(store_path=store_file)
    store1.save(Snapshot("persistent", {"KEY": "value"}))

    store2 = SnapshotStore(store_path=store_file)
    assert store2.exists("persistent")
    assert store2.get("persistent").variables["KEY"] == "value"
