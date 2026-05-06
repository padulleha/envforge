"""CLI commands for snapshot alias management."""

from __future__ import annotations

import argparse
import sys

from envforge.alias import add_alias, remove_alias, resolve_alias, format_aliases
from envforge.store import SnapshotStore


def _get_aliases(store: SnapshotStore) -> list:
    return store.meta.get("aliases", [])


def _save_aliases(store: SnapshotStore, raw: list) -> None:
    store.meta["aliases"] = raw
    store._save()


def _load_alias_objects(store: SnapshotStore):
    from envforge.alias import SnapshotAlias
    return [SnapshotAlias.from_dict(d) for d in _get_aliases(store)]


def cmd_alias_add(args: argparse.Namespace, store: SnapshotStore) -> int:
    aliases = _load_alias_objects(store)
    try:
        aliases = add_alias(aliases, args.alias, args.snapshot, getattr(args, "description", ""))
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    _save_aliases(store, [a.to_dict() for a in aliases])
    print(f"Alias '{args.alias}' -> '{args.snapshot}' saved.")
    return 0


def cmd_alias_remove(args: argparse.Namespace, store: SnapshotStore) -> int:
    aliases = _load_alias_objects(store)
    try:
        aliases = remove_alias(aliases, args.alias)
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    _save_aliases(store, [a.to_dict() for a in aliases])
    print(f"Alias '{args.alias}' removed.")
    return 0


def cmd_alias_list(args: argparse.Namespace, store: SnapshotStore) -> int:
    aliases = _load_alias_objects(store)
    print(format_aliases(aliases))
    return 0


def cmd_alias_resolve(args: argparse.Namespace, store: SnapshotStore) -> int:
    aliases = _load_alias_objects(store)
    name = resolve_alias(aliases, args.alias)
    if name is None:
        print(f"Error: Alias '{args.alias}' not found.", file=sys.stderr)
        return 1
    print(name)
    return 0


def register_alias_commands(subparsers) -> None:
    p_add = subparsers.add_parser("alias-add", help="Add or update a snapshot alias")
    p_add.add_argument("alias", help="Alias name")
    p_add.add_argument("snapshot", help="Snapshot name to point to")
    p_add.add_argument("--description", default="", help="Optional description")
    p_add.set_defaults(func=cmd_alias_add)

    p_rm = subparsers.add_parser("alias-remove", help="Remove a snapshot alias")
    p_rm.add_argument("alias", help="Alias name to remove")
    p_rm.set_defaults(func=cmd_alias_remove)

    p_ls = subparsers.add_parser("alias-list", help="List all snapshot aliases")
    p_ls.set_defaults(func=cmd_alias_list)

    p_res = subparsers.add_parser("alias-resolve", help="Resolve an alias to a snapshot name")
    p_res.add_argument("alias", help="Alias to resolve")
    p_res.set_defaults(func=cmd_alias_resolve)
