"""CLI commands for renaming snapshots."""

from __future__ import annotations

import argparse

from envforge.rename import RenameError, rename_snapshot


def cmd_rename(args: argparse.Namespace, store) -> int:
    """Handle the ``envforge rename <old> <new>`` command."""
    try:
        result = rename_snapshot(
            store,
            args.old_name,
            args.new_name,
            overwrite=getattr(args, "overwrite", False),
        )
    except RenameError as exc:
        print(f"Error: {exc}")
        return 1

    print(result)
    return 0


def register_rename_commands(
    subparsers: argparse._SubParsersAction,  # type: ignore[type-arg]
) -> None:
    """Register the *rename* subcommand on *subparsers*."""
    parser = subparsers.add_parser(
        "rename",
        help="Rename a snapshot",
        description="Rename an existing snapshot to a new name.",
    )
    parser.add_argument("old_name", help="Current snapshot name")
    parser.add_argument("new_name", help="New snapshot name")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Replace the destination snapshot if it already exists",
    )
    parser.set_defaults(func=cmd_rename)
