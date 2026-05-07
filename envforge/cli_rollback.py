"""CLI commands for snapshot rollback."""

from __future__ import annotations

import argparse
import sys

from envforge.cli import get_store
from envforge.store_history import load_history, record_and_save
from envforge.rollback import get_rollback_points, rollback_to


def cmd_rollback_list(args: argparse.Namespace) -> int:
    store = get_store(args)
    history = load_history(args.store)
    points = get_rollback_points(args.name, history, limit=args.limit)
    if not points:
        print(f"No rollback points found for '{args.name}'.")
        return 0
    print(f"Rollback points for '{args.name}':")
    for point in points:
        print(" ", point.format())
    return 0


def cmd_rollback_apply(args: argparse.Namespace) -> int:
    store = get_store(args)
    history = load_history(args.store)
    snap = rollback_to(args.name, args.index, history)
    if snap is None:
        print(
            f"Error: rollback index {args.index} not found for '{args.name}'.",
            file=sys.stderr,
        )
        return 1
    snap.name = args.name  # keep the canonical name
    store.save(snap)
    record_and_save(
        args.store,
        history,
        action="rollback",
        name=args.name,
        detail=f"restored to index {args.index}",
        snapshot=snap,
    )
    print(f"Rolled back '{args.name}' to index {args.index}.")
    return 0


def register_rollback_commands(
    subparsers: argparse._SubParsersAction,
) -> None:
    rb = subparsers.add_parser("rollback", help="Rollback snapshot to a previous state")
    rb_sub = rb.add_subparsers(dest="rollback_cmd", required=True)

    ls = rb_sub.add_parser("list", help="List rollback points for a snapshot")
    ls.add_argument("name", help="Snapshot name")
    ls.add_argument("--limit", type=int, default=10, help="Max points to show")
    ls.set_defaults(func=cmd_rollback_list)

    ap = rb_sub.add_parser("apply", help="Restore snapshot to a rollback point")
    ap.add_argument("name", help="Snapshot name")
    ap.add_argument("index", type=int, help="Rollback point index (from rollback list)")
    ap.set_defaults(func=cmd_rollback_apply)
