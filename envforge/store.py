"""Persistent storage for environment snapshots using JSON files."""

import json
import os
from pathlib import Path
from typing import List, Optional

from envforge.snapshot import Snapshot

DEFAULT_STORE_PATH = Path.home() / ".envforge" / "snapshots.json"


class SnapshotStore:
    """Manages loading and saving snapshots to a JSON file."""

    def __init__(self, store_path: Optional[Path] = None):
        self.store_path = Path(store_path) if store_path else DEFAULT_STORE_PATH
        self._snapshots: dict = {}
        self._load()

    def _load(self) -> None:
        """Load snapshots from disk."""
        if self.store_path.exists():
            with open(self.store_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            self._snapshots = {name: Snapshot.from_dict(data) for name, data in raw.items()}
        else:
            self._snapshots = {}

    def _save(self) -> None:
        """Persist snapshots to disk."""
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.store_path, "w", encoding="utf-8") as f:
            json.dump(
                {name: snap.to_dict() for name, snap in self._snapshots.items()},
                f,
                indent=2,
            )

    def save(self, snapshot: Snapshot) -> None:
        """Add or update a snapshot in the store."""
        self._snapshots[snapshot.name] = snapshot
        self._save()

    def get(self, name: str) -> Optional[Snapshot]:
        """Retrieve a snapshot by name."""
        return self._snapshots.get(name)

    def delete(self, name: str) -> bool:
        """Remove a snapshot by name. Returns True if deleted, False if not found."""
        if name in self._snapshots:
            del self._snapshots[name]
            self._save()
            return True
        return False

    def list_all(self) -> List[Snapshot]:
        """Return all stored snapshots sorted by creation time."""
        return sorted(self._snapshots.values(), key=lambda s: s.created_at)

    def exists(self, name: str) -> bool:
        """Check if a snapshot with the given name exists."""
        return name in self._snapshots

    def __len__(self) -> int:
        return len(self._snapshots)
