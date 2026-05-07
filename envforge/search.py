"""Search and filter snapshots by key/value patterns."""
from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass, field
from typing import List, Optional

from envforge.snapshot import Snapshot


@dataclass
class SearchResult:
    snapshot_name: str
    matched_keys: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return bool(self.matched_keys)

    def summary(self) -> str:
        keys = ", ".join(self.matched_keys)
        return f"{self.snapshot_name}: [{keys}]"


def search_snapshots(
    snapshots: dict[str, Snapshot],
    key_pattern: Optional[str] = None,
    value_pattern: Optional[str] = None,
    use_regex: bool = False,
) -> List[SearchResult]:
    """Search snapshots whose variables match key and/or value patterns.

    Args:
        snapshots: mapping of name -> Snapshot
        key_pattern: glob (or regex if use_regex) pattern for variable names
        value_pattern: glob (or regex if use_regex) pattern for variable values
        use_regex: treat patterns as regular expressions instead of globs

    Returns:
        List of SearchResult, one per snapshot that had at least one match.
    """
    if not key_pattern and not value_pattern:
        raise ValueError("At least one of key_pattern or value_pattern must be provided.")

    def _match(pattern: str, text: str) -> bool:
        if use_regex:
            return bool(re.search(pattern, text))
        return fnmatch.fnmatch(text, pattern)

    results: List[SearchResult] = []
    for name, snap in snapshots.items():
        matched: List[str] = []
        for k, v in snap.variables.items():
            key_ok = _match(key_pattern, k) if key_pattern else True
            val_ok = _match(value_pattern, v) if value_pattern else True
            if key_ok and val_ok:
                matched.append(k)
        if matched:
            results.append(SearchResult(snapshot_name=name, matched_keys=sorted(matched)))
    return results
