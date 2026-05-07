"""Rename snapshots with optional history recording."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


class RenameError(Exception):
    """Raised when a rename operation cannot be completed."""


@dataclass
class RenameResult:
    old_name: str
    new_name: str
    success: bool
    message: str = ""

    def __str__(self) -> str:
        if self.success:
            return f"Renamed '{self.old_name}' -> '{self.new_name}'"
        return f"Rename failed: {self.message}"


def rename_snapshot(
    store,
    old_name: str,
    new_name: str,
    *,
    overwrite: bool = False,
) -> RenameResult:
    """Rename a snapshot from *old_name* to *new_name*.

    Args:
        store: A :class:`~envforge.store.SnapshotStore` instance.
        old_name: Existing snapshot name.
        new_name: Desired new name.
        overwrite: If *True*, replace an existing snapshot with *new_name*.

    Returns:
        A :class:`RenameResult` describing the outcome.

    Raises:
        RenameError: If the source snapshot does not exist, or the destination
            already exists and *overwrite* is *False*.
    """
    if not new_name or not new_name.strip():
        raise RenameError("new_name must be a non-empty string")

    snap = store.get(old_name)
    if snap is None:
        raise RenameError(f"Snapshot '{old_name}' not found")

    if new_name == old_name:
        return RenameResult(old_name, new_name, True, "names are identical; nothing to do")

    existing = store.get(new_name)
    if existing is not None and not overwrite:
        raise RenameError(
            f"Snapshot '{new_name}' already exists. Use overwrite=True to replace it."
        )

    # Preserve all snapshot data but update the name
    snap.name = new_name
    store.save(snap)
    store.delete(old_name)

    return RenameResult(old_name, new_name, True)
