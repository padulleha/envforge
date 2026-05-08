"""Copy (duplicate) a snapshot into another snapshot within the same store."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from envforge.snapshot import Snapshot


class CopyError(Exception):
    """Raised when a copy operation cannot be completed."""


@dataclass
class CopyResult:
    source_name: str
    dest_name: str
    overwritten: bool

    def __str__(self) -> str:
        action = "overwritten" if self.overwritten else "created"
        return f"Copied '{self.source_name}' -> '{self.dest_name}' ({action})"


def copy_snapshot(
    store,
    source_name: str,
    dest_name: str,
    *,
    overwrite: bool = False,
    tag: Optional[str] = None,
) -> CopyResult:
    """Copy *source_name* to *dest_name* inside *store*.

    Parameters
    ----------
    store:
        A :class:`~envforge.store.SnapshotStore` instance.
    source_name:
        Name of the snapshot to copy.
    dest_name:
        Name for the new snapshot.
    overwrite:
        If *False* (default) raise :class:`CopyError` when *dest_name* already
        exists.  Set to *True* to replace it silently.
    tag:
        Optional tag to add to the copied snapshot's metadata.
    """
    if not source_name or not source_name.strip():
        raise CopyError("source_name must not be empty")
    if not dest_name or not dest_name.strip():
        raise CopyError("dest_name must not be empty")
    if source_name == dest_name:
        raise CopyError("source and destination names must differ")

    source: Optional[Snapshot] = store.get(source_name)
    if source is None:
        raise CopyError(f"Snapshot '{source_name}' not found")

    existing = store.get(dest_name)
    overwritten = existing is not None
    if overwritten and not overwrite:
        raise CopyError(
            f"Snapshot '{dest_name}' already exists. Use overwrite=True to replace it."
        )

    data = source.to_dict()
    data["name"] = dest_name

    # Preserve or extend tags
    tags = list(data.get("tags", []))
    if tag and tag not in tags:
        tags.append(tag)
        tags.sort()
    data["tags"] = tags

    new_snap = Snapshot.from_dict(data)
    store.save(new_snap)
    return CopyResult(source_name=source_name, dest_name=dest_name, overwritten=overwritten)
