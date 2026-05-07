"""CLI commands for searching snapshots by key/value patterns."""
from __future__ import annotations

import argparse
import sys

from envforge.cli import get_store
from envforge.search import search_snapshots


def cmd_search(args: argparse.Namespace) -> int:
    store = get_store(args)
    names = store.list()
    if not names:
        print("No snapshots found.")
        return 0

    snapshots = {name: store.load(name) for name in names}

    if not args.key and not args.value:
        print("error: provide --key and/or --value pattern", file=sys.stderr)
        return 1

    try:
        results = search_snapshots(
            snapshots,
            key_pattern=args.key or None,
            value_pattern=args.value or None,
            use_regex=args.regex,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not results:
        print("No matches found.")
        return 0

    for result in results:
        print(result.summary())
    return 0


def register_search_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("search", help="Search snapshots by key/value pattern")
    p.add_argument("--key", default="", help="Pattern to match variable names (glob or regex)")
    p.add_argument("--value", default="", help="Pattern to match variable values (glob or regex)")
    p.add_argument(
        "--regex",
        action="store_true",
        default=False,
        help="Treat patterns as regular expressions",
    )
    p.set_defaults(func=cmd_search)
