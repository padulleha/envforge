"""CLI commands for snapshot templates."""

from __future__ import annotations

import json
import sys
from argparse import ArgumentParser, Namespace

from envforge.cli import get_store
from envforge.snapshot import Snapshot
from envforge.template import SnapshotTemplate, TemplateMissingValueError


def cmd_template_render(args: Namespace) -> None:
    """Render a template file into a named snapshot, optionally overriding vars."""
    try:
        with open(args.template_file) as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read template file: {exc}", file=sys.stderr)
        sys.exit(1)

    template = SnapshotTemplate.from_dict(data)

    overrides: dict[str, str] = {}
    for item in args.set or []:
        if "=" not in item:
            print(f"error: --set value must be KEY=VALUE, got: {item!r}", file=sys.stderr)
            sys.exit(1)
        k, v = item.split("=", 1)
        overrides[k] = v

    try:
        env_vars = template.render(overrides)
    except TemplateMissingValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    snapshot_name = args.name or template.name
    snap = Snapshot(name=snapshot_name, vars=env_vars)

    store = get_store(args)
    store.save(snap)
    print(f"Snapshot '{snapshot_name}' created from template '{template.name}' ({len(env_vars)} vars).")


def cmd_template_show(args: Namespace) -> None:
    """Display the variables defined in a template file."""
    try:
        with open(args.template_file) as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read template file: {exc}", file=sys.stderr)
        sys.exit(1)

    template = SnapshotTemplate.from_dict(data)
    print(f"Template: {template.name}")
    if template.description:
        print(f"  {template.description}")
    print(f"  {'KEY':<30} {'REQUIRED':<10} {'DEFAULT':<20} DESCRIPTION")
    for var in template.vars:
        req = "yes" if var.required else "no"
        default = var.default if var.default is not None else ""
        print(f"  {var.key:<30} {req:<10} {default:<20} {var.description}")


def register_template_commands(subparsers) -> None:
    p_render: ArgumentParser = subparsers.add_parser(
        "template-render", help="Create a snapshot from a template file"
    )
    p_render.add_argument("template_file", help="Path to JSON template file")
    p_render.add_argument("--name", help="Override snapshot name")
    p_render.add_argument("--set", metavar="KEY=VALUE", action="append", help="Override a template variable")
    p_render.set_defaults(func=cmd_template_render)

    p_show: ArgumentParser = subparsers.add_parser(
        "template-show", help="Display variables defined in a template file"
    )
    p_show.add_argument("template_file", help="Path to JSON template file")
    p_show.set_defaults(func=cmd_template_show)
