"""Tests for envforge.snapshot_score."""
from __future__ import annotations

import pytest

from envforge.snapshot import Snapshot
from envforge.snapshot_score import (
    ScoreBreakdown,
    SnapshotScore,
    _grade,
    _unique_prefixes,
    score_snapshot,
)


def _snap(name: str = "test", variables: dict | None = None, **kwargs) -> Snapshot:
    return Snapshot(
        name=name,
        variables=variables or {},
        **kwargs,
    )


# --- unit helpers ---

def test_grade_boundaries():
    assert _grade(100) == "A"
    assert _grade(90) == "A"
    assert _grade(89) == "B"
    assert _grade(75) == "B"
    assert _grade(74) == "C"
    assert _grade(55) == "C"
    assert _grade(54) == "D"
    assert _grade(35) == "D"
    assert _grade(34) == "F"
    assert _grade(0) == "F"


def test_unique_prefixes_empty():
    assert _unique_prefixes([]) == 0


def test_unique_prefixes_single():
    assert _unique_prefixes(["HOME"]) == 1


def test_unique_prefixes_deduped():
    keys = ["APP_HOST", "APP_PORT", "DB_HOST", "DB_PASS"]
    assert _unique_prefixes(keys) == 2


# --- score_snapshot ---

def test_score_empty_snapshot_is_zero():
    snap = _snap(variables={})
    result = score_snapshot(snap)
    assert result.score == 0.0
    assert result.breakdown.key_count == 0


def test_score_breakdown_key_count():
    snap = _snap(variables={"A": "1", "B": "2"})
    result = score_snapshot(snap)
    assert result.breakdown.key_count == 2


def test_score_non_empty_ratio_all_filled():
    snap = _snap(variables={"A": "x", "B": "y"})
    result = score_snapshot(snap)
    assert result.breakdown.non_empty_ratio == pytest.approx(1.0)


def test_score_non_empty_ratio_partial():
    snap = _snap(variables={"A": "x", "B": ""})
    result = score_snapshot(snap)
    assert result.breakdown.non_empty_ratio == pytest.approx(0.5)


def test_score_has_description_true():
    snap = _snap(variables={"A": "1"})
    snap.description = "A useful snapshot"
    result = score_snapshot(snap)
    assert result.breakdown.has_description is True


def test_score_has_description_false():
    snap = _snap(variables={"A": "1"})
    result = score_snapshot(snap)
    assert result.breakdown.has_description is False


def test_score_has_tags_true():
    snap = _snap(variables={"A": "1"})
    snap.tags = ["prod"]
    result = score_snapshot(snap)
    assert result.breakdown.has_tags is True


def test_score_increases_with_more_keys():
    small = _snap(variables={"A": "1"})
    large = _snap(variables={f"K{i}": str(i) for i in range(20)})
    assert score_snapshot(large).score > score_snapshot(small).score


def test_score_summary_contains_name():
    snap = _snap(name="mysnap", variables={"A": "1"})
    result = score_snapshot(snap)
    assert "mysnap" in result.summary()


def test_score_format_text_contains_breakdown_labels():
    snap = _snap(name="s", variables={"A": "1"})
    text = score_snapshot(snap).format_text()
    assert "Keys" in text
    assert "Non-empty" in text
    assert "description" in text
    assert "tags" in text
    assert "prefixes" in text


def test_score_breakdown_to_dict_keys():
    b = ScoreBreakdown(key_count=5, non_empty_ratio=0.8, has_description=True, has_tags=False, unique_prefix_count=3)
    d = b.to_dict()
    assert set(d.keys()) == {"key_count", "non_empty_ratio", "has_description", "has_tags", "unique_prefix_count"}


def test_score_max_capped_at_100():
    snap = _snap(variables={f"APP_KEY_{i}": f"val{i}" for i in range(50)})
    snap.description = "full"
    snap.tags = ["t"]
    result = score_snapshot(snap)
    assert result.score <= 100.0
