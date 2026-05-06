"""Pin specific environment variable keys to fixed values within a snapshot."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class PinnedKey:
    key: str
    value: str
    reason: str = ""

    def to_dict(self) -> dict:
        return {"key": self.key, "value": self.value, "reason": self.reason}

    @classmethod
    def from_dict(cls, data: dict) -> "PinnedKey":
        return cls(
            key=data["key"],
            value=data["value"],
            reason=data.get("reason", ""),
        )


def add_pin(pins: List[dict], key: str, value: str, reason: str = "") -> List[dict]:
    """Add or update a pin for a key. Returns updated list of pin dicts."""
    if not key:
        raise ValueError("Pin key must not be empty.")
    updated = [p for p in pins if p["key"] != key]
    updated.append(PinnedKey(key=key, value=value, reason=reason).to_dict())
    return sorted(updated, key=lambda p: p["key"])


def remove_pin(pins: List[dict], key: str) -> List[dict]:
    """Remove a pin by key. Returns updated list."""
    result = [p for p in pins if p["key"] != key]
    if len(result) == len(pins):
        raise KeyError(f"No pin found for key: {key!r}")
    return result


def apply_pins(env: Dict[str, str], pins: List[dict]) -> Dict[str, str]:
    """Override env values with pinned values. Returns new dict."""
    result = dict(env)
    for p in pins:
        result[p["key"]] = p["value"]
    return result


def list_pins(pins: List[dict]) -> List[PinnedKey]:
    """Return list of PinnedKey objects."""
    return [PinnedKey.from_dict(p) for p in pins]


def format_pins(pins: List[dict]) -> str:
    """Return a human-readable table of pinned keys."""
    if not pins:
        return "(no pinned keys)"
    lines = []
    for p in list_pins(pins):
        reason_part = f"  # {p.reason}" if p.reason else ""
        lines.append(f"  {p.key}={p.value!r}{reason_part}")
    return "\n".join(lines)
