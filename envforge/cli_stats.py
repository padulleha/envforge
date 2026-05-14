"""CLI commands for snapshot statistics."""
from __future__ import annotations

import argparse
import sys

from envforge.cli import get_store
from envforge.snapshot_stats import compute_stats, multi_summary


def cmd_stats(args: argparse.Namespace) -> int:
    """Show statistics for one or all snapshots."""
    store = get_store(args)

    if args.name:
        snap = store.get(args.name)
        if snap is None:
            print(f"Error: snapshot '{args.name}' not found.", file=sys.stderr)
            return 1
        stats = compute_stats(snap)
        print(stats.summary())
        return 0

    names = store.list()
    if not names:
        print("No snapshots found.")
        return 0

    snapshots = [store.get(n) for n in names if store.get(n) is not None]
    results = multi_summary(snapshots)

    header = f"{'NAME':<25} {'KEYS':>6} {'EMPTY':>6} {'AVG LEN':>8} {'TAGS':>5}"
    print(header)
    print("-" * len(header))
    for name, st in sorted(results.items()):
        print(
            f"{st.name:<25} {st.key_count:>6} {st.empty_value_count:>6}"
            f" {st.avg_value_length:>8.1f} {st.tag_count:>5}"
        )
    return 0


def register_stats_commands(
    subparsers: argparse._SubParsersAction,
) -> None:
    p = subparsers.add_parser("stats", help="Show statistics for snapshots")
    p.add_argument(
        "name",
        nargs="?",
        default=None,
        help="Snapshot name (omit to list all)",
    )
    p.set_defaults(func=cmd_stats)
