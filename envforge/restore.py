"""Restore a snapshot to a previous state using a backup copy stored alongside it."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from envforge.snapshot import Snapshot


class RestoreError(Exception):
    """Raised when a restore operation cannot be completed."""


@dataclass
class RestoreResult:
    snapshot_name: str
    restored_from: str
    keys_restored: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __str__(self) -> str:
        return (
            f"Restored '{self.snapshot_name}' from backup '{self.restored_from}' "
            f"({self.keys_restored} keys) at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )


def make_backup_name(name: str) -> str:
    """Return the conventional backup snapshot name for a given snapshot."""
    return f"{name}.__backup__"


def backup_snapshot(store, name: str) -> str:
    """Save a backup copy of *name* into the store. Returns the backup name."""
    snap = store.get(name)
    if snap is None:
        raise RestoreError(f"Snapshot '{name}' not found; cannot create backup.")
    backup_name = make_backup_name(name)
    backup = Snapshot(
        name=backup_name,
        variables=dict(snap.variables),
        tags=list(snap.tags),
        description=f"Auto-backup of '{name}'",
        created_at=snap.created_at,
    )
    store.save(backup)
    return backup_name


def restore_snapshot(store, name: str, backup_name: Optional[str] = None) -> RestoreResult:
    """Overwrite *name* with the contents of *backup_name* (or the auto-backup).

    Args:
        store: A SnapshotStore instance.
        name: The snapshot to restore.
        backup_name: Explicit backup snapshot name; defaults to the auto-backup.

    Returns:
        A RestoreResult describing what was done.

    Raises:
        RestoreError: If the backup snapshot does not exist.
    """
    if backup_name is None:
        backup_name = make_backup_name(name)

    backup = store.get(backup_name)
    if backup is None:
        raise RestoreError(
            f"Backup snapshot '{backup_name}' not found. "
            "Create one first with 'envforge restore backup <name>'."
        )

    original = store.get(name)
    restored = Snapshot(
        name=name,
        variables=dict(backup.variables),
        tags=list(original.tags) if original else [],
        description=original.description if original else "",
        created_at=original.created_at if original else backup.created_at,
    )
    store.save(restored)
    return RestoreResult(
        snapshot_name=name,
        restored_from=backup_name,
        keys_restored=len(restored.variables),
    )
