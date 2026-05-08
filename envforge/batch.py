"""Batch operations: apply or capture multiple snapshots in one call."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envforge.snapshot import Snapshot


@dataclass
class BatchResult:
    succeeded: List[str] = field(default_factory=list)
    failed: List[str] = field(default_factory=list)
    errors: dict = field(default_factory=dict)

    def __str__(self) -> str:
        parts = []
        if self.succeeded:
            parts.append(f"OK: {', '.join(self.succeeded)}")
        if self.failed:
            parts.append(f"FAILED: {', '.join(self.failed)}")
        return " | ".join(parts) if parts else "No operations performed"

    @property
    def all_succeeded(self) -> bool:
        return len(self.failed) == 0


def batch_capture(store, names: List[str], keys: Optional[List[str]] = None) -> BatchResult:
    """Capture current environment into multiple named snapshots."""
    result = BatchResult()
    for name in names:
        try:
            snap = Snapshot.capture(name=name, keys=keys)
            store.save(snap)
            result.succeeded.append(name)
        except Exception as exc:  # noqa: BLE001
            result.failed.append(name)
            result.errors[name] = str(exc)
    return result


def batch_apply(store, names: List[str], overwrite: bool = True) -> BatchResult:
    """Apply multiple snapshots to the current environment in order."""
    import os

    result = BatchResult()
    for name in names:
        try:
            snap = store.get(name)
            if snap is None:
                raise KeyError(f"Snapshot '{name}' not found")
            snap.apply(overwrite=overwrite)
            result.succeeded.append(name)
        except Exception as exc:  # noqa: BLE001
            result.failed.append(name)
            result.errors[name] = str(exc)
    return result


def batch_delete(store, names: List[str]) -> BatchResult:
    """Delete multiple snapshots from the store."""
    result = BatchResult()
    for name in names:
        try:
            if store.get(name) is None:
                raise KeyError(f"Snapshot '{name}' not found")
            store.delete(name)
            result.succeeded.append(name)
        except Exception as exc:  # noqa: BLE001
            result.failed.append(name)
            result.errors[name] = str(exc)
    return result
