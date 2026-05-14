"""CLI commands for sorting and listing snapshots in order."""
from __future__ import annotations

import argparse

from envforge.cli import get_store
from envforge.snapshot_sort import SortCriteria, SortKey, SortOrder, sort_snapshots


def cmd_sort(args: argparse.Namespace) -> int:
    """List snapshots sorted by the chosen field."""
    store = get_store(args)
    names = store.list()
    if not names:
        print("No snapshots found.")
        return 0

    snapshots = []
    for name in names:
        snap = store.get(name)
        if snap is not None:
            snapshots.append(snap)

    try:
        key = SortKey(args.sort_key)
    except ValueError:
        valid = ", ".join(k.value for k in SortKey)
        print(f"Error: invalid sort key '{args.sort_key}'. Choose from: {valid}")
        return 1

    try:
        order = SortOrder(args.order)
    except ValueError:
        print(f"Error: invalid order '{args.order}'. Choose 'asc' or 'desc'.")
        return 1

    criteria = SortCriteria(key=key, order=order)
    result = sort_snapshots(snapshots, criteria)

    print(result.summary())
    print()
    for snap in result.snapshots:
        key_count = len(snap.variables)
        desc = f" — {snap.description}" if snap.description else ""
        created = f" [{snap.created_at}]" if snap.created_at else ""
        print(f"  {snap.name} ({key_count} keys){created}{desc}")

    return 0


def register_sort_commands(subparsers) -> None:
    p = subparsers.add_parser("sort", help="List snapshots in sorted order")
    p.add_argument(
        "--key",
        dest="sort_key",
        default=SortKey.NAME.value,
        choices=[k.value for k in SortKey],
        help="Field to sort by (default: name)",
    )
    p.add_argument(
        "--order",
        default=SortOrder.ASC.value,
        choices=[o.value for o in SortOrder],
        help="Sort order: asc or desc (default: asc)",
    )
    p.set_defaults(func=cmd_sort)
