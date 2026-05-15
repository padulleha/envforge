"""Redact specific keys from a snapshot, replacing values with a placeholder."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envforge.snapshot import Snapshot

DEFAULT_PLACEHOLDER = "[REDACTED]"


@dataclass
class RedactResult:
    snapshot: Snapshot
    redacted_keys: List[str] = field(default_factory=list)
    placeholder: str = DEFAULT_PLACEHOLDER

    def __str__(self) -> str:
        if not self.redacted_keys:
            return "No keys redacted."
        keys = ", ".join(sorted(self.redacted_keys))
        return f"Redacted {len(self.redacted_keys)} key(s): {keys}"

    @property
    def has_redactions(self) -> bool:
        return len(self.redacted_keys) > 0


def redact_snapshot(
    snapshot: Snapshot,
    keys: List[str],
    placeholder: Optional[str] = None,
    new_name: Optional[str] = None,
) -> RedactResult:
    """Return a new Snapshot with the given keys replaced by *placeholder*.

    Args:
        snapshot: Source snapshot to redact.
        keys: List of exact key names to redact.
        placeholder: String to substitute for redacted values.
            Defaults to ``DEFAULT_PLACEHOLDER``.
        new_name: Optional name for the resulting snapshot.
            Defaults to ``<original>-redacted``.

    Returns:
        A :class:`RedactResult` containing the new snapshot and metadata.
    """
    if placeholder is None:
        placeholder = DEFAULT_PLACEHOLDER

    key_set = set(keys)
    new_vars: dict[str, str] = {}
    actually_redacted: list[str] = []

    for k, v in snapshot.variables.items():
        if k in key_set:
            new_vars[k] = placeholder
            actually_redacted.append(k)
        else:
            new_vars[k] = v

    name = new_name or f"{snapshot.name}-redacted"

    new_snap = Snapshot(
        name=name,
        variables=new_vars,
        description=snapshot.description,
        tags=list(snapshot.tags),
    )

    return RedactResult(
        snapshot=new_snap,
        redacted_keys=sorted(actually_redacted),
        placeholder=placeholder,
    )
