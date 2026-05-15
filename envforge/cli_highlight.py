"""CLI commands for snapshot-highlight feature."""
from __future__ import annotations

import argparse
import sys

from envforge.snapshot_highlight import highlight_snapshot


def cmd_highlight(args: argparse.Namespace, store) -> int:
    snapshot = store.get(args.name)
    if snapshot is None:
        print(f"Error: snapshot '{args.name}' not found.", file=sys.stderr)
        return 1

    if not args.pattern:
        print("Error: at least one pattern is required.", file=sys.stderr)
        return 1

    result = highlight_snapshot(
        snapshot,
        patterns=args.pattern,
        case_sensitive=args.case_sensitive,
    )

    if not result:
        print(result.summary())
        return 0

    print(result.format_text(mask_values=args.mask))
    return 0


def register_highlight_commands(
    subparsers: argparse._SubParsersAction,
    get_store,
) -> None:
    p = subparsers.add_parser(
        "highlight",
        help="Show specific keys from a snapshot matching glob patterns.",
    )
    p.add_argument("name", help="Snapshot name")
    p.add_argument(
        "pattern",
        nargs="+",
        help="Glob pattern(s) to match key names (e.g. 'AWS_*').",
    )
    p.add_argument(
        "--case-sensitive",
        action="store_true",
        default=False,
        help="Use case-sensitive pattern matching (default: case-insensitive).",
    )
    p.add_argument(
        "--mask",
        action="store_true",
        default=False,
        help="Replace values with *** in output.",
    )

    def _run(a: argparse.Namespace) -> None:
        sys.exit(cmd_highlight(a, get_store(a)))

    p.set_defaults(func=_run)
