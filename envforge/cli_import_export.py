"""CLI commands for importing and exporting snapshots to files."""

from __future__ import annotations

import argparse
import sys

from envforge.cli import get_store
from envforge.import_export_file import (
    UnsupportedFormatError,
    export_snapshot,
    import_snapshot,
)


def cmd_export(args: argparse.Namespace) -> int:
    store = get_store(args)
    snap = store.get(args.name)
    if snap is None:
        print(f"[error] Snapshot '{args.name}' not found.", file=sys.stderr)
        return 1
    try:
        out = export_snapshot(snap, args.file, fmt=args.format or None)
        print(f"Exported '{args.name}' → {out}")
        return 0
    except UnsupportedFormatError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1


def cmd_import(args: argparse.Namespace) -> int:
    store = get_store(args)
    try:
        snap = import_snapshot(
            args.file,
            name=args.name,
            fmt=args.format or None,
            description=args.description or "",
        )
    except FileNotFoundError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1
    except UnsupportedFormatError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    if store.get(args.name) is not None and not args.force:
        print(
            f"[error] Snapshot '{args.name}' already exists. Use --force to overwrite.",
            file=sys.stderr,
        )
        return 1

    store.save(snap)
    print(f"Imported snapshot '{args.name}' from {args.file} ({len(snap.variables)} vars).")
    return 0


def register_import_export_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    # export
    p_export = subparsers.add_parser("export", help="Export a snapshot to a file")
    p_export.add_argument("name", help="Snapshot name")
    p_export.add_argument("file", help="Destination file path")
    p_export.add_argument(
        "--format", choices=["json", "dotenv"], default="",
        help="File format (default: inferred from extension)",
    )
    p_export.set_defaults(func=cmd_export)

    # import
    p_import = subparsers.add_parser("import", help="Import a snapshot from a file")
    p_import.add_argument("name", help="Name to assign to the imported snapshot")
    p_import.add_argument("file", help="Source file path")
    p_import.add_argument(
        "--format", choices=["json", "dotenv"], default="",
        help="File format (default: inferred from extension)",
    )
    p_import.add_argument("--description", default="", help="Optional description")
    p_import.add_argument(
        "--force", action="store_true", help="Overwrite existing snapshot"
    )
    p_import.set_defaults(func=cmd_import)
