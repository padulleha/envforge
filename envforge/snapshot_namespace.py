"""Namespace support for grouping snapshots by dot-separated prefix."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class NamespaceTree:
    """Hierarchical view of snapshot names organised by namespace."""

    root: str
    children: Dict[str, "NamespaceTree"] = field(default_factory=dict)
    snapshots: List[str] = field(default_factory=list)

    def insert(self, name: str) -> None:
        """Insert a snapshot name into the tree."""
        parts = name.split(".", 1)
        if len(parts) == 1:
            self.snapshots.append(name)
        else:
            ns, remainder = parts
            if ns not in self.children:
                self.children[ns] = NamespaceTree(root=ns)
            self.children[ns].insert(remainder)

    def format(self, indent: int = 0) -> str:
        """Return a human-readable tree representation."""
        lines: List[str] = []
        prefix = "  " * indent
        for snap in sorted(self.snapshots):
            lines.append(f"{prefix}- {snap}")
        for ns, subtree in sorted(self.children.items()):
            lines.append(f"{prefix}[{ns}]")
            lines.append(subtree.format(indent + 1))
        return "\n".join(lines)


def infer_namespace(name: str) -> Optional[str]:
    """Return the top-level namespace of *name*, or None if there is none."""
    parts = name.split(".", 1)
    return parts[0] if len(parts) > 1 else None


def group_by_namespace(names: List[str]) -> Dict[str, List[str]]:
    """Return a mapping of top-level namespace -> list of snapshot names.

    Snapshots without a namespace are stored under the empty string key.
    """
    result: Dict[str, List[str]] = {}
    for name in names:
        ns = infer_namespace(name) or ""
        result.setdefault(ns, []).append(name)
    return result


def build_namespace_tree(names: List[str]) -> NamespaceTree:
    """Build a full :class:`NamespaceTree` from a flat list of snapshot names."""
    tree = NamespaceTree(root="<root>")
    for name in names:
        tree.insert(name)
    return tree
