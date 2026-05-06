"""Main CLI entry point for envforge."""

from __future__ import annotations

import argparse
import os
import sys

from envforge.snapshot import Snapshot
from envforge.store import SnapshotStore


DEFAULT_STORE = os.path.expanduser("~/.envforge/store.json")


def get_store(args: argparse.Namespace) -> SnapshotStore:
    path = getattr(args, "store", None) or DEFAULT_STORE
    return SnapshotStore(path)


def cmd_capture(args: argparse.Namespace) -> None:
    store = get_store(args)
    keys = args.keys if args.keys else None
    snap = Snapshot.capture(args.name, keys=keys)
    store.save(snap)
    count = len(snap.vars)
    print(f"Captured snapshot {args.name!r} with {count} variable(s).")


def cmd_apply(args: argparse.Namespace) -> None:
    store = get_store(args)
    snap = store.get(args.name)
    if snap is None:
        print(f"Snapshot {args.name!r} not found.")
        sys.exit(1)
    overwrite = not args.no_overwrite
    snap.apply(overwrite=overwrite)
    print(f"Applied snapshot {args.name!r}.")


def cmd_list(args: argparse.Namespace) -> None:
    store = get_store(args)
    names = store.list()
    if not names:
        print("(no snapshots)")
        return
    for name in names:
        print(name)


def cmd_delete(args: argparse.Namespace) -> None:
    store = get_store(args)
    try:
        store.delete(args.name)
        print(f"Deleted snapshot {args.name!r}.")
    except KeyError:
        print(f"Snapshot {args.name!r} not found.")
        sys.exit(1)


def cmd_show(args: argparse.Namespace) -> None:
    store = get_store(args)
    snap = store.get(args.name)
    if snap is None:
        print(f"Snapshot {args.name!r} not found.")
        sys.exit(1)
    for k, v in sorted(snap.vars.items()):
        print(f"{k}={v}")


def cmd_export(args: argparse.Namespace) -> None:
    from envforge.export import to_shell_export

    store = get_store(args)
    snap = store.get(args.name)
    if snap is None:
        print(f"Snapshot {args.name!r} not found.")
        sys.exit(1)
    shell = getattr(args, "shell", "bash")
    print(to_shell_export(snap, shell=shell))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envforge", description="Snapshot and restore environment variables."
    )
    parser.add_argument("--store", default=None, help="Path to store file")
    subparsers = parser.add_subparsers(dest="command")

    p_capture = subparsers.add_parser("capture", help="Capture current environment")
    p_capture.add_argument("name", help="Snapshot name")
    p_capture.add_argument("keys", nargs="*", help="Specific keys to capture")
    p_capture.set_defaults(func=cmd_capture)

    p_apply = subparsers.add_parser("apply", help="Apply a snapshot")
    p_apply.add_argument("name", help="Snapshot name")
    p_apply.add_argument("--no-overwrite", action="store_true")
    p_apply.set_defaults(func=cmd_apply)

    p_list = subparsers.add_parser("list", help="List snapshots")
    p_list.set_defaults(func=cmd_list)

    p_delete = subparsers.add_parser("delete", help="Delete a snapshot")
    p_delete.add_argument("name", help="Snapshot name")
    p_delete.set_defaults(func=cmd_delete)

    p_show = subparsers.add_parser("show", help="Show snapshot variables")
    p_show.add_argument("name", help="Snapshot name")
    p_show.set_defaults(func=cmd_show)

    p_export = subparsers.add_parser("export", help="Export snapshot as shell script")
    p_export.add_argument("name", help="Snapshot name")
    p_export.add_argument("--shell", default="bash", choices=["bash", "fish", "powershell"])
    p_export.set_defaults(func=cmd_export)

    from envforge.cli_encrypt import register_encrypt_commands
    from envforge.cli_tags import register_tag_commands
    from envforge.cli_history import register_history_commands
    from envforge.cli_merge import register_merge_commands
    from envforge.cli_template import register_template_commands
    from envforge.cli_schedule import register_schedule_commands
    from envforge.cli_compare import register_compare_commands
    from envforge.cli_pin import register_pin_commands

    register_encrypt_commands(subparsers)
    register_tag_commands(subparsers)
    register_history_commands(subparsers)
    register_merge_commands(subparsers)
    register_template_commands(subparsers)
    register_schedule_commands(subparsers)
    register_compare_commands(subparsers)
    register_pin_commands(subparsers)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)
    args.func(args)


if __name__ == "__main__":
    main()
