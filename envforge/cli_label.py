"""CLI commands for snapshot labelling."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

from envforge.snapshot_label import LabelSet, LabelError, add_label, remove_label, get_labels, filter_by_label


def _labels_path(store_path: str) -> Path:
    return Path(store_path).parent / "labels.json"


def _load_labels(store_path: str) -> List[LabelSet]:
    p = _labels_path(store_path)
    if not p.exists():
        return []
    with p.open() as f:
        return [LabelSet.from_dict(d) for d in json.load(f)]


def _save_labels(store_path: str, label_sets: List[LabelSet]) -> None:
    p = _labels_path(store_path)
    with p.open("w") as f:
        json.dump([ls.to_dict() for ls in label_sets], f, indent=2)


def cmd_label_add(args, store) -> int:
    label_sets = _load_labels(store.path)
    try:
        updated = add_label(label_sets, args.name, args.key, args.value)
    except LabelError as exc:
        print(f"Error: {exc}")
        return 1
    _save_labels(store.path, updated)
    print(f"Label '{args.key}={args.value}' added to '{args.name}'.")
    return 0


def cmd_label_remove(args, store) -> int:
    label_sets = _load_labels(store.path)
    updated = remove_label(label_sets, args.name, args.key)
    _save_labels(store.path, updated)
    print(f"Label '{args.key}' removed from '{args.name}' (if present).")
    return 0


def cmd_label_list(args, store) -> int:
    label_sets = _load_labels(store.path)
    ls = get_labels(label_sets, args.name)
    if ls is None:
        print(f"No labels for '{args.name}'.")
    else:
        print(ls.format())
    return 0


def cmd_label_filter(args, store) -> int:
    label_sets = _load_labels(store.path)
    value = getattr(args, "value", None)
    results = filter_by_label(label_sets, args.key, value)
    if not results:
        print("No snapshots match.")
    else:
        for ls in results:
            print(ls.format())
    return 0


def register_label_commands(subparsers, get_store_fn) -> None:
    p = subparsers.add_parser("label", help="Manage snapshot labels")
    sp = p.add_subparsers(dest="label_cmd")

    add_p = sp.add_parser("add", help="Add a label")
    add_p.add_argument("name"); add_p.add_argument("key"); add_p.add_argument("value")
    add_p.set_defaults(func=lambda a: cmd_label_add(a, get_store_fn(a)))

    rm_p = sp.add_parser("remove", help="Remove a label")
    rm_p.add_argument("name"); rm_p.add_argument("key")
    rm_p.set_defaults(func=lambda a: cmd_label_remove(a, get_store_fn(a)))

    ls_p = sp.add_parser("list", help="List labels for a snapshot")
    ls_p.add_argument("name")
    ls_p.set_defaults(func=lambda a: cmd_label_list(a, get_store_fn(a)))

    fi_p = sp.add_parser("filter", help="Filter snapshots by label")
    fi_p.add_argument("key"); fi_p.add_argument("value", nargs="?")
    fi_p.set_defaults(func=lambda a: cmd_label_filter(a, get_store_fn(a)))
