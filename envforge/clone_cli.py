"""CLI commands for cloning snapshots."""
from __future__ import annotations

import argparse

from envforge.cli import get_store
from envforge.clone import CloneError, clone_snapshot


def cmd_clone(args: argparse.Namespace) -> int:
    """Clone an existing snapshot under a new name."""
    store = get_store(args)
    try:
        result = clone_snapshot(
            store=store,
            source_name=args.source,
            dest_name=args.dest,
            overwrite=args.overwrite,
            tag=args.tag,
        )
    except CloneError as exc:
        print(f"error: {exc}")
        return 1

    print(str(result))
    return 0


def register_clone_commands(
    subparsers: argparse._SubParsersAction,  # type: ignore[type-arg]
) -> None:
    """Attach the 'clone' sub-command to *subparsers*."""
    p = subparsers.add_parser(
        "clone",
        help="Clone a snapshot under a new name",
    )
    p.add_argument("source", help="Name of the snapshot to clone")
    p.add_argument("dest", help="Name for the new snapshot")
    p.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite destination if it already exists",
    )
    p.add_argument(
        "--tag",
        metavar="TAG",
        default=None,
        help="Optional tag to add to the cloned snapshot",
    )
    p.set_defaults(func=cmd_clone)
