"""CLI commands for snapshot bookmarks."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

from envforge.snapshot_bookmark import (
    Bookmark,
    BookmarkError,
    add_bookmark,
    get_bookmark,
    list_bookmarks_for,
    remove_bookmark,
)


def _bookmarks_path(store_path: str) -> Path:
    return Path(store_path).parent / "bookmarks.json"


def _load_bookmarks(store_path: str) -> List[Bookmark]:
    p = _bookmarks_path(store_path)
    if not p.exists():
        return []
    data = json.loads(p.read_text())
    return [Bookmark.from_dict(d) for d in data]


def _save_bookmarks(store_path: str, bookmarks: List[Bookmark]) -> None:
    p = _bookmarks_path(store_path)
    p.write_text(json.dumps([b.to_dict() for b in bookmarks], indent=2))


def cmd_bookmark_add(args, store) -> int:
    snap = store.get(args.snapshot)
    if snap is None:
        print(f"Error: snapshot '{args.snapshot}' not found.")
        return 1
    keys = args.keys if args.keys else list(snap.variables.keys())
    bookmarks = _load_bookmarks(args.store)
    try:
        bookmarks = add_bookmark(
            bookmarks,
            name=args.name,
            snapshot_name=args.snapshot,
            keys=keys,
            description=getattr(args, "description", ""),
        )
    except BookmarkError as exc:
        print(f"Error: {exc}")
        return 1
    _save_bookmarks(args.store, bookmarks)
    print(f"Bookmark '{args.name}' saved ({len(keys)} keys).")
    return 0


def cmd_bookmark_remove(args, store) -> int:
    bookmarks = _load_bookmarks(args.store)
    try:
        bookmarks = remove_bookmark(bookmarks, args.name)
    except BookmarkError as exc:
        print(f"Error: {exc}")
        return 1
    _save_bookmarks(args.store, bookmarks)
    print(f"Bookmark '{args.name}' removed.")
    return 0


def cmd_bookmark_show(args, store) -> int:
    bookmarks = _load_bookmarks(args.store)
    bm = get_bookmark(bookmarks, args.name)
    if bm is None:
        print(f"Error: bookmark '{args.name}' not found.")
        return 1
    print(bm.format())
    return 0


def cmd_bookmark_list(args, store) -> int:
    bookmarks = _load_bookmarks(args.store)
    if hasattr(args, "snapshot") and args.snapshot:
        bookmarks = list_bookmarks_for(bookmarks, args.snapshot)
    if not bookmarks:
        print("No bookmarks found.")
        return 0
    for bm in bookmarks:
        desc = f" — {bm.description}" if bm.description else ""
        print(f"  {bm.name} -> {bm.snapshot_name} ({len(bm.keys)} keys){desc}")
    return 0


def register_bookmark_commands(subparsers, parent_parser):
    p = subparsers.add_parser("bookmark", help="Manage snapshot bookmarks")
    sub = p.add_subparsers(dest="bookmark_cmd")

    add_p = sub.add_parser("add", parents=[parent_parser])
    add_p.add_argument("name")
    add_p.add_argument("snapshot")
    add_p.add_argument("--keys", nargs="+")
    add_p.add_argument("--description", default="")
    add_p.set_defaults(func=cmd_bookmark_add)

    rm_p = sub.add_parser("remove", parents=[parent_parser])
    rm_p.add_argument("name")
    rm_p.set_defaults(func=cmd_bookmark_remove)

    show_p = sub.add_parser("show", parents=[parent_parser])
    show_p.add_argument("name")
    show_p.set_defaults(func=cmd_bookmark_show)

    ls_p = sub.add_parser("list", parents=[parent_parser])
    ls_p.add_argument("--snapshot", default=None)
    ls_p.set_defaults(func=cmd_bookmark_list)
