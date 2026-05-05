"""Tag management for snapshots — attach, remove, and filter by tags."""

from __future__ import annotations

from typing import List, Optional


def add_tag(tags: List[str], tag: str) -> List[str]:
    """Return a new tag list with *tag* added (deduped, sorted)."""
    tag = tag.strip()
    if not tag:
        raise ValueError("Tag must not be empty.")
    return sorted(set(tags) | {tag})


def remove_tag(tags: List[str], tag: str) -> List[str]:
    """Return a new tag list with *tag* removed. Silent if absent."""
    return sorted(t for t in tags if t != tag)


def filter_by_tag(snapshot_names: List[str], tag: str, store) -> List[str]:
    """Return snapshot names whose tag list contains *tag*."""
    result = []
    for name in snapshot_names:
        snap = store.get(name)
        if snap and tag in snap.tags:
            result.append(name)
    return result


def format_tags(tags: List[str]) -> str:
    """Human-readable tag display string."""
    if not tags:
        return "(no tags)"
    return ", ".join(f"#{t}" for t in tags)
