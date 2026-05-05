"""Diff utilities for comparing environment snapshots."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from envforge.snapshot import Snapshot


@dataclass
class SnapshotDiff:
    """Result of comparing two snapshots."""

    added: Dict[str, str] = field(default_factory=dict)
    removed: Dict[str, str] = field(default_factory=dict)
    changed: Dict[str, tuple] = field(default_factory=dict)  # key -> (old, new)
    unchanged: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def summary(self) -> str:
        parts = []
        if self.added:
            parts.append(f"{len(self.added)} added")
        if self.removed:
            parts.append(f"{len(self.removed)} removed")
        if self.changed:
            parts.append(f"{len(self.changed)} changed")
        if not parts:
            return "No differences."
        return ", ".join(parts) + "."

    def format_text(self, show_unchanged: bool = False, mask_values: bool = False) -> str:
        lines = []

        def _val(v: str) -> str:
            return "***" if mask_values else v

        for key, value in sorted(self.added.items()):
            lines.append(f"+ {key}={_val(value)}")
        for key, value in sorted(self.removed.items()):
            lines.append(f"- {key}={_val(value)}")
        for key, (old, new) in sorted(self.changed.items()):
            lines.append(f"~ {key}: {_val(old)} -> {_val(new)}")
        if show_unchanged:
            for key in sorted(self.unchanged):
                lines.append(f"  {key}")

        return "\n".join(lines) if lines else "No differences."


def diff_snapshots(old: "Snapshot", new: "Snapshot") -> SnapshotDiff:
    """Compare two snapshots and return a SnapshotDiff.

    Args:
        old: The baseline snapshot.
        new: The snapshot to compare against the baseline.

    Returns:
        A SnapshotDiff describing additions, removals, and changes.
    """
    old_vars = old.variables
    new_vars = new.variables

    old_keys = set(old_vars)
    new_keys = set(new_vars)

    added = {k: new_vars[k] for k in new_keys - old_keys}
    removed = {k: old_vars[k] for k in old_keys - new_keys}
    changed = {
        k: (old_vars[k], new_vars[k])
        for k in old_keys & new_keys
        if old_vars[k] != new_vars[k]
    }
    unchanged = [k for k in old_keys & new_keys if old_vars[k] == new_vars[k]]

    return SnapshotDiff(added=added, removed=removed, changed=changed, unchanged=unchanged)


def diff_snapshot_with_env(snapshot: "Snapshot", env: dict | None = None) -> SnapshotDiff:
    """Compare a snapshot against the current (or provided) environment.

    Args:
        snapshot: The snapshot to compare.
        env: Optional dict to use as the environment; defaults to os.environ.

    Returns:
        A SnapshotDiff describing differences between the snapshot and environment.
    """
    import os
    from envforge.snapshot import Snapshot

    current_env = env if env is not None else dict(os.environ)
    current_snapshot = Snapshot(name="__current__", variables=current_env)
    return diff_snapshots(snapshot, current_snapshot)
