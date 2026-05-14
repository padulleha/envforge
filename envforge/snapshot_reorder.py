"""Reorder (rekey) variables within a snapshot by a given ordering strategy."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from envforge.snapshot import Snapshot


class ReorderStrategy(str, Enum):
    ALPHABETICAL = "alphabetical"
    REVERSE_ALPHA = "reverse_alpha"
    BY_VALUE_LENGTH = "by_value_length"
    CUSTOM = "custom"


class ReorderError(Exception):
    """Raised when reordering cannot be completed."""


@dataclass
class ReorderResult:
    snapshot_name: str
    strategy: ReorderStrategy
    original_order: List[str]
    new_order: List[str]
    changed: bool = field(init=False)

    def __post_init__(self) -> None:
        self.changed = self.original_order != self.new_order

    def __str__(self) -> str:
        if not self.changed:
            return f"[{self.snapshot_name}] Order unchanged ({len(self.new_order)} keys)"
        return (
            f"[{self.snapshot_name}] Reordered {len(self.new_order)} keys "
            f"using strategy '{self.strategy.value}'"
        )


def reorder_snapshot(
    snapshot: Snapshot,
    strategy: ReorderStrategy,
    custom_order: Optional[List[str]] = None,
) -> ReorderResult:
    """Return a new Snapshot with variables reordered by *strategy*.

    The original snapshot object is not mutated.
    """
    original_keys: List[str] = list(snapshot.variables.keys())

    if strategy == ReorderStrategy.ALPHABETICAL:
        new_keys = sorted(original_keys)
    elif strategy == ReorderStrategy.REVERSE_ALPHA:
        new_keys = sorted(original_keys, reverse=True)
    elif strategy == ReorderStrategy.BY_VALUE_LENGTH:
        new_keys = sorted(original_keys, key=lambda k: len(snapshot.variables[k]))
    elif strategy == ReorderStrategy.CUSTOM:
        if custom_order is None:
            raise ReorderError("custom_order must be provided when strategy is CUSTOM")
        unknown = set(custom_order) - set(original_keys)
        if unknown:
            raise ReorderError(
                f"custom_order references unknown keys: {sorted(unknown)}"
            )
        # Keys not mentioned in custom_order are appended at the end, sorted.
        trailing = sorted(k for k in original_keys if k not in custom_order)
        new_keys = [k for k in custom_order if k in original_keys] + trailing
    else:
        raise ReorderError(f"Unsupported strategy: {strategy}")

    new_vars: Dict[str, str] = {k: snapshot.variables[k] for k in new_keys}

    reordered = Snapshot(
        name=snapshot.name,
        variables=new_vars,
        description=snapshot.description,
        tags=list(snapshot.tags),
        created_at=snapshot.created_at,
    )

    return ReorderResult(
        snapshot_name=snapshot.name,
        strategy=strategy,
        original_order=original_keys,
        new_order=new_keys,
    ), reordered
