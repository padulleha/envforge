"""CLI commands for copying snapshots."""

from __future__ import annotations

import argparse

from envforge.copy import CopyError, copy_snapshot


def cmd_copy(args: argparse.Namespace, store) -> int:
    """Handle the ``envforge copy`` sub-command."""
    try:
        result = copy_snapshot(
            store,
            args.source,
            args.dest,
            overwrite=args.overwrite,
            tag=args.tag,
        )
    except CopyError as exc:
        print(f"Error: {exc}")
        return 1

    print(str(result))
    return 0


def register_copy_commands(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the ``copy`` sub-command on *subparsers*."""
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "copy",
        help="Copy a snapshot to a new name",
    )
    parser.add_argument("source", help="Name of the snapshot to copy")
    parser.add_argument("dest", help="Name for the new snapshot")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Replace destination if it already exists",
    )
    parser.add_argument(
        "--tag",
        default=None,
        metavar="TAG",
        help="Optional tag to attach to the copied snapshot",
    )
    parser.set_defaults(func=cmd_copy)
