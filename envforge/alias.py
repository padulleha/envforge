"""Snapshot alias management — assign human-friendly names to snapshots."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SnapshotAlias:
    alias: str
    snapshot_name: str
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "alias": self.alias,
            "snapshot_name": self.snapshot_name,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SnapshotAlias":
        return cls(
            alias=data["alias"],
            snapshot_name=data["snapshot_name"],
            description=data.get("description", ""),
        )


def add_alias(aliases: List[SnapshotAlias], alias: str, snapshot_name: str, description: str = "") -> List[SnapshotAlias]:
    """Add or update an alias. Raises ValueError if alias string is empty."""
    if not alias or not alias.strip():
        raise ValueError("Alias name must not be empty.")
    if not snapshot_name or not snapshot_name.strip():
        raise ValueError("Snapshot name must not be empty.")
    updated = [a for a in aliases if a.alias != alias]
    updated.append(SnapshotAlias(alias=alias, snapshot_name=snapshot_name, description=description))
    return sorted(updated, key=lambda a: a.alias)


def remove_alias(aliases: List[SnapshotAlias], alias: str) -> List[SnapshotAlias]:
    """Remove an alias by name. Raises KeyError if not found."""
    existing = {a.alias for a in aliases}
    if alias not in existing:
        raise KeyError(f"Alias '{alias}' not found.")
    return [a for a in aliases if a.alias != alias]


def resolve_alias(aliases: List[SnapshotAlias], alias: str) -> Optional[str]:
    """Return the snapshot name for a given alias, or None if not found."""
    for a in aliases:
        if a.alias == alias:
            return a.snapshot_name
    return None


def format_aliases(aliases: List[SnapshotAlias]) -> str:
    if not aliases:
        return "(no aliases defined)"
    lines = []
    for a in aliases:
        desc = f"  # {a.description}" if a.description else ""
        lines.append(f"  {a.alias} -> {a.snapshot_name}{desc}")
    return "\n".join(lines)
