"""Bookmark named positions within a snapshot's key set for quick access."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Bookmark:
    name: str
    snapshot_name: str
    keys: List[str]
    description: str = ""
    created_at: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "snapshot_name": self.snapshot_name,
            "keys": sorted(self.keys),
            "description": self.description,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Bookmark":
        return cls(
            name=data["name"],
            snapshot_name=data["snapshot_name"],
            keys=data.get("keys", []),
            description=data.get("description", ""),
            created_at=data.get("created_at", ""),
        )

    def format(self) -> str:
        lines = [f"Bookmark '{self.name}' -> snapshot '{self.snapshot_name}'"]
        if self.description:
            lines.append(f"  Description: {self.description}")
        lines.append(f"  Keys ({len(self.keys)}): {', '.join(sorted(self.keys))}")
        return "\n".join(lines)


class BookmarkError(Exception):
    pass


def add_bookmark(
    bookmarks: List[Bookmark],
    name: str,
    snapshot_name: str,
    keys: List[str],
    description: str = "",
    created_at: Optional[str] = None,
) -> List[Bookmark]:
    if not name:
        raise BookmarkError("Bookmark name must not be empty.")
    if not keys:
        raise BookmarkError("Bookmark must include at least one key.")

    import datetime
    ts = created_at or datetime.datetime.utcnow().isoformat()

    updated = [b for b in bookmarks if b.name != name]
    updated.append(Bookmark(name=name, snapshot_name=snapshot_name, keys=list(keys), description=description, created_at=ts))
    return sorted(updated, key=lambda b: b.name)


def remove_bookmark(bookmarks: List[Bookmark], name: str) -> List[Bookmark]:
    result = [b for b in bookmarks if b.name != name]
    if len(result) == len(bookmarks):
        raise BookmarkError(f"Bookmark '{name}' not found.")
    return result


def get_bookmark(bookmarks: List[Bookmark], name: str) -> Optional[Bookmark]:
    for b in bookmarks:
        if b.name == name:
            return b
    return None


def list_bookmarks_for(bookmarks: List[Bookmark], snapshot_name: str) -> List[Bookmark]:
    return [b for b in bookmarks if b.snapshot_name == snapshot_name]
