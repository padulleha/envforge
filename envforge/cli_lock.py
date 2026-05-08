"""CLI commands for snapshot locking."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

from envforge.lock import (
    LockedSnapshot,
    add_lock,
    remove_lock,
    is_locked,
    format_locks,
)


def _locks_path(store_path: str) -> Path:
    return Path(store_path).parent / "locks.json"


def _load_locks(store_path: str) -> List[LockedSnapshot]:
    p = _locks_path(store_path)
    if not p.exists():
        return []
    data = json.loads(p.read_text())
    return [LockedSnapshot.from_dict(d) for d in data]


def _save_locks(store_path: str, locks: List[LockedSnapshot]) -> None:
    p = _locks_path(store_path)
    p.write_text(json.dumps([lk.to_dict() for lk in locks], indent=2))


def cmd_lock_add(args: argparse.Namespace) -> int:
    locks = _load_locks(args.store)
    if is_locked(locks, args.name):
        print(f"Snapshot '{args.name}' is already locked.")
        return 1
    locks = add_lock(locks, args.name, reason=getattr(args, "reason", None))
    _save_locks(args.store, locks)
    print(f"Locked snapshot '{args.name}'.")
    return 0


def cmd_lock_remove(args: argparse.Namespace) -> int:
    locks = _load_locks(args.store)
    if not is_locked(locks, args.name):
        print(f"Snapshot '{args.name}' is not locked.")
        return 1
    locks = remove_lock(locks, args.name)
    _save_locks(args.store, locks)
    print(f"Unlocked snapshot '{args.name}'.")
    return 0


def cmd_lock_list(args: argparse.Namespace) -> int:
    locks = _load_locks(args.store)
    print(format_locks(locks))
    return 0


def register_lock_commands(
    subparsers: argparse._SubParsersAction,
) -> None:
    lock_p = subparsers.add_parser("lock", help="Lock a snapshot against modification")
    lock_p.add_argument("name")
    lock_p.add_argument("--reason", default=None, help="Optional reason for locking")
    lock_p.set_defaults(func=cmd_lock_add)

    unlock_p = subparsers.add_parser("unlock", help="Remove lock from a snapshot")
    unlock_p.add_argument("name")
    unlock_p.set_defaults(func=cmd_lock_remove)

    list_p = subparsers.add_parser("lock-list", help="List all locked snapshots")
    list_p.set_defaults(func=cmd_lock_list)
