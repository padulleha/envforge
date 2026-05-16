"""CLI commands for exporting snapshot diffs."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envforge.cli import get_store
from envforge.diff import SnapshotDiff
from envforge.snapshot_diff_export import ExportFormat, export_diff


def cmd_diff_export(args: argparse.Namespace) -> int:
    store = get_store(args)
    base = store.get(args.base)
    if base is None:
        print(f"error: snapshot '{args.base}' not found", file=sys.stderr)
        return 1
    other = store.get(args.other)
    if other is None:
        print(f"error: snapshot '{args.other}' not found", file=sys.stderr)
        return 1

    diff = SnapshotDiff(base=base, other=other)
    fmt: ExportFormat = args.format

    try:
        result = export_diff(diff, fmt=fmt)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.output:
        Path(args.output).write_text(result.content, encoding="utf-8")
        print(f"Diff exported to {args.output} ({fmt})")
    else:
        print(result.content)

    return 0


def register_diff_export_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "diff-export",
        help="Export the diff between two snapshots to json/markdown/csv",
    )
    p.add_argument("base", help="Base snapshot name")
    p.add_argument("other", help="Other snapshot name")
    p.add_argument(
        "--format",
        choices=["json", "markdown", "csv"],
        default="json",
        dest="format",
        help="Output format (default: json)",
    )
    p.add_argument(
        "--output",
        metavar="FILE",
        default=None,
        help="Write output to FILE instead of stdout",
    )
    p.set_defaults(func=cmd_diff_export)
