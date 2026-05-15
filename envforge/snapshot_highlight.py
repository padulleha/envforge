"""Highlight specific keys in a snapshot for quick visual inspection."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import fnmatch

from envforge.snapshot import Snapshot


@dataclass
class HighlightResult:
    snapshot_name: str
    highlighted: Dict[str, str] = field(default_factory=dict)
    patterns: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return bool(self.highlighted)

    def summary(self) -> str:
        n = len(self.highlighted)
        if n == 0:
            return f"{self.snapshot_name}: no keys matched patterns {self.patterns}"
        return f"{self.snapshot_name}: {n} key(s) highlighted"

    def format_text(self, mask_values: bool = False) -> str:
        if not self.highlighted:
            return self.summary()
        lines = [f"Highlighted keys in '{self.snapshot_name}':", ""]
        for key, value in sorted(self.highlighted.items()):
            display = "***" if mask_values else value
            lines.append(f"  {key} = {display}")
        return "\n".join(lines)


def highlight_snapshot(
    snapshot: Snapshot,
    patterns: List[str],
    case_sensitive: bool = False,
) -> HighlightResult:
    """Return keys from *snapshot* whose names match any of the glob *patterns*."""
    matched: Dict[str, str] = {}
    for key, value in snapshot.variables.items():
        compare_key = key if case_sensitive else key.upper()
        for pattern in patterns:
            compare_pattern = pattern if case_sensitive else pattern.upper()
            if fnmatch.fnmatch(compare_key, compare_pattern):
                matched[key] = value
                break
    return HighlightResult(
        snapshot_name=snapshot.name,
        highlighted=matched,
        patterns=list(patterns),
    )
