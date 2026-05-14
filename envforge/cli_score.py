"""CLI commands for snapshot scoring."""
from __future__ import annotations

import argparse
import sys

from envforge.snapshot_score import score_snapshot


def cmd_score(args: argparse.Namespace, store) -> int:
    """Score one or all snapshots and print results."""
    names = args.names if args.names else store.list()

    if not names:
        print("No snapshots found.", file=sys.stderr)
        return 1

    scores = []
    missing = []
    for name in names:
        snap = store.get(name)
        if snap is None:
            missing.append(name)
            continue
        scores.append(score_snapshot(snap))

    for m in missing:
        print(f"Warning: snapshot '{m}' not found.", file=sys.stderr)

    if not scores:
        return 1

    scores.sort(key=lambda s: s.score, reverse=True)

    if getattr(args, "verbose", False):
        for s in scores:
            print(s.format_text())
            print()
    else:
        for s in scores:
            print(s.summary())

    return 0


def register_score_commands(
    subparsers: argparse._SubParsersAction,
) -> None:
    p = subparsers.add_parser(
        "score",
        help="Score snapshots based on quality metrics",
    )
    p.add_argument(
        "names",
        nargs="*",
        metavar="NAME",
        help="Snapshot name(s) to score; omit to score all",
    )
    p.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed breakdown for each snapshot",
    )
    p.set_defaults(func=cmd_score)
