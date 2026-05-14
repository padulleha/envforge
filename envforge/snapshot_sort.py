"""Sort and order snapshots by various criteria."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from envforge.snapshot import Snapshot


class SortKey(str, Enum):
    NAME = "name"
    CREATED = "created"
    KEY_COUNT = "key_count"
    DESCRIPTION = "description"


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


@dataclass
class SortCriteria:
    key: SortKey = SortKey.NAME
    order: SortOrder = SortOrder.ASC

    def to_dict(self) -> dict:
        return {"key": self.key.value, "order": self.order.value}

    @classmethod
    def from_dict(cls, data: dict) -> "SortCriteria":
        return cls(
            key=SortKey(data.get("key", SortKey.NAME.value)),
            order=SortOrder(data.get("order", SortOrder.ASC.value)),
        )


@dataclass
class SortResult:
    snapshots: List[Snapshot]
    criteria: SortCriteria
    original_count: int

    def summary(self) -> str:
        return (
            f"Sorted {self.original_count} snapshot(s) by "
            f"'{self.criteria.key.value}' ({self.criteria.order.value})"
        )


def _sort_key_fn(snap: Snapshot, key: SortKey):
    if key == SortKey.NAME:
        return (snap.name or "").lower()
    if key == SortKey.CREATED:
        return snap.created_at or ""
    if key == SortKey.KEY_COUNT:
        return len(snap.variables)
    if key == SortKey.DESCRIPTION:
        return (snap.description or "").lower()
    return ""


def sort_snapshots(
    snapshots: List[Snapshot],
    criteria: Optional[SortCriteria] = None,
) -> SortResult:
    """Return a SortResult with snapshots ordered by the given criteria."""
    if criteria is None:
        criteria = SortCriteria()

    reverse = criteria.order == SortOrder.DESC
    sorted_snaps = sorted(
        snapshots,
        key=lambda s: _sort_key_fn(s, criteria.key),
        reverse=reverse,
    )
    return SortResult(
        snapshots=sorted_snaps,
        criteria=criteria,
        original_count=len(snapshots),
    )
