"""Filter snapshots by various criteria (key patterns, value patterns, metadata)."""
from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from typing import List, Optional

from envforge.snapshot import Snapshot


@dataclass
class FilterCriteria:
    key_pattern: Optional[str] = None      # glob pattern for keys
    value_pattern: Optional[str] = None    # glob pattern for values
    name_pattern: Optional[str] = None     # glob pattern for snapshot name
    tags: List[str] = field(default_factory=list)  # all tags must be present
    min_keys: Optional[int] = None
    max_keys: Optional[int] = None


@dataclass
class FilterResult:
    snapshot: Snapshot
    matched_keys: List[str]

    def __bool__(self) -> bool:
        return len(self.matched_keys) > 0

    def summary(self) -> str:
        return f"{self.snapshot.name}: {len(self.matched_keys)} matching key(s)"


def _match_pattern(value: str, pattern: Optional[str]) -> bool:
    if pattern is None:
        return True
    return fnmatch.fnmatch(value, pattern)


def filter_snapshot(snap: Snapshot, criteria: FilterCriteria) -> Optional[FilterResult]:
    """Apply criteria to a single snapshot. Returns FilterResult or None if excluded."""
    if not _match_pattern(snap.name, criteria.name_pattern):
        return None

    snap_tags = set(snap.metadata.get("tags", []))
    if any(t not in snap_tags for t in criteria.tags):
        return None

    key_count = len(snap.variables)
    if criteria.min_keys is not None and key_count < criteria.min_keys:
        return None
    if criteria.max_keys is not None and key_count > criteria.max_keys:
        return None

    matched = [
        k for k, v in snap.variables.items()
        if _match_pattern(k, criteria.key_pattern)
        and _match_pattern(v, criteria.value_pattern)
    ]

    if criteria.key_pattern is not None or criteria.value_pattern is not None:
        if not matched:
            return None

    return FilterResult(snapshot=snap, matched_keys=matched)


def filter_snapshots(
    snapshots: List[Snapshot],
    criteria: FilterCriteria,
) -> List[FilterResult]:
    """Filter a list of snapshots, returning only those that match all criteria."""
    results = []
    for snap in snapshots:
        result = filter_snapshot(snap, criteria)
        if result is not None:
            results.append(result)
    return results
