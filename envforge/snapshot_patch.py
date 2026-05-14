"""Apply a partial patch (key/value updates and deletions) to a snapshot."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envforge.snapshot import Snapshot


class PatchError(Exception):
    """Raised when a patch cannot be applied."""


@dataclass
class PatchResult:
    name: str
    added: List[str] = field(default_factory=list)
    updated: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        parts = []
        if self.added:
            parts.append(f"added: {', '.join(self.added)}")
        if self.updated:
            parts.append(f"updated: {', '.join(self.updated)}")
        if self.removed:
            parts.append(f"removed: {', '.join(self.removed)}")
        if self.skipped:
            parts.append(f"skipped: {', '.join(self.skipped)}")
        summary = "; ".join(parts) if parts else "no changes"
        return f"Patch applied to '{self.name}': {summary}"

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.updated or self.removed)


def apply_patch(
    snapshot: Snapshot,
    set_keys: Optional[Dict[str, str]] = None,
    delete_keys: Optional[List[str]] = None,
    overwrite: bool = True,
) -> tuple[Snapshot, PatchResult]:
    """Return a new Snapshot with the patch applied and a PatchResult summary.

    Args:
        snapshot: The base snapshot to patch.
        set_keys: Mapping of key -> value to add or update.
        delete_keys: List of keys to remove.
        overwrite: If False, existing keys in *set_keys* are skipped.

    Returns:
        A (new_snapshot, result) tuple.
    """
    if set_keys is None:
        set_keys = {}
    if delete_keys is None:
        delete_keys = []

    new_vars: Dict[str, str] = dict(snapshot.variables)
    result = PatchResult(name=snapshot.name)

    for key, value in set_keys.items():
        if key in new_vars:
            if overwrite:
                new_vars[key] = value
                result.updated.append(key)
            else:
                result.skipped.append(key)
        else:
            new_vars[key] = value
            result.added.append(key)

    for key in delete_keys:
        if key in new_vars:
            del new_vars[key]
            result.removed.append(key)
        else:
            result.skipped.append(key)

    patched = Snapshot(
        name=snapshot.name,
        variables=new_vars,
        tags=list(snapshot.tags),
        description=snapshot.description,
    )
    return patched, result
