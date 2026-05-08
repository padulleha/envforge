"""CLI commands for snapshot backup and restore."""

from __future__ import annotations

import argparse
import sys

from envforge.restore import RestoreError, backup_snapshot, restore_snapshot


def cmd_backup(args: argparse.Namespace, store) -> int:
    """Create an auto-backup of a snapshot."""
    try:
        backup_name = backup_snapshot(store, args.name)
        print(f"Backup created: '{backup_name}'")
        return 0
    except RestoreError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_restore(args: argparse.Namespace, store) -> int:
    """Restore a snapshot from its backup (or an explicit backup name)."""
    backup_name: str | None = getattr(args, "from_backup", None) or None
    try:
        result = restore_snapshot(store, args.name, backup_name=backup_name)
        print(str(result))
        return 0
    except RestoreError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def register_restore_commands(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Attach backup/restore sub-commands to the given subparsers."""
    # --- backup ---
    p_backup = subparsers.add_parser(
        "backup",
        help="Create an auto-backup copy of a snapshot.",
    )
    p_backup.add_argument("name", help="Name of the snapshot to back up.")
    p_backup.set_defaults(func=cmd_backup)

    # --- restore ---
    p_restore = subparsers.add_parser(
        "restore",
        help="Restore a snapshot from its backup copy.",
    )
    p_restore.add_argument("name", help="Name of the snapshot to restore.")
    p_restore.add_argument(
        "--from-backup",
        dest="from_backup",
        default=None,
        metavar="BACKUP_NAME",
        help="Explicit backup snapshot name (defaults to auto-backup).",
    )
    p_restore.set_defaults(func=cmd_restore)
