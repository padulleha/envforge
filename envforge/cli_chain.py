"""CLI commands for snapshot chains."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

from envforge.chain import SnapshotChain, add_chain, apply_chain, get_chain, remove_chain


def _chains_path(store_path: str) -> Path:
    return Path(store_path).parent / "chains.json"


def _load_chains(store_path: str) -> List[SnapshotChain]:
    p = _chains_path(store_path)
    if not p.exists():
        return []
    data = json.loads(p.read_text())
    return [SnapshotChain.from_dict(d) for d in data]


def _save_chains(store_path: str, chains: List[SnapshotChain]) -> None:
    p = _chains_path(store_path)
    p.write_text(json.dumps([c.to_dict() for c in chains], indent=2))


def cmd_chain_add(args: argparse.Namespace) -> int:
    from envforge.cli import get_store
    store = get_store(args)
    chains = _load_chains(store.path)
    try:
        chains = add_chain(chains, args.chain_name, args.steps, args.description or "")
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1
    _save_chains(store.path, chains)
    print(f"Chain '{args.chain_name}' saved with {len(args.steps)} step(s).")
    return 0


def cmd_chain_remove(args: argparse.Namespace) -> int:
    from envforge.cli import get_store
    store = get_store(args)
    chains = _load_chains(store.path)
    try:
        chains = remove_chain(chains, args.chain_name)
    except KeyError as exc:
        print(f"Error: {exc}")
        return 1
    _save_chains(store.path, chains)
    print(f"Chain '{args.chain_name}' removed.")
    return 0


def cmd_chain_list(args: argparse.Namespace) -> int:
    from envforge.cli import get_store
    store = get_store(args)
    chains = _load_chains(store.path)
    if not chains:
        print("No chains defined.")
        return 0
    for c in chains:
        print(c.format())
        print()
    return 0


def cmd_chain_apply(args: argparse.Namespace) -> int:
    from envforge.cli import get_store
    store = get_store(args)
    chains = _load_chains(store.path)
    chain = get_chain(chains, args.chain_name)
    if chain is None:
        print(f"Error: Chain '{args.chain_name}' not found.")
        return 1
    try:
        applied = apply_chain(chain, store, overwrite=not args.no_overwrite)
    except KeyError as exc:
        print(f"Error: {exc}")
        return 1
    print(f"Applied {len(applied)} snapshot(s): {', '.join(applied)}")
    return 0


def register_chain_commands(subparsers: argparse._SubParsersAction) -> None:
    p_add = subparsers.add_parser("chain-add", help="Define a snapshot chain")
    p_add.add_argument("chain_name")
    p_add.add_argument("steps", nargs="+")
    p_add.add_argument("--description", default="")
    p_add.set_defaults(func=cmd_chain_add)

    p_rm = subparsers.add_parser("chain-remove", help="Remove a snapshot chain")
    p_rm.add_argument("chain_name")
    p_rm.set_defaults(func=cmd_chain_remove)

    p_ls = subparsers.add_parser("chain-list", help="List snapshot chains")
    p_ls.set_defaults(func=cmd_chain_list)

    p_ap = subparsers.add_parser("chain-apply", help="Apply a snapshot chain")
    p_ap.add_argument("chain_name")
    p_ap.add_argument("--no-overwrite", action="store_true")
    p_ap.set_defaults(func=cmd_chain_apply)
