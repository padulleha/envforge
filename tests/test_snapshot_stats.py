"""Tests for envforge.snapshot_stats and envforge.cli_stats."""
from __future__ import annotations

import argparse
import pytest

from envforge.snapshot import Snapshot
from envforge.snapshot_stats import compute_stats, multi_summary
from envforge.cli_stats import cmd_stats


def _snap(name: str, env: dict, tags=None, description="") -> Snapshot:
    s = Snapshot(name=name, env_vars=env)
    s.tags = tags or []
    s.description = description
    return s


def test_compute_stats_key_count():
    s = _snap("s", {"A": "1", "BB": "22", "CCC": "333"})
    st = compute_stats(s)
    assert st.key_count == 3


def test_compute_stats_empty_snapshot():
    s = _snap("empty", {})
    st = compute_stats(s)
    assert st.key_count == 0
    assert st.avg_value_length == 0.0
    assert st.longest_key == ""
    assert st.shortest_key == ""


def test_compute_stats_empty_value_count():
    s = _snap("s", {"A": "", "B": "hello", "C": ""})
    st = compute_stats(s)
    assert st.empty_value_count == 2


def test_compute_stats_avg_value_length():
    s = _snap("s", {"A": "ab", "B": "abcd"})  # lengths 2 and 4 -> avg 3.0
    st = compute_stats(s)
    assert st.avg_value_length == pytest.approx(3.0)


def test_compute_stats_longest_and_shortest_key():
    s = _snap("s", {"X": "1", "LONGKEY": "2", "MID": "3"})
    st = compute_stats(s)
    assert st.longest_key == "LONGKEY"
    assert st.shortest_key == "X"


def test_compute_stats_tag_count():
    s = _snap("s", {"A": "1"}, tags=["prod", "web"])
    st = compute_stats(s)
    assert st.tag_count == 2


def test_compute_stats_has_description_true():
    s = _snap("s", {"A": "1"}, description="my desc")
    st = compute_stats(s)
    assert st.has_description is True


def test_compute_stats_has_description_false():
    s = _snap("s", {"A": "1"})
    st = compute_stats(s)
    assert st.has_description is False


def test_summary_contains_name():
    s = _snap("mysnap", {"K": "val"})
    st = compute_stats(s)
    assert "mysnap" in st.summary()


def test_multi_summary_returns_all():
    snaps = [_snap("a", {"K": "1"}), _snap("b", {"X": "2", "Y": "3"})]
    result = multi_summary(snaps)
    assert set(result.keys()) == {"a", "b"}
    assert result["b"].key_count == 2


# --- CLI tests ---

class _FakeStore:
    def __init__(self, snaps):
        self._snaps = {s.name: s for s in snaps}

    def get(self, name):
        return self._snaps.get(name)

    def list(self):
        return list(self._snaps.keys())


def _make_args(name=None, store=None):
    ns = argparse.Namespace(name=name, store=store or "unused")
    return ns


def test_cmd_stats_single_snapshot(capsys, monkeypatch):
    snap = _snap("dev", {"FOO": "bar"})
    fake = _FakeStore([snap])
    monkeypatch.setattr("envforge.cli_stats.get_store", lambda _: fake)
    rc = cmd_stats(_make_args(name="dev"))
    out = capsys.readouterr().out
    assert rc == 0
    assert "dev" in out
    assert "Keys" in out


def test_cmd_stats_missing_snapshot(capsys, monkeypatch):
    fake = _FakeStore([])
    monkeypatch.setattr("envforge.cli_stats.get_store", lambda _: fake)
    rc = cmd_stats(_make_args(name="ghost"))
    assert rc == 1


def test_cmd_stats_all_snapshots(capsys, monkeypatch):
    snaps = [_snap("a", {"K": "1"}), _snap("b", {"X": "2"})]
    fake = _FakeStore(snaps)
    monkeypatch.setattr("envforge.cli_stats.get_store", lambda _: fake)
    rc = cmd_stats(_make_args())
    out = capsys.readouterr().out
    assert rc == 0
    assert "a" in out
    assert "b" in out


def test_cmd_stats_no_snapshots(capsys, monkeypatch):
    fake = _FakeStore([])
    monkeypatch.setattr("envforge.cli_stats.get_store", lambda _: fake)
    rc = cmd_stats(_make_args())
    out = capsys.readouterr().out
    assert rc == 0
    assert "No snapshots" in out
