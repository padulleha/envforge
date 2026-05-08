"""Promote a snapshot from one environment tier to another (e.g. dev -> staging -> prod)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

DEFAULT_TIERS: List[str] = ["dev", "staging", "prod"]


class PromoteError(Exception):
    """Raised when a promotion cannot be completed."""


@dataclass
class PromoteResult:
    source_name: str
    dest_name: str
    tier_from: str
    tier_to: str
    keys_copied: int
    overwritten: bool = False

    def __str__(self) -> str:
        action = "overwrote" if self.overwritten else "created"
        return (
            f"Promoted '{self.source_name}' ({self.tier_from}) -> "
            f"'{self.dest_name}' ({self.tier_to}): {action} {self.keys_copied} key(s)"
        )


def _next_tier(current: str, tiers: List[str]) -> str:
    """Return the tier that follows *current* in *tiers*."""
    try:
        idx = tiers.index(current)
    except ValueError:
        raise PromoteError(
            f"Tier '{current}' not found in tier list: {tiers}"
        )
    if idx + 1 >= len(tiers):
        raise PromoteError(
            f"Tier '{current}' is already the last tier — cannot promote further."
        )
    return tiers[idx + 1]


def promote_snapshot(
    store,
    source_name: str,
    tier_from: str,
    *,
    dest_name: Optional[str] = None,
    tiers: Optional[List[str]] = None,
    overwrite: bool = False,
) -> PromoteResult:
    """Copy *source_name* to the next environment tier.

    Parameters
    ----------
    store:        SnapshotStore instance.
    source_name:  Name of the snapshot to promote.
    tier_from:    Current tier label (e.g. ``"dev"``).
    dest_name:    Explicit destination name; auto-generated when omitted.
    tiers:        Ordered tier list; defaults to ``DEFAULT_TIERS``.
    overwrite:    Allow overwriting an existing destination snapshot.
    """
    tiers = tiers or DEFAULT_TIERS
    tier_to = _next_tier(tier_from, tiers)

    source = store.get(source_name)
    if source is None:
        raise PromoteError(f"Snapshot '{source_name}' not found.")

    if dest_name is None:
        # Replace the first occurrence of tier_from in the name, or append tier suffix.
        if tier_from in source_name:
            dest_name = source_name.replace(tier_from, tier_to, 1)
        else:
            dest_name = f"{source_name}-{tier_to}"

    existing = store.get(dest_name)
    if existing is not None and not overwrite:
        raise PromoteError(
            f"Destination snapshot '{dest_name}' already exists. "
            "Use --overwrite to replace it."
        )

    import copy as _copy
    from envforge.snapshot import Snapshot
    import datetime

    promoted = Snapshot(
        name=dest_name,
        variables=_copy.deepcopy(source.variables),
        created_at=datetime.datetime.utcnow().isoformat(),
        description=f"Promoted from '{source_name}' ({tier_from} -> {tier_to})",
        tags=list(source.tags) if hasattr(source, "tags") else [],
    )
    store.save(promoted)

    return PromoteResult(
        source_name=source_name,
        dest_name=dest_name,
        tier_from=tier_from,
        tier_to=tier_to,
        keys_copied=len(promoted.variables),
        overwritten=existing is not None,
    )
