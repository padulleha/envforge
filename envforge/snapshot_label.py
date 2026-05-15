"""Snapshot labelling — attach arbitrary key/value labels to snapshots."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class LabelSet:
    snapshot_name: str
    labels: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"snapshot_name": self.snapshot_name, "labels": dict(self.labels)}

    @classmethod
    def from_dict(cls, data: dict) -> "LabelSet":
        return cls(
            snapshot_name=data["snapshot_name"],
            labels=dict(data.get("labels", {})),
        )

    def format(self) -> str:
        if not self.labels:
            return f"{self.snapshot_name}: (no labels)"
        pairs = ", ".join(f"{k}={v}" for k, v in sorted(self.labels.items()))
        return f"{self.snapshot_name}: {pairs}"


class LabelError(Exception):
    pass


def add_label(label_sets: List[LabelSet], snapshot_name: str, key: str, value: str) -> List[LabelSet]:
    """Add or update a label on a snapshot; returns updated list."""
    if not key:
        raise LabelError("Label key must not be empty.")
    for ls in label_sets:
        if ls.snapshot_name == snapshot_name:
            ls.labels[key] = value
            return label_sets
    label_sets.append(LabelSet(snapshot_name=snapshot_name, labels={key: value}))
    return label_sets


def remove_label(label_sets: List[LabelSet], snapshot_name: str, key: str) -> List[LabelSet]:
    """Remove a label from a snapshot; silently ignores missing key."""
    for ls in label_sets:
        if ls.snapshot_name == snapshot_name:
            ls.labels.pop(key, None)
            return label_sets
    return label_sets


def get_labels(label_sets: List[LabelSet], snapshot_name: str) -> Optional[LabelSet]:
    for ls in label_sets:
        if ls.snapshot_name == snapshot_name:
            return ls
    return None


def filter_by_label(label_sets: List[LabelSet], key: str, value: Optional[str] = None) -> List[LabelSet]:
    """Return label sets where key exists (and optionally matches value)."""
    results = []
    for ls in label_sets:
        if key in ls.labels:
            if value is None or ls.labels[key] == value:
                results.append(ls)
    return results
