"""Watch for environment variable changes and record diffs."""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envforge.snapshot import Snapshot
from envforge.diff import SnapshotDiff


@dataclass
class WatchEvent:
    timestamp: float
    added: Dict[str, str] = field(default_factory=dict)
    removed: Dict[str, str] = field(default_factory=dict)
    changed: Dict[str, tuple] = field(default_factory=dict)  # key -> (old, new)

    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "added": self.added,
            "removed": self.removed,
            "changed": {k: list(v) for k, v in self.changed.items()},
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WatchEvent":
        return cls(
            timestamp=data["timestamp"],
            added=data.get("added", {}),
            removed=data.get("removed", {}),
            changed={k: tuple(v) for k, v in data.get("changed", {}).items()},
        )

    def format(self) -> str:
        lines = [f"[{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.timestamp))}]"]
        for k, v in self.added.items():
            lines.append(f"  + {k}={v}")
        for k, v in self.removed.items():
            lines.append(f"  - {k}={v}")
        for k, (old, new) in self.changed.items():
            lines.append(f"  ~ {k}: {old!r} -> {new!r}")
        return "\n".join(lines)


def poll_once(baseline: Dict[str, str], keys: Optional[List[str]] = None) -> WatchEvent:
    """Compare current environment against baseline and return a WatchEvent."""
    current = dict(os.environ)
    if keys:
        baseline = {k: v for k, v in baseline.items() if k in keys}
        current = {k: v for k, v in current.items() if k in keys}

    added = {k: v for k, v in current.items() if k not in baseline}
    removed = {k: v for k, v in baseline.items() if k not in current}
    changed = {
        k: (baseline[k], current[k])
        for k in baseline
        if k in current and baseline[k] != current[k]
    }
    return WatchEvent(timestamp=time.time(), added=added, removed=removed, changed=changed)


def snapshot_to_baseline(snapshot: Snapshot) -> Dict[str, str]:
    """Extract a plain dict from a Snapshot for use as a watch baseline."""
    return dict(snapshot.variables)
