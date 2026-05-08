"""CLI commands for snapshot promotion across environment tiers."""
from __future__ import annotations

import argparse
import sys

from envforge.promote import DEFAULT_TIERS, PromoteError, promote_snapshot


def cmd_promote(args: argparse.Namespace, store) -> int:
    """Promote a snapshot to the next environment tier."""
    tiers = [t.strip() for t in args.tiers.split(",")] if args.tiers else DEFAULT_TIERS

    try:
        result = promote_snapshot(
            store,
            source_name=args.name,
            tier_from=args.from_tier,
            dest_name=args.dest or None,
            tiers=tiers,
            overwrite=args.overwrite,
        )
    except PromoteError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(result)
    return 0


def register_promote_commands(
    subparsers: argparse._SubParsersAction,
    store_factory,
) -> None:
    """Attach the ``promote`` sub-command to *subparsers*."""
    p = subparsers.add_parser(
        "promote",
        help="Promote a snapshot to the next environment tier.",
    )
    p.add_argument("name", help="Name of the snapshot to promote.")
    p.add_argument(
        "from_tier",
        metavar="FROM_TIER",
        help="Current tier of the snapshot (e.g. dev, staging).",
    )
    p.add_argument(
        "--dest",
        default=None,
        help="Explicit destination snapshot name (auto-generated if omitted).",
    )
    p.add_argument(
        "--tiers",
        default=None,
        help=(
            "Comma-separated ordered tier list "
            f"(default: {','.join(DEFAULT_TIERS)})."
        ),
    )
    p.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite destination snapshot if it already exists.",
    )

    def _run(a: argparse.Namespace) -> None:
        store = store_factory(a)
        sys.exit(cmd_promote(a, store))

    p.set_defaults(func=_run)
