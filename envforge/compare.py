"""Compare two snapshots and produce a structured report."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envforge.snapshot import Snapshot


@dataclass
class CompareReport:
    base_name: str
    other_name: str
    added: Dict[str, str] = field(default_factory=dict)      # in other, not in base
    removed: Dict[str, str] = field(default_factory=dict)    # in base, not in other
    changed: Dict[str, tuple] = field(default_factory=dict)  # key -> (base_val, other_val)
    unchanged: List[str] = field(default_factory=list)

    @property
    def has_differences(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def summary(self) -> str:
        parts = []
        if self.added:
            parts.append(f"+{len(self.added)} added")
        if self.removed:
            parts.append(f"-{len(self.removed)} removed")
        if self.changed:
            parts.append(f"~{len(self.changed)} changed")
        if not parts:
            return "No differences"
        return ", ".join(parts)

    def format_text(self, show_unchanged: bool = False) -> str:
        lines = [
            f"Compare: {self.base_name!r} vs {self.other_name!r}",
            f"Summary: {self.summary()}",
            "",
        ]
        for k, v in sorted(self.added.items()):
            lines.append(f"  + {k}={v!r}")
        for k, v in sorted(self.removed.items()):
            lines.append(f"  - {k}={v!r}")
        for k, (bv, ov) in sorted(self.changed.items()):
            lines.append(f"  ~ {k}: {bv!r} -> {ov!r}")
        if show_unchanged:
            for k in sorted(self.unchanged):
                lines.append(f"    {k} (unchanged)")
        return "\n".join(lines)


def compare_snapshots(
    base: Snapshot,
    other: Snapshot,
    base_name: Optional[str] = None,
    other_name: Optional[str] = None,
) -> CompareReport:
    """Return a CompareReport between two Snapshot objects."""
    bname = base_name or base.name
    oname = other_name or other.name
    report = CompareReport(base_name=bname, other_name=oname)

    base_vars = base.variables
    other_vars = other.variables

    all_keys = set(base_vars) | set(other_vars)
    for key in all_keys:
        if key in base_vars and key not in other_vars:
            report.removed[key] = base_vars[key]
        elif key in other_vars and key not in base_vars:
            report.added[key] = other_vars[key]
        elif base_vars[key] != other_vars[key]:
            report.changed[key] = (base_vars[key], other_vars[key])
        else:
            report.unchanged.append(key)

    return report
