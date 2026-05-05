"""Merge two snapshots into a new one, with configurable conflict resolution."""

from __future__ import annotations

from enum import Enum
from typing import Dict, Optional

from envforge.snapshot import Snapshot


class ConflictStrategy(str, Enum):
    USE_BASE = "base"       # keep value from base snapshot
    USE_OTHER = "other"     # keep value from other snapshot
    ERROR = "error"         # raise on any conflict


class MergeConflictError(Exception):
    """Raised when a key conflict is detected and strategy is ERROR."""

    def __init__(self, conflicts: Dict[str, tuple]):
        self.conflicts = conflicts  # {key: (base_val, other_val)}
        keys = ", ".join(sorted(conflicts))
        super().__init__(f"Merge conflicts on keys: {keys}")


def merge_snapshots(
    base: Snapshot,
    other: Snapshot,
    name: str,
    strategy: ConflictStrategy = ConflictStrategy.USE_OTHER,
    description: Optional[str] = None,
) -> Snapshot:
    """Return a new Snapshot that merges *base* and *other*.

    Keys present only in one snapshot are always included.  Keys present in
    both are resolved according to *strategy*.
    """
    merged: Dict[str, str] = dict(base.variables)

    conflicts: Dict[str, tuple] = {}

    for key, value in other.variables.items():
        if key in merged and merged[key] != value:
            conflicts[key] = (merged[key], value)
        else:
            merged[key] = value

    if conflicts:
        if strategy == ConflictStrategy.ERROR:
            raise MergeConflictError(conflicts)
        elif strategy == ConflictStrategy.USE_BASE:
            # keep base values — already in merged, nothing to do
            pass
        else:  # USE_OTHER
            for key, (_, other_val) in conflicts.items():
                merged[key] = other_val

    combined_tags = sorted(set(base.tags) | set(other.tags))

    snap = Snapshot(
        name=name,
        variables=merged,
        description=description or f"Merged from '{base.name}' and '{other.name}'",
        tags=combined_tags,
    )
    return snap
