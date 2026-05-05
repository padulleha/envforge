"""CLI commands for snapshot merging."""

from __future__ import annotations

import argparse
import sys

from envforge.cli import get_store
from envforge.merge import ConflictStrategy, MergeConflictError, merge_snapshots


def cmd_merge(args: argparse.Namespace) -> None:
    store = get_store(args)

    base = store.get(args.base)
    if base is None:
        print(f"Error: snapshot '{args.base}' not found.", file=sys.stderr)
        sys.exit(1)

    other = store.get(args.other)
    if other is None:
        print(f"Error: snapshot '{args.other}' not found.", file=sys.stderr)
        sys.exit(1)

    strategy = ConflictStrategy(args.strategy)

    try:
        merged = merge_snapshots(
            base,
            other,
            name=args.name,
            strategy=strategy,
            description=args.description,
        )
    except MergeConflictError as exc:
        print(f"Merge aborted — conflicts detected:", file=sys.stderr)
        for key, (bv, ov) in sorted(exc.conflicts.items()):
            print(f"  {key}: '{bv}' vs '{ov}'", file=sys.stderr)
        sys.exit(1)

    store.save(merged)
    print(
        f"Merged '{args.base}' + '{args.other}' → '{args.name}' "
        f"({len(merged.variables)} variables, strategy={strategy.value})"
    )


def register_merge_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("merge", help="Merge two snapshots into a new one")
    p.add_argument("base", help="Name of the base snapshot")
    p.add_argument("other", help="Name of the snapshot to merge in")
    p.add_argument("name", help="Name for the resulting merged snapshot")
    p.add_argument("-d", "--description", default=None, help="Description for merged snapshot")
    p.add_argument(
        "--strategy",
        choices=[s.value for s in ConflictStrategy],
        default=ConflictStrategy.USE_OTHER.value,
        help="How to resolve conflicting keys (default: other)",
    )
    p.set_defaults(func=cmd_merge)
