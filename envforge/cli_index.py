"""CLI commands for the snapshot index."""
from __future__ import annotations

import argparse

from envforge.cli import get_store
from envforge.snapshot_index import build_index


def cmd_index_keys(args: argparse.Namespace) -> int:
    store = get_store(args)
    names = store.list()
    snaps = [store.get(n) for n in names if store.get(n) is not None]
    idx = build_index(snaps)  # type: ignore[arg-type]
    matches = idx.find_by_key(args.pattern)
    if not matches:
        print(f"No snapshots contain a key matching '{args.pattern}'.")
        return 0
    for name in sorted(matches):
        print(name)
    return 0


def cmd_index_tag(args: argparse.Namespace) -> int:
    store = get_store(args)
    names = store.list()
    snaps = [store.get(n) for n in names if store.get(n) is not None]
    idx = build_index(snaps)  # type: ignore[arg-type]
    matches = idx.find_by_tag(args.tag)
    if not matches:
        print(f"No snapshots tagged '{args.tag}'.")
        return 0
    for name in sorted(matches):
        print(name)
    return 0


def cmd_index_describe(args: argparse.Namespace) -> int:
    store = get_store(args)
    names = store.list()
    snaps = [store.get(n) for n in names if store.get(n) is not None]
    idx = build_index(snaps)  # type: ignore[arg-type]
    matches = idx.find_by_description(args.substring)
    if not matches:
        print(f"No snapshots whose description contains '{args.substring}'.")
        return 0
    for name in sorted(matches):
        print(name)
    return 0


def cmd_index_all_keys(args: argparse.Namespace) -> int:
    store = get_store(args)
    names = store.list()
    snaps = [store.get(n) for n in names if store.get(n) is not None]
    idx = build_index(snaps)  # type: ignore[arg-type]
    keys = sorted(idx.all_keys())
    if not keys:
        print("No keys found.")
        return 0
    for k in keys:
        print(k)
    return 0


def register_index_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p_keys = subparsers.add_parser("index-keys", help="Find snapshots by key glob")
    p_keys.add_argument("pattern", help="Key glob pattern (e.g. 'AWS_*')")
    p_keys.set_defaults(func=cmd_index_keys)

    p_tag = subparsers.add_parser("index-tag", help="Find snapshots by tag")
    p_tag.add_argument("tag", help="Tag to search for")
    p_tag.set_defaults(func=cmd_index_tag)

    p_desc = subparsers.add_parser("index-describe", help="Find snapshots by description substring")
    p_desc.add_argument("substring", help="Substring to search in descriptions")
    p_desc.set_defaults(func=cmd_index_describe)

    p_all = subparsers.add_parser("index-all-keys", help="List all unique keys across snapshots")
    p_all.set_defaults(func=cmd_index_all_keys)
