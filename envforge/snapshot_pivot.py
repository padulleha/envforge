"""Pivot snapshot variables into a structured table by prefix."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envforge.snapshot import Snapshot


@dataclass
class PivotRow:
    prefix: str
    keys: List[str] = field(default_factory=list)
    values: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"prefix": self.prefix, "keys": self.keys, "values": self.values}


@dataclass
class PivotResult:
    rows: List[PivotRow] = field(default_factory=list)
    ungrouped: Dict[str, str] = field(default_factory=dict)

    @property
    def has_groups(self) -> bool:
        return len(self.rows) > 0

    def summary(self) -> str:
        parts = [f"{len(self.rows)} prefix group(s)"]
        if self.ungrouped:
            parts.append(f"{len(self.ungrouped)} ungrouped key(s)")
        return ", ".join(parts)

    def format_text(self) -> str:
        lines: List[str] = []
        for row in self.rows:
            lines.append(f"[{row.prefix}]")
            for k in sorted(row.keys):
                lines.append(f"  {k} = {row.values[k]}")
        if self.ungrouped:
            lines.append("[ungrouped]")
            for k, v in sorted(self.ungrouped.items()):
                lines.append(f"  {k} = {v}")
        return "\n".join(lines)


def pivot_snapshot(
    snapshot: Snapshot,
    separator: str = "_",
    min_prefix_length: int = 1,
    prefixes: Optional[List[str]] = None,
) -> PivotResult:
    """Group snapshot variables by their common prefix.

    Args:
        snapshot: The snapshot to pivot.
        separator: Character used to split key into prefix and remainder.
        min_prefix_length: Minimum number of characters for a valid prefix.
        prefixes: If provided, only group by these explicit prefixes.

    Returns:
        A PivotResult with grouped rows and any ungrouped keys.
    """
    groups: Dict[str, PivotRow] = {}
    ungrouped: Dict[str, str] = {}

    for key, value in snapshot.variables.items():
        matched = False
        if prefixes is not None:
            for p in prefixes:
                if key.startswith(p + separator) or key == p:
                    if p not in groups:
                        groups[p] = PivotRow(prefix=p)
                    groups[p].keys.append(key)
                    groups[p].values[key] = value
                    matched = True
                    break
        else:
            idx = key.find(separator)
            if idx >= min_prefix_length:
                prefix = key[:idx]
                if prefix not in groups:
                    groups[prefix] = PivotRow(prefix=prefix)
                groups[prefix].keys.append(key)
                groups[prefix].values[key] = value
                matched = True

        if not matched:
            ungrouped[key] = value

    rows = sorted(groups.values(), key=lambda r: r.prefix)
    return PivotResult(rows=rows, ungrouped=ungrouped)
