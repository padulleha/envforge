"""CLI commands for filtering snapshots."""
from __future__ import annotations

import argparse
import sys

from envforge.cli import get_store
from envforge.snapshot_filter import FilterCriteria, filter_snapshots


def cmd_filter(args: argparse.Namespace) -> int:
    store = get_store(args)
    names = store.list()
    if not names:
        print("No snapshots found.")
        return 0

    snapshots = [s for s in (store.get(n) for n in names) if s is not None]

    tags = args.tag if args.tag else []
    criteria = FilterCriteria(
        key_pattern=args.key or None,
        value_pattern=args.value or None,
        name_pattern=args.name or None,
        tags=tags,
        min_keys=args.min_keys,
        max_keys=args.max_keys,
    )

    results = filter_snapshots(snapshots, criteria)

    if not results:
        print("No snapshots matched the given criteria.")
        return 1

    for r in results:
        print(r.summary())
        if args.verbose and r.matched_keys:
            for k in r.matched_keys:
                print(f"  {k}={r.snapshot.variables[k]}")

    return 0


def register_filter_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("filter", help="Filter snapshots by key/value/tag patterns")
    p.add_argument("--key", metavar="PATTERN", help="Glob pattern for variable keys")
    p.add_argument("--value", metavar="PATTERN", help="Glob pattern for variable values")
    p.add_argument("--name", metavar="PATTERN", help="Glob pattern for snapshot names")
    p.add_argument("--tag", metavar="TAG", action="append", help="Require tag (repeatable)")
    p.add_argument("--min-keys", type=int, metavar="N", help="Minimum number of keys")
    p.add_argument("--max-keys", type=int, metavar="N", help="Maximum number of keys")
    p.add_argument("-v", "--verbose", action="store_true", help="Show matching key=value pairs")
    p.set_defaults(func=cmd_filter)
