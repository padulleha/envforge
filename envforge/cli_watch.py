"""CLI commands for watching environment variable changes."""
from __future__ import annotations

import os
import time
import argparse
from typing import Optional

from envforge.watch import poll_once, snapshot_to_baseline
from envforge.store import SnapshotStore


def cmd_watch(args: argparse.Namespace, store: Optional[SnapshotStore] = None) -> int:
    """Poll the environment for changes against a snapshot or the current env."""
    if store is None:
        from envforge.cli import get_store
        store = get_store(args)

    interval: int = getattr(args, "interval", 2)
    count: int = getattr(args, "count", 0)  # 0 means unlimited
    keys = getattr(args, "keys", None) or None
    snapshot_name: Optional[str] = getattr(args, "snapshot", None)

    if snapshot_name:
        snap = store.get(snapshot_name)
        if snap is None:
            print(f"Snapshot '{snapshot_name}' not found.")
            return 1
        baseline = snapshot_to_baseline(snap)
        print(f"Watching against snapshot '{snapshot_name}' (interval={interval}s)")
    else:
        baseline = dict(os.environ)
        print(f"Watching against current environment (interval={interval}s)")

    if keys:
        print(f"Filtering keys: {', '.join(keys)}")

    iterations = 0
    try:
        while True:
            event = poll_once(baseline, keys=keys)
            if event.has_changes():
                print(event.format())
            iterations += 1
            if count and iterations >= count:
                break
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nWatch stopped.")
    return 0


def register_watch_commands(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("watch", help="Watch for environment variable changes")
    p.add_argument(
        "--snapshot", "-s", default=None,
        help="Snapshot name to use as baseline (default: current environment)"
    )
    p.add_argument(
        "--interval", "-i", type=int, default=2,
        help="Poll interval in seconds (default: 2)"
    )
    p.add_argument(
        "--count", "-n", type=int, default=0,
        help="Number of polls before stopping (0 = unlimited)"
    )
    p.add_argument(
        "--keys", "-k", nargs="+", default=None,
        help="Limit watching to specific keys"
    )
    p.set_defaults(func=cmd_watch)
