"""Snapshot locking — prevent accidental modification of named snapshots."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class LockedSnapshot:
    name: str
    reason: Optional[str] = None

    def to_dict(self) -> dict:
        return {"name": self.name, "reason": self.reason}

    @classmethod
    def from_dict(cls, data: dict) -> "LockedSnapshot":
        return cls(name=data["name"], reason=data.get("reason"))

    def format(self) -> str:
        base = f"  🔒 {self.name}"
        if self.reason:
            base += f"  ({self.reason})"
        return base


def add_lock(
    locks: List[LockedSnapshot],
    name: str,
    reason: Optional[str] = None,
) -> List[LockedSnapshot]:
    """Add or update a lock entry for *name*."""
    if not name:
        raise ValueError("Snapshot name must not be empty.")
    updated = [lk for lk in locks if lk.name != name]
    updated.append(LockedSnapshot(name=name, reason=reason))
    return sorted(updated, key=lambda lk: lk.name)


def remove_lock(
    locks: List[LockedSnapshot], name: str
) -> List[LockedSnapshot]:
    """Remove the lock for *name*; silently succeeds if not present."""
    return [lk for lk in locks if lk.name != name]


def is_locked(locks: List[LockedSnapshot], name: str) -> bool:
    """Return True if *name* is currently locked."""
    return any(lk.name == name for lk in locks)


def get_lock(locks: List[LockedSnapshot], name: str) -> Optional[LockedSnapshot]:
    """Return the LockedSnapshot entry for *name*, or None."""
    for lk in locks:
        if lk.name == name:
            return lk
    return None


def format_locks(locks: List[LockedSnapshot]) -> str:
    if not locks:
        return "  (no locked snapshots)"
    return "\n".join(lk.format() for lk in locks)
