"""CLI commands for snapshot pivot."""
from __future__ import annotations

import argparse
import sys
from typing import Optional

from envforge.snapshot_pivot import pivot_snapshot


def cmd_pivot(args: argparse.Namespace, get_store) -> int:
    store = get_store(args)
    snapshot = store.get(args.name)
    if snapshot is None:
        print(f"error: snapshot '{args.name}' not found", file=sys.stderr)
        return 1

    prefixes: Optional[list] = None
    if args.prefixes:
        prefixes = [p.strip() for p in args.prefixes.split(",") if p.strip()]

    result = pivot_snapshot(
        snapshot,
        separator=args.separator,
        min_prefix_length=args.min_prefix,
        prefixes=prefixes,
    )

    if args.summary:
        print(result.summary())
        return 0

    if not result.has_groups and not result.ungrouped:
        print("(no variables)")
        return 0

    print(result.format_text())
    return 0


def register_pivot_commands(
    subparsers: argparse._SubParsersAction, get_store
) -> None:
    p = subparsers.add_parser("pivot", help="Pivot snapshot variables by prefix")
    p.add_argument("name", help="Snapshot name")
    p.add_argument(
        "--separator",
        default="_",
        help="Key separator character (default: _)",
    )
    p.add_argument(
        "--min-prefix",
        type=int,
        default=1,
        dest="min_prefix",
        help="Minimum prefix length (default: 1)",
    )
    p.add_argument(
        "--prefixes",
        default=None,
        help="Comma-separated explicit prefixes to group by",
    )
    p.add_argument(
        "--summary",
        action="store_true",
        help="Print summary line only",
    )
    p.set_defaults(func=lambda a: cmd_pivot(a, get_store))
