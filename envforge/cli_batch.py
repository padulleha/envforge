"""CLI commands for batch snapshot operations."""
from __future__ import annotations

import argparse

from envforge.batch import batch_apply, batch_capture, batch_delete


def cmd_batch_capture(args: argparse.Namespace, store) -> int:
    """Capture current env into each named snapshot."""
    result = batch_capture(store, args.names, keys=args.keys or None)
    for name in result.succeeded:
        print(f"[ok] captured '{name}'")
    for name in result.failed:
        print(f"[error] '{name}': {result.errors[name]}")
    return 0 if result.all_succeeded else 1


def cmd_batch_apply(args: argparse.Namespace, store) -> int:
    """Apply multiple snapshots in order."""
    result = batch_apply(store, args.names, overwrite=not args.no_overwrite)
    for name in result.succeeded:
        print(f"[ok] applied '{name}'")
    for name in result.failed:
        print(f"[error] '{name}': {result.errors[name]}")
    return 0 if result.all_succeeded else 1


def cmd_batch_delete(args: argparse.Namespace, store) -> int:
    """Delete multiple snapshots."""
    result = batch_delete(store, args.names)
    for name in result.succeeded:
        print(f"[ok] deleted '{name}'")
    for name in result.failed:
        print(f"[error] '{name}': {result.errors[name]}")
    return 0 if result.all_succeeded else 1


def register_batch_commands(subparsers, parent) -> None:
    # batch-capture
    p_cap = subparsers.add_parser("batch-capture", parents=[parent],
                                  help="Capture env into multiple snapshots")
    p_cap.add_argument("names", nargs="+", help="Snapshot names")
    p_cap.add_argument("--keys", nargs="*", help="Limit to specific env keys")
    p_cap.set_defaults(func=cmd_batch_capture)

    # batch-apply
    p_app = subparsers.add_parser("batch-apply", parents=[parent],
                                  help="Apply multiple snapshots in order")
    p_app.add_argument("names", nargs="+", help="Snapshot names")
    p_app.add_argument("--no-overwrite", action="store_true",
                       help="Skip keys already set in environment")
    p_app.set_defaults(func=cmd_batch_apply)

    # batch-delete
    p_del = subparsers.add_parser("batch-delete", parents=[parent],
                                  help="Delete multiple snapshots")
    p_del.add_argument("names", nargs="+", help="Snapshot names")
    p_del.set_defaults(func=cmd_batch_delete)
