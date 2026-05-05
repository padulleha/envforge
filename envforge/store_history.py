"""Mixin / helpers that wire SnapshotHistory into SnapshotStore persistence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from envforge.history import SnapshotHistory

_HISTORY_FILENAME = "history.json"


def load_history(store_dir: Path) -> SnapshotHistory:
    """Load history from *store_dir*/history.json; return empty log if absent."""
    path = store_dir / _HISTORY_FILENAME
    if not path.exists():
        return SnapshotHistory()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return SnapshotHistory.from_list(data)
    except (json.JSONDecodeError, KeyError):
        return SnapshotHistory()


def save_history(store_dir: Path, history: SnapshotHistory) -> None:
    """Persist *history* to *store_dir*/history.json."""
    store_dir.mkdir(parents=True, exist_ok=True)
    path = store_dir / _HISTORY_FILENAME
    path.write_text(json.dumps(history.to_list(), indent=2), encoding="utf-8")


def record_and_save(
    store_dir: Path,
    action: str,
    snapshot_name: str,
    detail: Optional[str] = None,
) -> None:
    """Convenience: load, append one entry, and save."""
    history = load_history(store_dir)
    history.record(action, snapshot_name, detail)
    save_history(store_dir, history)
