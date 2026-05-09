"""CLI commands for applying value transforms to a stored snapshot."""
from __future__ import annotations
import argparse
from envforge.cli import get_store
from envforge.transform import parse_rule, transform_snapshot_values, TransformError


def cmd_transform(args: argparse.Namespace) -> int:
    store = get_store(args)
    snap = store.get(args.name)
    if snap is None:
        print(f"Error: snapshot '{args.name}' not found.")
        return 1

    try:
        rules = [parse_rule(r) for r in args.rule]
    except TransformError as exc:
        print(f"Error parsing rule: {exc}")
        return 1

    keys = args.keys.split(",") if args.keys else None

    transformed = transform_snapshot_values(snap.variables, rules, keys=keys)

    if args.dry_run:
        changed = {k: v for k, v in transformed.items() if v != snap.variables.get(k)}
        if not changed:
            print("No values would change.")
        else:
            for k, v in changed.items():
                print(f"  {k}: {snap.variables[k]!r} -> {v!r}")
        return 0

    target = args.target or args.name
    if target == args.name:
        snap.variables = transformed
        store.save(snap)
        print(f"Snapshot '{args.name}' updated in-place ({len(transformed)} keys).")
    else:
        import copy
        new_snap = copy.deepcopy(snap)
        new_snap.name = target
        new_snap.variables = transformed
        store.save(new_snap)
        print(f"Transformed snapshot saved as '{target}'.")
    return 0


def register_transform_commands(subparsers) -> None:
    p = subparsers.add_parser(
        "transform",
        help="Apply value transformation rules to a snapshot",
    )
    p.add_argument("name", help="Source snapshot name")
    p.add_argument(
        "--rule",
        action="append",
        default=[],
        metavar="OP[:ARG1[:ARG2]]",
        help="Transform rule (repeatable). E.g. --rule upper --rule prefix:PROD_",
    )
    p.add_argument(
        "--keys",
        default="",
        help="Comma-separated list of keys to transform (default: all)",
    )
    p.add_argument(
        "--target",
        default="",
        help="Save result as a new snapshot with this name (default: overwrite source)",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without saving",
    )
    p.set_defaults(func=cmd_transform)
