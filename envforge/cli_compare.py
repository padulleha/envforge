"""CLI commands for snapshot comparison."""
from __future__ import annotations

import argparse
import sys

from envforge.compare import compare_snapshots


def cmd_compare(args: argparse.Namespace, store) -> int:
    """Compare two named snapshots and print a report."""
    base = store.get(args.base)
    if base is None:
        print(f"Error: snapshot {args.base!r} not found.", file=sys.stderr)
        return 1

    other = store.get(args.other)
    if other is None:
        print(f"Error: snapshot {args.other!r} not found.", file=sys.stderr)
        return 1

    report = compare_snapshots(base, other, base_name=args.base, other_name=args.other)

    if args.format == "text":
        print(report.format_text(show_unchanged=args.show_unchanged))
    elif args.format == "summary":
        print(report.summary())
    elif args.format == "json":
        import json
        data = {
            "base": args.base,
            "other": args.other,
            "added": report.added,
            "removed": report.removed,
            "changed": {k: list(v) for k, v in report.changed.items()},
            "unchanged": report.unchanged,
        }
        print(json.dumps(data, indent=2))

    return 0 if not report.has_differences else 2


def register_compare_commands(
    subparsers: argparse._SubParsersAction,
) -> None:
    p = subparsers.add_parser(
        "compare",
        help="Compare two snapshots and show differences",
    )
    p.add_argument("base", help="Name of the base snapshot")
    p.add_argument("other", help="Name of the snapshot to compare against")
    p.add_argument(
        "--format",
        choices=["text", "summary", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--show-unchanged",
        action="store_true",
        default=False,
        help="Also list keys that are identical in both snapshots",
    )
    p.set_defaults(func=cmd_compare)
