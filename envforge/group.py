"""Snapshot grouping — assign snapshots to named groups and query by group."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SnapshotGroup:
    name: str
    description: str = ""
    members: List[str] = field(default_factory=list)  # snapshot names

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "members": sorted(self.members),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SnapshotGroup":
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            members=list(data.get("members", [])),
        )


def add_to_group(
    groups: List[SnapshotGroup],
    group_name: str,
    snapshot_name: str,
    description: str = "",
) -> List[SnapshotGroup]:
    """Add *snapshot_name* to *group_name*, creating the group if needed."""
    if not group_name:
        raise ValueError("group_name must not be empty")
    if not snapshot_name:
        raise ValueError("snapshot_name must not be empty")

    for grp in groups:
        if grp.name == group_name:
            if snapshot_name not in grp.members:
                grp.members.append(snapshot_name)
                grp.members.sort()
            return groups

    new_group = SnapshotGroup(name=group_name, description=description, members=[snapshot_name])
    groups.append(new_group)
    groups.sort(key=lambda g: g.name)
    return groups


def remove_from_group(
    groups: List[SnapshotGroup],
    group_name: str,
    snapshot_name: str,
) -> List[SnapshotGroup]:
    """Remove *snapshot_name* from *group_name*. No-op if not present."""
    for grp in groups:
        if grp.name == group_name:
            grp.members = [m for m in grp.members if m != snapshot_name]
            return groups
    return groups


def get_group(
    groups: List[SnapshotGroup], group_name: str
) -> Optional[SnapshotGroup]:
    for grp in groups:
        if grp.name == group_name:
            return grp
    return None


def groups_for_snapshot(
    groups: List[SnapshotGroup], snapshot_name: str
) -> List[SnapshotGroup]:
    """Return all groups that contain *snapshot_name*."""
    return [g for g in groups if snapshot_name in g.members]


def format_groups(groups: List[SnapshotGroup]) -> str:
    if not groups:
        return "(no groups)"
    lines = []
    for g in groups:
        member_str = ", ".join(g.members) if g.members else "(empty)"
        desc = f" — {g.description}" if g.description else ""
        lines.append(f"{g.name}{desc}: {member_str}")
    return "\n".join(lines)
