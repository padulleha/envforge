"""Tests for envforge.annotate."""
import pytest
from envforge.annotate import (
    Annotation,
    add_annotation,
    get_annotations,
    remove_annotations,
    annotations_to_dict,
    annotations_from_dict,
)


# ---------------------------------------------------------------------------
# Annotation dataclass
# ---------------------------------------------------------------------------

def test_annotation_roundtrip():
    a = Annotation(snapshot_name="prod", note="initial deploy", author="alice")
    restored = Annotation.from_dict(a.to_dict())
    assert restored.snapshot_name == a.snapshot_name
    assert restored.note == a.note
    assert restored.author == a.author
    assert restored.created_at == a.created_at


def test_annotation_defaults():
    a = Annotation(snapshot_name="dev", note="test")
    assert a.author is None
    assert a.created_at  # should be set automatically


def test_annotation_format_with_author():
    a = Annotation(snapshot_name="s", note="hello", author="bob", created_at="2024-01-01T00:00:00+00:00")
    fmt = a.format()
    assert "[bob]" in fmt
    assert "hello" in fmt
    assert "2024-01-01" in fmt


def test_annotation_format_no_author():
    a = Annotation(snapshot_name="s", note="world", created_at="2024-06-01T12:00:00+00:00")
    fmt = a.format()
    assert "[" not in fmt
    assert "world" in fmt


# ---------------------------------------------------------------------------
# add_annotation
# ---------------------------------------------------------------------------

def test_add_annotation_appends():
    result = add_annotation([], "prod", "first note")
    assert len(result) == 1
    assert result[0].note == "first note"


def test_add_annotation_does_not_mutate_original():
    original: list = []
    add_annotation(original, "prod", "note")
    assert original == []


def test_add_annotation_empty_note_raises():
    with pytest.raises(ValueError, match="empty"):
        add_annotation([], "prod", "   ")


def test_add_annotation_strips_whitespace():
    result = add_annotation([], "prod", "  trimmed  ")
    assert result[0].note == "trimmed"


# ---------------------------------------------------------------------------
# get_annotations
# ---------------------------------------------------------------------------

def test_get_annotations_filters_by_name():
    base = add_annotation([], "prod", "note A")
    base = add_annotation(base, "dev", "note B")
    base = add_annotation(base, "prod", "note C")
    prod_notes = get_annotations(base, "prod")
    assert len(prod_notes) == 2
    assert all(a.snapshot_name == "prod" for a in prod_notes)


def test_get_annotations_empty_result():
    base = add_annotation([], "prod", "note")
    assert get_annotations(base, "staging") == []


# ---------------------------------------------------------------------------
# remove_annotations
# ---------------------------------------------------------------------------

def test_remove_annotations_removes_all_for_snapshot():
    base = add_annotation([], "prod", "note A")
    base = add_annotation(base, "dev", "note B")
    base = add_annotation(base, "prod", "note C")
    result = remove_annotations(base, "prod")
    assert all(a.snapshot_name != "prod" for a in result)
    assert len(result) == 1
    assert result[0].snapshot_name == "dev"


def test_remove_annotations_does_not_mutate_original():
    base = add_annotation([], "prod", "note")
    remove_annotations(base, "prod")
    assert len(base) == 1


def test_remove_annotations_nonexistent_snapshot_returns_unchanged():
    base = add_annotation([], "prod", "note")
    result = remove_annotations(base, "staging")
    assert len(result) == 1
    assert result[0].snapshot_name == "prod"


# ---------------------------------------------------------------------------
# annotations_to_dict / annotations_from_dict
# ---------------------------------------------------------------------------

def test_annotations_roundtrip_serialization():
    base = add_annotation([], "prod", "note A", author="alice")
    base = add_annotation(base, "dev", "note B")
    data = annotations_to_dict(base)
    restored = annotations_from_dict(data)
    assert len(restored) == 2
    assert restored[0].note == "note A"
    assert restored[0].author == "alice"
    assert restored[1].snapshot_name == "dev"


def test_annotations_from_dict_empty():
    assert annotations_from_dict([]) == []
