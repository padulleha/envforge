"""Compute statistics and summaries for snapshots."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict

from envforge.snapshot import Snapshot


@dataclass
class SnapshotStats:
    name: str
    key_count: int
    empty_value_count: int
    avg_value_length: float
    longest_key: str
    shortest_key: str
    tag_count: int
    has_description: bool

    def summary(self) -> str:
        lines = [
            f"Snapshot : {self.name}",
            f"Keys     : {self.key_count}",
            f"Empty    : {self.empty_value_count}",
            f"Avg len  : {self.avg_value_length:.1f}",
            f"Longest  : {self.longest_key!r}",
            f"Shortest : {self.shortest_key!r}",
            f"Tags     : {self.tag_count}",
            f"Desc     : {'yes' if self.has_description else 'no'}",
        ]
        return "\n".join(lines)


def compute_stats(snapshot: Snapshot) -> SnapshotStats:
    """Return a SnapshotStats for the given snapshot."""
    env = snapshot.env_vars
    keys = list(env.keys())

    if not keys:
        return SnapshotStats(
            name=snapshot.name,
            key_count=0,
            empty_value_count=0,
            avg_value_length=0.0,
            longest_key="",
            shortest_key="",
            tag_count=len(snapshot.tags),
            has_description=bool(snapshot.description),
        )

    empty_count = sum(1 for v in env.values() if v == "")
    value_lengths = [len(v) for v in env.values()]
    avg_len = sum(value_lengths) / len(value_lengths)
    longest = max(keys, key=len)
    shortest = min(keys, key=len)

    return SnapshotStats(
        name=snapshot.name,
        key_count=len(keys),
        empty_value_count=empty_count,
        avg_value_length=avg_len,
        longest_key=longest,
        shortest_key=shortest,
        tag_count=len(snapshot.tags),
        has_description=bool(snapshot.description),
    )


def multi_summary(snapshots: List[Snapshot]) -> Dict[str, SnapshotStats]:
    """Return a dict of name -> SnapshotStats for a list of snapshots."""
    return {snap.name: compute_stats(snap) for snap in snapshots}
