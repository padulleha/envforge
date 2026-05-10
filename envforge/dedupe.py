"""Detect and remove duplicate snapshots based on their variable contents."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from envforge.snapshot import Snapshot


@dataclass
class DedupeResult:
    """Result of a deduplication scan."""

    groups: List[List[str]] = field(default_factory=list)  # groups of duplicate names
    removed: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        if not self.groups:
            return "No duplicate snapshots found."
        lines = [f"Found {len(self.groups)} duplicate group(s):"]
        for group in self.groups:
            lines.append("  " + ", ".join(group))
        if self.removed:
            lines.append("Removed: " + ", ".join(self.removed))
        return "\n".join(lines)

    @property
    def has_duplicates(self) -> bool:
        return len(self.groups) > 0


def _snapshot_fingerprint(snap: Snapshot) -> str:
    """Return a stable fingerprint string for a snapshot's variables."""
    items = sorted(snap.variables.items())
    return ";".join(f"{k}={v}" for k, v in items)


def find_duplicates(snapshots: Dict[str, Snapshot]) -> DedupeResult:
    """Group snapshot names that share identical variable contents."""
    fingerprint_map: Dict[str, List[str]] = {}
    for name, snap in snapshots.items():
        fp = _snapshot_fingerprint(snap)
        fingerprint_map.setdefault(fp, []).append(name)

    groups = [sorted(names) for names in fingerprint_map.values() if len(names) > 1]
    return DedupeResult(groups=groups)


def remove_duplicates(
    snapshots: Dict[str, Snapshot],
    keep: str = "first",
) -> DedupeResult:
    """Remove duplicate snapshots, keeping one per group.

    Args:
        snapshots: Mapping of snapshot name -> Snapshot (mutated in place).
        keep: ``"first"`` keeps the lexicographically first name;
              ``"last"`` keeps the lexicographically last name.
    """
    result = find_duplicates(snapshots)
    removed: List[str] = []
    for group in result.groups:
        ordered = sorted(group)
        to_remove = ordered[1:] if keep == "first" else ordered[:-1]
        for name in to_remove:
            del snapshots[name]
            removed.append(name)
    result.removed = removed
    return result
