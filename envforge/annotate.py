"""Snapshot annotation support — attach freeform notes to snapshots."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class Annotation:
    snapshot_name: str
    note: str
    author: Optional[str] = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        return {
            "snapshot_name": self.snapshot_name,
            "note": self.note,
            "author": self.author,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Annotation":
        return cls(
            snapshot_name=data["snapshot_name"],
            note=data["note"],
            author=data.get("author"),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
        )

    def format(self) -> str:
        author_part = f" [{self.author}]" if self.author else ""
        return f"{self.created_at}{author_part}: {self.note}"


def add_annotation(
    annotations: List[Annotation],
    snapshot_name: str,
    note: str,
    author: Optional[str] = None,
) -> List[Annotation]:
    """Append a new annotation for *snapshot_name* and return the updated list."""
    if not note.strip():
        raise ValueError("Annotation note must not be empty.")
    entry = Annotation(snapshot_name=snapshot_name, note=note.strip(), author=author)
    return annotations + [entry]


def get_annotations(annotations: List[Annotation], snapshot_name: str) -> List[Annotation]:
    """Return all annotations for the given snapshot, oldest first."""
    return [a for a in annotations if a.snapshot_name == snapshot_name]


def remove_annotations(
    annotations: List[Annotation], snapshot_name: str
) -> List[Annotation]:
    """Remove every annotation tied to *snapshot_name*."""
    return [a for a in annotations if a.snapshot_name != snapshot_name]


def annotations_to_dict(annotations: List[Annotation]) -> List[dict]:
    return [a.to_dict() for a in annotations]


def annotations_from_dict(data: List[dict]) -> List[Annotation]:
    return [Annotation.from_dict(d) for d in data]
