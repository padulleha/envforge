"""Rollback support: restore a snapshot to a previous state via history."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envforge.history import SnapshotHistory, HistoryEntry
from envforge.snapshot import Snapshot


@dataclass
class RollbackPoint:
    """A restorable point in a snapshot's history."""
    index: int
    entry: HistoryEntry
    snapshot: Snapshot

    def format(self) -> str:
        ts = self.entry.timestamp[:19].replace("T", " ")
        detail = f" ({self.entry.detail})" if self.entry.detail else ""
        return f"[{self.index}] {ts}  {self.entry.action}{detail}"


def get_rollback_points(
    name: str,
    history: SnapshotHistory,
    limit: int = 10,
) -> List[RollbackPoint]:
    """Return up to *limit* rollback points for *name*, newest first."""
    entries = history.for_snapshot(name)
    # Only entries that carry a snapshot payload can be restored
    restorable = [
        e for e in entries
        if e.snapshot_data is not None
    ]
    restorable = restorable[-limit:][::-1]  # newest first
    points = []
    for idx, entry in enumerate(restorable):
        snap = Snapshot.from_dict(entry.snapshot_data)
        points.append(RollbackPoint(index=idx, entry=entry, snapshot=snap))
    return points


def rollback_to(
    name: str,
    index: int,
    history: SnapshotHistory,
) -> Optional[Snapshot]:
    """Return the snapshot at rollback *index*, or None if not found."""
    points = get_rollback_points(name, history)
    for point in points:
        if point.index == index:
            return point.snapshot
    return None
