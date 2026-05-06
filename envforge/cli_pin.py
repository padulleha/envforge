"""CLI commands for managing pinned keys in a snapshot."""

from __future__ import annotations

import argparse

from envforge.cli import get_store
from envforge.pin import add_pin, remove_pin, apply_pins, format_pins


def cmd_pin_add(args: argparse.Namespace) -> None:
    store = get_store(args)
    snap = store.get(args.name)
    if snap is None:
        print(f"Snapshot {args.name!r} not found.")
        return
    pins = snap.metadata.get("pins", [])
    pins = add_pin(pins, args.key, args.value, reason=args.reason or "")
    snap.metadata["pins"] = pins
    store.save(snap)
    print(f"Pinned {args.key!r} = {args.value!r} in snapshot {args.name!r}.")


def cmd_pin_remove(args: argparse.Namespace) -> None:
    store = get_store(args)
    snap = store.get(args.name)
    if snap is None:
        print(f"Snapshot {args.name!r} not found.")
        return
    pins = snap.metadata.get("pins", [])
    try:
        pins = remove_pin(pins, args.key)
    except KeyError as exc:
        print(str(exc))
        return
    snap.metadata["pins"] = pins
    store.save(snap)
    print(f"Removed pin for {args.key!r} from snapshot {args.name!r}.")


def cmd_pin_list(args: argparse.Namespace) -> None:
    store = get_store(args)
    snap = store.get(args.name)
    if snap is None:
        print(f"Snapshot {args.name!r} not found.")
        return
    pins = snap.metadata.get("pins", [])
    print(f"Pinned keys for {args.name!r}:")
    print(format_pins(pins))


def cmd_pin_apply(args: argparse.Namespace) -> None:
    """Apply pins to the snapshot's env values (modifies stored values)."""
    store = get_store(args)
    snap = store.get(args.name)
    if snap is None:
        print(f"Snapshot {args.name!r} not found.")
        return
    pins = snap.metadata.get("pins", [])
    if not pins:
        print(f"No pins defined for {args.name!r}.")
        return
    snap.vars = apply_pins(snap.vars, pins)
    store.save(snap)
    print(f"Applied {len(pins)} pin(s) to snapshot {args.name!r}.")


def register_pin_commands(subparsers: argparse._SubParsersAction) -> None:
    p_add = subparsers.add_parser("pin-add", help="Pin a key to a fixed value")
    p_add.add_argument("name", help="Snapshot name")
    p_add.add_argument("key", help="Environment variable key")
    p_add.add_argument("value", help="Fixed value")
    p_add.add_argument("--reason", default="", help="Optional reason")
    p_add.set_defaults(func=cmd_pin_add)

    p_rem = subparsers.add_parser("pin-remove", help="Remove a pinned key")
    p_rem.add_argument("name", help="Snapshot name")
    p_rem.add_argument("key", help="Key to unpin")
    p_rem.set_defaults(func=cmd_pin_remove)

    p_list = subparsers.add_parser("pin-list", help="List pinned keys")
    p_list.add_argument("name", help="Snapshot name")
    p_list.set_defaults(func=cmd_pin_list)

    p_apply = subparsers.add_parser("pin-apply", help="Apply pins to snapshot vars")
    p_apply.add_argument("name", help="Snapshot name")
    p_apply.set_defaults(func=cmd_pin_apply)
