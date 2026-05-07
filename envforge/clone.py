"""Clone (deep-copy) a snapshot under a new name, with optional key filtering."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envforge.snapshot import Snapshot


class CloneError(Exception):
    """Raised when a clone operation cannot be completed."""


@dataclass
class CloneResult:
    source_name: str
    target_name: str
    keys_copied: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        return (
            f"Cloned '{self.source_name}' -> '{self.target_name}' "
            f"({len(self.keys_copied)} key(s))"
        )


def clone_snapshot(
    store,
    source_name: str,
    target_name: str,
    keys: Optional[List[str]] = None,
    overwrite: bool = False,
) -> CloneResult:
    """Clone *source_name* into *target_name* inside *store*.

    Parameters
    ----------
    store:
        A :class:`~envforge.store.SnapshotStore` instance.
    source_name:
        Name of the snapshot to copy from.
    target_name:
        Name of the new snapshot.
    keys:
        Optional list of keys to include.  ``None`` means copy all keys.
    overwrite:
        If ``False`` (default) raise :class:`CloneError` when *target_name*
        already exists.
    """
    if source_name == target_name:
        raise CloneError("Source and target names must differ.")

    source: Optional[Snapshot] = store.get(source_name)
    if source is None:
        raise CloneError(f"Snapshot '{source_name}' not found.")

    if not overwrite and store.get(target_name) is not None:
        raise CloneError(
            f"Snapshot '{target_name}' already exists. Use overwrite=True to replace it."
        )

    if keys is not None:
        missing = [k for k in keys if k not in source.vars]
        if missing:
            raise CloneError(
                f"Key(s) not present in source snapshot: {', '.join(missing)}"
            )
        filtered_vars = {k: source.vars[k] for k in keys}
    else:
        filtered_vars = dict(source.vars)

    cloned = Snapshot(
        name=target_name,
        vars=filtered_vars,
        tags=list(source.tags),
        description=source.description,
    )
    store.save(cloned)

    return CloneResult(
        source_name=source_name,
        target_name=target_name,
        keys_copied=list(filtered_vars.keys()),
    )
