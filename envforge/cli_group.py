"""CLI commands for snapshot groups."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

from envforge.group import (
    SnapshotGroup,
    add_to_group,
    format_groups,
    get_group,
    groups_for_snapshot,
    remove_from_group,
)

_GROUPS_FILE = "groups.json"


def _groups_path(store_dir: str) -> Path:
    return Path(store_dir) / _GROUPS_FILE


def _load_groups(store_dir: str) -> List[SnapshotGroup]:
    p = _groups_path(store_dir)
    if not p.exists():
        return []
    data = json.loads(p.read_text())
    return [SnapshotGroup.from_dict(d) for d in data]


def _save_groups(store_dir: str, groups: List[SnapshotGroup]) -> None:
    p = _groups_path(store_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps([g.to_dict() for g in groups], indent=2))


def cmd_group_add(args: argparse.Namespace) -> int:
    groups = _load_groups(args.store_dir)
    try:
        groups = add_to_group(groups, args.group, args.snapshot, args.description)
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1
    _save_groups(args.store_dir, groups)
    print(f"Added '{args.snapshot}' to group '{args.group}'.")
    return 0


def cmd_group_remove(args: argparse.Namespace) -> int:
    groups = _load_groups(args.store_dir)
    groups = remove_from_group(groups, args.group, args.snapshot)
    _save_groups(args.store_dir, groups)
    print(f"Removed '{args.snapshot}' from group '{args.group}' (if present).")
    return 0


def cmd_group_list(args: argparse.Namespace) -> int:
    groups = _load_groups(args.store_dir)
    if getattr(args, "snapshot", None):
        groups = groups_for_snapshot(groups, args.snapshot)
    print(format_groups(groups))
    return 0


def cmd_group_show(args: argparse.Namespace) -> int:
    groups = _load_groups(args.store_dir)
    grp = get_group(groups, args.group)
    if grp is None:
        print(f"Group '{args.group}' not found.")
        return 1
    print(format_groups([grp]))
    return 0


def register_group_commands(subparsers: argparse._SubParsersAction, store_dir: str) -> None:
    def _defaults(p: argparse.ArgumentParser) -> None:
        p.set_defaults(store_dir=store_dir)

    p_add = subparsers.add_parser("group-add", help="Add a snapshot to a group")
    p_add.add_argument("group", help="Group name")
    p_add.add_argument("snapshot", help="Snapshot name")
    p_add.add_argument("--description", default="", help="Group description (created if new)")
    p_add.set_defaults(func=cmd_group_add)
    _defaults(p_add)

    p_rm = subparsers.add_parser("group-remove", help="Remove a snapshot from a group")
    p_rm.add_argument("group")
    p_rm.add_argument("snapshot")
    p_rm.set_defaults(func=cmd_group_remove)
    _defaults(p_rm)

    p_ls = subparsers.add_parser("group-list", help="List all groups (or groups for a snapshot)")
    p_ls.add_argument("--snapshot", default=None, help="Filter to groups containing this snapshot")
    p_ls.set_defaults(func=cmd_group_list)
    _defaults(p_ls)

    p_sh = subparsers.add_parser("group-show", help="Show members of a specific group")
    p_sh.add_argument("group")
    p_sh.set_defaults(func=cmd_group_show)
    _defaults(p_sh)
