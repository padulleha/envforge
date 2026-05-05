"""Command-line interface for envforge."""

import os
import sys
import argparse

from envforge.snapshot import Snapshot
from envforge.store import SnapshotStore


def get_store() -> SnapshotStore:
    store_path = os.environ.get("ENVFORGE_STORE", os.path.expanduser("~/.envforge/snapshots.json"))
    return SnapshotStore(store_path)


def cmd_capture(args: argparse.Namespace) -> int:
    store = get_store()
    keys = args.keys if args.keys else None
    snapshot = Snapshot.capture(name=args.name, keys=keys, description=args.description)
    store.save(snapshot)
    print(f"Snapshot '{args.name}' captured ({len(snapshot.variables)} variables).")
    return 0


def cmd_apply(args: argparse.Namespace) -> int:
    store = get_store()
    snapshot = store.get(args.name)
    if snapshot is None:
        print(f"Error: snapshot '{args.name}' not found.", file=sys.stderr)
        return 1
    applied = snapshot.apply(overwrite=not args.no_overwrite)
    print(f"Applied {applied} variable(s) from snapshot '{args.name}'.")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    store = get_store()
    snapshots = store.list()
    if not snapshots:
        print("No snapshots found.")
        return 0
    for name in snapshots:
        snap = store.get(name)
        desc = f" — {snap.description}" if snap and snap.description else ""
        count = len(snap.variables) if snap else 0
        print(f"  {name} ({count} vars){desc}")
    return 0


def cmd_delete(args: argparse.Namespace) -> int:
    store = get_store()
    removed = store.delete(args.name)
    if not removed:
        print(f"Error: snapshot '{args.name}' not found.", file=sys.stderr)
        return 1
    print(f"Snapshot '{args.name}' deleted.")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    store = get_store()
    snapshot = store.get(args.name)
    if snapshot is None:
        print(f"Error: snapshot '{args.name}' not found.", file=sys.stderr)
        return 1
    print(f"Snapshot: {snapshot.name}")
    if snapshot.description:
        print(f"Description: {snapshot.description}")
    print(f"Created: {snapshot.created_at}")
    print(f"Variables ({len(snapshot.variables)}):")
    for key, value in sorted(snapshot.variables.items()):
        display = value if not args.mask else "***"
        print(f"  {key}={display}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envforge",
        description="Snapshot and restore environment variable sets.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_capture = sub.add_parser("capture", help="Capture current environment variables.")
    p_capture.add_argument("name", help="Name for the snapshot.")
    p_capture.add_argument("--keys", nargs="+", metavar="KEY", help="Specific keys to capture.")
    p_capture.add_argument("--description", "-d", default="", help="Optional description.")
    p_capture.set_defaults(func=cmd_capture)

    p_apply = sub.add_parser("apply", help="Apply a snapshot to the current environment.")
    p_apply.add_argument("name", help="Name of the snapshot to apply.")
    p_apply.add_argument("--no-overwrite", action="store_true", help="Skip variables already set.")
    p_apply.set_defaults(func=cmd_apply)

    p_list = sub.add_parser("list", help="List all saved snapshots.")
    p_list.set_defaults(func=cmd_list)

    p_delete = sub.add_parser("delete", help="Delete a snapshot.")
    p_delete.add_argument("name", help="Name of the snapshot to delete.")
    p_delete.set_defaults(func=cmd_delete)

    p_show = sub.add_parser("show", help="Show details of a snapshot.")
    p_show.add_argument("name", help="Name of the snapshot to show.")
    p_show.add_argument("--mask", action="store_true", help="Mask variable values.")
    p_show.set_defaults(func=cmd_show)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
