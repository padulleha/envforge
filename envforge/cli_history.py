"""CLI sub-commands for inspecting snapshot history."""

from __future__ import annotations

import argparse

from envforge.cli import get_store
from envforge.store_history import load_history


def cmd_history_list(args: argparse.Namespace) -> None:
    """Print the N most-recent history entries."""
    store = get_store(args)
    history = load_history(store.store_dir)
    entries = history.recent(n=getattr(args, "limit", 20))
    if not entries:
        print("No history recorded yet.")
        return
    for entry in entries:
        print(entry.format())


def cmd_history_show(args: argparse.Namespace) -> None:
    """Print history for a specific snapshot."""
    store = get_store(args)
    history = load_history(store.store_dir)
    entries = history.for_snapshot(args.name)
    if not entries:
        print(f"No history for snapshot '{args.name}'.")
        return
    for entry in sorted(entries, key=lambda e: e.timestamp):
        print(entry.format())


def register_history_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    # history list
    p_list = subparsers.add_parser("history", help="Show recent snapshot activity")
    p_list.add_argument(
        "--limit", "-n", type=int, default=20, help="Number of entries to show (default 20)"
    )
    p_list.set_defaults(func=cmd_history_list)

    # history show <name>
    p_show = subparsers.add_parser("history-show", help="Show history for a specific snapshot")
    p_show.add_argument("name", help="Snapshot name")
    p_show.set_defaults(func=cmd_history_show)
