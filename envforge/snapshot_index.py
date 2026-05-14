"""Build and query an in-memory index over all snapshots for fast lookups."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from envforge.snapshot import Snapshot


@dataclass
class IndexEntry:
    name: str
    keys: Set[str] = field(default_factory=set)
    tags: List[str] = field(default_factory=list)
    description: str = ""

    def matches_key(self, pattern: str) -> bool:
        import fnmatch
        return any(fnmatch.fnmatch(k, pattern) for k in self.keys)

    def has_tag(self, tag: str) -> bool:
        return tag in self.tags


@dataclass
class SnapshotIndex:
    _entries: Dict[str, IndexEntry] = field(default_factory=dict)

    def build(self, snapshots: List[Snapshot]) -> None:
        """Rebuild the index from a list of snapshots."""
        self._entries.clear()
        for snap in snapshots:
            self._entries[snap.name] = IndexEntry(
                name=snap.name,
                keys=set(snap.variables.keys()),
                tags=list(snap.metadata.get("tags", [])),
                description=snap.metadata.get("description", ""),
            )

    def find_by_key(self, pattern: str) -> List[str]:
        """Return snapshot names that contain a key matching *pattern*."""
        return [
            name for name, entry in self._entries.items()
            if entry.matches_key(pattern)
        ]

    def find_by_tag(self, tag: str) -> List[str]:
        """Return snapshot names that carry *tag*."""
        return [
            name for name, entry in self._entries.items()
            if entry.has_tag(tag)
        ]

    def find_by_description(self, substring: str) -> List[str]:
        """Return snapshot names whose description contains *substring* (case-insensitive)."""
        sub = substring.lower()
        return [
            name for name, entry in self._entries.items()
            if sub in entry.description.lower()
        ]

    def all_keys(self) -> Set[str]:
        """Return the union of all keys across every indexed snapshot."""
        result: Set[str] = set()
        for entry in self._entries.values():
            result |= entry.keys
        return result

    def get(self, name: str) -> Optional[IndexEntry]:
        return self._entries.get(name)

    def size(self) -> int:
        return len(self._entries)


def build_index(snapshots: List[Snapshot]) -> SnapshotIndex:
    idx = SnapshotIndex()
    idx.build(snapshots)
    return idx
