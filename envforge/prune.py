"""Prune snapshots from the store based on age or count limits."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from envforge.snapshot import Snapshot
from envforge.store import SnapshotStore


class PruneError(Exception):
    pass


@dataclass
class PruneResult:
    removed: List[str] = field(default_factory=list)
    kept: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        if not self.removed:
            return "No snapshots pruned."
        removed_list = ", ".join(self.removed)
        return f"Pruned {len(self.removed)} snapshot(s): {removed_list}"


def prune_by_age(
    store: SnapshotStore,
    max_age_days: int,
    dry_run: bool = False,
) -> PruneResult:
    """Remove snapshots older than *max_age_days* days."""
    if max_age_days <= 0:
        raise PruneError("max_age_days must be a positive integer.")

    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=max_age_days)
    result = PruneResult()

    for name in list(store.list()):
        snap: Optional[Snapshot] = store.get(name)
        if snap is None:
            continue
        created = snap.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        if created < cutoff:
            result.removed.append(name)
            if not dry_run:
                store.delete(name)
        else:
            result.kept.append(name)

    return result


def prune_by_count(
    store: SnapshotStore,
    keep: int,
    dry_run: bool = False,
) -> PruneResult:
    """Keep only the *keep* most-recently-created snapshots; remove the rest."""
    if keep <= 0:
        raise PruneError("keep must be a positive integer.")

    names = list(store.list())
    snapshots: list[tuple[str, Snapshot]] = []
    for name in names:
        snap = store.get(name)
        if snap is not None:
            snapshots.append((name, snap))

    snapshots.sort(
        key=lambda t: t[1].created_at.replace(tzinfo=timezone.utc)
        if t[1].created_at.tzinfo is None
        else t[1].created_at,
        reverse=True,
    )

    result = PruneResult()
    for i, (name, _) in enumerate(snapshots):
        if i < keep:
            result.kept.append(name)
        else:
            result.removed.append(name)
            if not dry_run:
                store.delete(name)

    return result
