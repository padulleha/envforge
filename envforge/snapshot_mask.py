"""Mask sensitive environment variable values in snapshots."""
from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatch
from typing import Dict, List, Optional

from envforge.snapshot import Snapshot

_DEFAULT_SENSITIVE_PATTERNS = [
    "*SECRET*",
    "*PASSWORD*",
    "*PASSWD*",
    "*TOKEN*",
    "*API_KEY*",
    "*PRIVATE_KEY*",
    "*CREDENTIALS*",
]

MASK_PLACEHOLDER = "***"


@dataclass
class MaskResult:
    original: Snapshot
    masked: Snapshot
    masked_keys: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        if not self.masked_keys:
            return f"No keys masked in '{self.original.name}'."
        keys = ", ".join(self.masked_keys)
        return f"Masked {len(self.masked_keys)} key(s) in '{self.original.name}': {keys}"

    @property
    def has_masked(self) -> bool:
        return bool(self.masked_keys)


def _is_sensitive(key: str, patterns: List[str]) -> bool:
    upper = key.upper()
    return any(fnmatch(upper, p.upper()) for p in patterns)


def mask_snapshot(
    snapshot: Snapshot,
    extra_patterns: Optional[List[str]] = None,
    placeholder: str = MASK_PLACEHOLDER,
) -> MaskResult:
    """Return a copy of *snapshot* with sensitive values replaced by *placeholder*."""
    patterns = list(_DEFAULT_SENSITIVE_PATTERNS)
    if extra_patterns:
        patterns.extend(extra_patterns)

    masked_vars: Dict[str, str] = {}
    masked_keys: List[str] = []

    for key, value in snapshot.vars.items():
        if _is_sensitive(key, patterns):
            masked_vars[key] = placeholder
            masked_keys.append(key)
        else:
            masked_vars[key] = value

    masked_snap = Snapshot(
        name=snapshot.name,
        vars=masked_vars,
        tags=list(snapshot.tags),
        description=snapshot.description,
        created_at=snapshot.created_at,
    )
    return MaskResult(original=snapshot, masked=masked_snap, masked_keys=sorted(masked_keys))
