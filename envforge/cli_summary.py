"""CLI commands for snapshot summaries."""
from __future__ import annotations

import argparse
import sys

from envforge.cli import get_store
from envforge.snapshot_summary import multi_summary, summarise


def cmd_summary(args: argparse.Namespace) -> int:
    """Print a summary for one or all snapshots."""
    store = get_store(args)

    if args.name:
        snap = store.get(args.name)
        if snap is None:
            print(f"Error: snapshot '{args.name}' not found.", file=sys.stderr)
            return 1
        s = summarise(snap)
        print(s.detail() if args.detail else s.one_line())
        return 0

    # All snapshots
    names = store.list()
    if not names:
        print("No snapshots found.")
        return 0

    snapshots = [store.get(n) for n in names if store.get(n) is not None]
    print(multi_summary(snapshots, detail=args.detail))
    return 0


def register_summary_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "summary",
        help="Show a human-readable summary of one or all snapshots",
    )
    p.add_argument(
        "name",
        nargs="?",
        default=None,
        help="Snapshot name (omit to summarise all)",
    )
    p.add_argument(
        "--detail",
        action="store_true",
        default=False,
        help="Show detailed multi-line output",
    )
    p.set_defaults(func=cmd_summary)
