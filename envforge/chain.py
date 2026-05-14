"""Chain multiple snapshots together for sequential apply."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SnapshotChain:
    name: str
    steps: List[str] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "steps": list(self.steps),
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SnapshotChain":
        return cls(
            name=data["name"],
            steps=list(data.get("steps", [])),
            description=data.get("description", ""),
        )

    def format(self) -> str:
        lines = [f"Chain: {self.name}"]
        if self.description:
            lines.append(f"  Description: {self.description}")
        for i, step in enumerate(self.steps, 1):
            lines.append(f"  {i}. {step}")
        return "\n".join(lines)


def add_chain(chains: List[SnapshotChain], name: str, steps: List[str], description: str = "") -> List[SnapshotChain]:
    """Add or replace a chain by name."""
    if not name:
        raise ValueError("Chain name must not be empty")
    if not steps:
        raise ValueError("Chain must have at least one step")
    updated = [c for c in chains if c.name != name]
    updated.append(SnapshotChain(name=name, steps=steps, description=description))
    return sorted(updated, key=lambda c: c.name)


def remove_chain(chains: List[SnapshotChain], name: str) -> List[SnapshotChain]:
    """Remove a chain by name; raises KeyError if not found."""
    if not any(c.name == name for c in chains):
        raise KeyError(f"Chain '{name}' not found")
    return [c for c in chains if c.name != name]


def get_chain(chains: List[SnapshotChain], name: str) -> Optional[SnapshotChain]:
    for c in chains:
        if c.name == name:
            return c
    return None


def apply_chain(chain: SnapshotChain, store, overwrite: bool = True) -> List[str]:
    """Apply each snapshot in the chain sequentially. Returns list of applied names."""
    applied = []
    for step in chain.steps:
        snap = store.get(step)
        if snap is None:
            raise KeyError(f"Snapshot '{step}' not found in store")
        snap.apply(overwrite=overwrite)
        applied.append(step)
    return applied
