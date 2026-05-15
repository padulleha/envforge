"""Trim snapshot variables by removing leading/trailing whitespace from keys and/or values."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envforge.snapshot import Snapshot


@dataclass
class TrimResult:
    name: str
    trimmed_keys: List[str] = field(default_factory=list)
    trimmed_values: List[str] = field(default_factory=list)
    snapshot: Snapshot = field(default=None)

    def __str__(self) -> str:
        parts = []
        if self.trimmed_keys:
            parts.append(f"keys trimmed: {', '.join(sorted(self.trimmed_keys))}")
        if self.trimmed_values:
            parts.append(f"values trimmed: {', '.join(sorted(self.trimmed_values))}")
        if not parts:
            return f"{self.name}: nothing to trim"
        return f"{self.name}: " + "; ".join(parts)

    @property
    def has_changes(self) -> bool:
        return bool(self.trimmed_keys or self.trimmed_values)


def trim_snapshot(
    snapshot: Snapshot,
    *,
    trim_keys: bool = True,
    trim_values: bool = True,
) -> TrimResult:
    """Return a new Snapshot with whitespace stripped from keys and/or values.

    Args:
        snapshot: The source snapshot.
        trim_keys: Whether to strip whitespace from variable names.
        trim_values: Whether to strip whitespace from variable values.

    Returns:
        A TrimResult containing the cleaned snapshot and lists of changed keys.
    """
    new_vars: dict[str, str] = {}
    trimmed_keys: list[str] = []
    trimmed_values: list[str] = []

    for raw_key, raw_value in snapshot.variables.items():
        clean_key = raw_key.strip() if trim_keys else raw_key
        clean_value = raw_value.strip() if trim_values else raw_value

        if clean_key != raw_key:
            trimmed_keys.append(raw_key)
        if clean_value != raw_value:
            trimmed_values.append(clean_key)

        new_vars[clean_key] = clean_value

    trimmed = Snapshot(
        name=snapshot.name,
        variables=new_vars,
        description=snapshot.description,
        tags=list(snapshot.tags),
        created_at=snapshot.created_at,
    )

    return TrimResult(
        name=snapshot.name,
        trimmed_keys=trimmed_keys,
        trimmed_values=trimmed_values,
        snapshot=trimmed,
    )
