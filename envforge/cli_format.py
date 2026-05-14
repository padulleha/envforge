"""CLI commands for snapshot formatting (table / compact)."""
from __future__ import annotations

import argparse
import sys

from envforge.cli import get_store
from envforge.snapshot_format import FormatOptions, format_compact, format_table


def cmd_format(args: argparse.Namespace) -> int:
    store = get_store(args)
    snapshot = store.get(args.name)
    if snapshot is None:
        print(f"Error: snapshot '{args.name}' not found.", file=sys.stderr)
        return 1

    options = FormatOptions(
        max_value_length=args.max_value_length,
        show_index=not args.no_index,
        show_types=args.show_types,
        title=args.title,
    )

    if args.style == "compact":
        print(format_compact(snapshot))
    else:
        print(format_table(snapshot, options))
    return 0


def register_format_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "format",
        help="Render a snapshot as a formatted table or compact key=value list.",
    )
    p.add_argument("name", help="Name of the snapshot to format.")
    p.add_argument(
        "--style",
        choices=["table", "compact"],
        default="table",
        help="Output style (default: table).",
    )
    p.add_argument(
        "--max-value-length",
        type=int,
        default=60,
        dest="max_value_length",
        help="Truncate values longer than this (default: 60).",
    )
    p.add_argument(
        "--no-index",
        action="store_true",
        default=False,
        help="Omit row numbers from table output.",
    )
    p.add_argument(
        "--show-types",
        action="store_true",
        default=False,
        dest="show_types",
        help="Add an inferred TYPE column to table output.",
    )
    p.add_argument(
        "--title",
        default=None,
        help="Override the table title line.",
    )
    p.set_defaults(func=cmd_format)
