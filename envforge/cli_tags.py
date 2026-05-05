"""CLI sub-commands for snapshot tag management."""

from __future__ import annotations

import argparse

from envforge.tags import add_tag, remove_tag, filter_by_tag, format_tags


def cmd_tag_add(args: argparse.Namespace, store) -> None:
    snap = store.get(args.name)
    if snap is None:
        print(f"Snapshot '{args.name}' not found.")
        return
    snap.tags = add_tag(snap.tags, args.tag)
    store.save(snap)
    print(f"Tag '#{args.tag}' added to '{args.name}'. Tags: {format_tags(snap.tags)}")


def cmd_tag_remove(args: argparse.Namespace, store) -> None:
    snap = store.get(args.name)
    if snap is None:
        print(f"Snapshot '{args.name}' not found.")
        return
    snap.tags = remove_tag(snap.tags, args.tag)
    store.save(snap)
    print(f"Tag '#{args.tag}' removed from '{args.name}'. Tags: {format_tags(snap.tags)}")


def cmd_tag_list(args: argparse.Namespace, store) -> None:
    names = store.list()
    if not names:
        print("No snapshots found.")
        return
    for name in names:
        snap = store.get(name)
        if snap:
            print(f"  {name}: {format_tags(snap.tags)}")


def cmd_tag_filter(args: argparse.Namespace, store) -> None:
    names = store.list()
    matched = filter_by_tag(names, args.tag, store)
    if not matched:
        print(f"No snapshots tagged '#{args.tag}'.")
    else:
        for name in matched:
            print(f"  {name}")


def register_tag_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    tag_parser = subparsers.add_parser("tag", help="Manage snapshot tags")
    tag_sub = tag_parser.add_subparsers(dest="tag_cmd", required=True)

    p_add = tag_sub.add_parser("add", help="Add a tag to a snapshot")
    p_add.add_argument("name", help="Snapshot name")
    p_add.add_argument("tag", help="Tag to add")
    p_add.set_defaults(func=cmd_tag_add)

    p_rm = tag_sub.add_parser("remove", help="Remove a tag from a snapshot")
    p_rm.add_argument("name", help="Snapshot name")
    p_rm.add_argument("tag", help="Tag to remove")
    p_rm.set_defaults(func=cmd_tag_remove)

    p_ls = tag_sub.add_parser("list", help="List tags for all snapshots")
    p_ls.set_defaults(func=cmd_tag_list)

    p_filter = tag_sub.add_parser("filter", help="List snapshots matching a tag")
    p_filter.add_argument("tag", help="Tag to filter by")
    p_filter.set_defaults(func=cmd_tag_filter)
