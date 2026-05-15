"""Snapshot summary: generate human-readable summaries for one or many snapshots."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envforge.snapshot import Snapshot


@dataclass
class SnapshotSummary:
    name: str
    key_count: int
    tags: List[str] = field(default_factory=list)
    description: Optional[str] = None
    created_at: Optional[str] = None

    def one_line(self) -> str:
        """Return a compact single-line summary."""
        parts = [f"{self.name} ({self.key_count} keys)"]
        if self.tags:
            parts.append("[" + ", ".join(self.tags) + "]")
        if self.description:
            parts.append(f"— {self.description}")
        return " ".join(parts)

    def detail(self) -> str:
        """Return a multi-line detailed summary."""
        lines = [
            f"Name        : {self.name}",
            f"Keys        : {self.key_count}",
        ]
        if self.tags:
            lines.append(f"Tags        : {', '.join(self.tags)}")
        else:
            lines.append("Tags        : (none)")
        if self.description:
            lines.append(f"Description : {self.description}")
        if self.created_at:
            lines.append(f"Created     : {self.created_at}")
        return "\n".join(lines)


def summarise(snapshot: Snapshot) -> SnapshotSummary:
    """Build a SnapshotSummary from a Snapshot instance."""
    return SnapshotSummary(
        name=snapshot.name,
        key_count=len(snapshot.variables),
        tags=list(snapshot.tags) if hasattr(snapshot, "tags") and snapshot.tags else [],
        description=snapshot.description if hasattr(snapshot, "description") else None,
        created_at=snapshot.created_at if hasattr(snapshot, "created_at") else None,
    )


def multi_summary(snapshots: List[Snapshot], *, detail: bool = False) -> str:
    """Return a formatted summary block for multiple snapshots."""
    if not snapshots:
        return "No snapshots found."
    summaries = [summarise(s) for s in snapshots]
    if detail:
        blocks = [s.detail() for s in summaries]
        return "\n\n".join(blocks)
    lines = [s.one_line() for s in summaries]
    return "\n".join(lines)
