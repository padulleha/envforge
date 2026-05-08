"""CLI commands for archive export/import."""

from __future__ import annotations

import argparse
import sys

from envforge.archive import ArchiveError, export_archive, import_archive
from envforge.cli import get_store


def cmd_archive_export(args: argparse.Namespace) -> int:
    """Export one or more snapshots to a compressed archive file."""
    store = get_store(args)
    names: list[str] = args.names
    snapshots = []
    for name in names:
        snap = store.get(name)
        if snap is None:
            print(f"Error: snapshot '{name}' not found.", file=sys.stderr)
            return 1
        snapshots.append(snap)
    try:
        result = export_archive(snapshots, args.output)
        print(result)
    except ArchiveError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


def cmd_archive_import(args: argparse.Namespace) -> int:
    """Import snapshots from a compressed archive file into the store."""
    store = get_store(args)
    try:
        snapshots = import_archive(args.input)
    except ArchiveError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    overwritten = 0
    added = 0
    for snap in snapshots:
        exists = store.get(snap.name) is not None
        if exists and not args.overwrite:
            print(f"Skipping '{snap.name}' (already exists, use --overwrite to replace).")
            continue
        store.save(snap)
        if exists:
            overwritten += 1
        else:
            added += 1

    print(f"Imported {added} new, {overwritten} overwritten snapshot(s) from {args.input}.")
    return 0


def register_archive_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    # archive-export
    p_export = subparsers.add_parser("archive-export", help="Export snapshots to a .gz archive")
    p_export.add_argument("names", nargs="+", help="Snapshot name(s) to export")
    p_export.add_argument("-o", "--output", required=True, help="Destination archive file path")
    p_export.set_defaults(func=cmd_archive_export)

    # archive-import
    p_import = subparsers.add_parser("archive-import", help="Import snapshots from a .gz archive")
    p_import.add_argument("input", help="Archive file path to import from")
    p_import.add_argument("--overwrite", action="store_true", help="Overwrite existing snapshots")
    p_import.set_defaults(func=cmd_archive_import)
