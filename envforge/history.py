"""Track snapshot history: timestamps, access log, and change events."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class HistoryEntry:
    action: str          # 'captured', 'applied', 'deleted', 'encrypted', 'tagged'
    snapshot_name: str
    timestamp: float = field(default_factory=time.time)
    detail: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "snapshot_name": self.snapshot_name,
            "timestamp": self.timestamp,
            "detail": self.detail,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HistoryEntry":
        return cls(
            action=data["action"],
            snapshot_name=data["snapshot_name"],
            timestamp=data.get("timestamp", 0.0),
            detail=data.get("detail"),
        )

    def format(self) -> str:
        import datetime
        ts = datetime.datetime.fromtimestamp(self.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        detail_str = f" ({self.detail})" if self.detail else ""
        return f"[{ts}] {self.action:<12} {self.snapshot_name}{detail_str}"


class SnapshotHistory:
    """Append-only history log stored alongside the snapshot store."""

    def __init__(self, entries: Optional[List[HistoryEntry]] = None):
        self._entries: List[HistoryEntry] = entries or []

    def record(self, action: str, snapshot_name: str, detail: Optional[str] = None) -> HistoryEntry:
        entry = HistoryEntry(action=action, snapshot_name=snapshot_name, detail=detail)
        self._entries.append(entry)
        return entry

    def for_snapshot(self, name: str) -> List[HistoryEntry]:
        return [e for e in self._entries if e.snapshot_name == name]

    def recent(self, n: int = 20) -> List[HistoryEntry]:
        return sorted(self._entries, key=lambda e: e.timestamp, reverse=True)[:n]

    def to_list(self) -> list:
        return [e.to_dict() for e in self._entries]

    @classmethod
    def from_list(cls, data: list) -> "SnapshotHistory":
        return cls([HistoryEntry.from_dict(d) for d in data])
