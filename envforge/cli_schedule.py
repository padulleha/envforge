"""CLI commands for managing snapshot schedule rules."""
from __future__ import annotations

import os
from argparse import ArgumentParser, Namespace
from datetime import datetime

from envforge.cli import get_store
from envforge.schedule import ScheduleRule, ScheduleStore
from envforge.snapshot import Snapshot


def _get_schedule_store(args: Namespace) -> ScheduleStore:
    store_path = getattr(args, "store", None) or os.path.expanduser("~/.envforge/store.json")
    schedule_path = store_path.replace(".json", "_schedule.json")
    return ScheduleStore(schedule_path)


def cmd_schedule_add(args: Namespace) -> None:
    """Add or update a schedule rule."""
    rule = ScheduleRule(
        name=args.name,
        keys=args.keys or [],
        interval_minutes=args.interval,
        tags=args.tags or [],
    )
    ss = _get_schedule_store(args)
    ss.add(rule)
    print(f"Schedule rule '{args.name}' saved (interval={args.interval}m).")


def cmd_schedule_remove(args: Namespace) -> None:
    """Remove a schedule rule by name."""
    ss = _get_schedule_store(args)
    if ss.remove(args.name):
        print(f"Schedule rule '{args.name}' removed.")
    else:
        print(f"No schedule rule named '{args.name}'.")


def cmd_schedule_list(args: Namespace) -> None:
    """List all schedule rules."""
    ss = _get_schedule_store(args)
    if not ss.rules:
        print("No schedule rules defined.")
        return
    for rule in ss.rules:
        due = "[DUE]" if rule.is_due() else ""
        tags = f" tags={rule.tags}" if rule.tags else ""
        keys = f" keys={rule.keys}" if rule.keys else " keys=ALL"
        print(f"  {rule.name}  interval={rule.interval_minutes}m  last_run={rule.last_run}{keys}{tags} {due}")


def cmd_schedule_run(args: Namespace) -> None:
    """Execute all due schedule rules, capturing snapshots."""
    ss = _get_schedule_store(args)
    store = get_store(args)
    now = datetime.utcnow()
    due = ss.due_rules(now)
    if not due:
        print("No rules are due.")
        return
    for rule in due:
        snap = Snapshot.capture(name=rule.name, keys=rule.keys or None)
        for tag in rule.tags:
            from envforge.tags import add_tag
            snap.tags = add_tag(snap.tags, tag)
        store.save(snap)
        rule.mark_run(now)
        ss._save()
        print(f"Captured snapshot '{rule.name}' ({len(snap.variables)} vars).")


def register_schedule_commands(subparsers) -> None:
    p_add = subparsers.add_parser("schedule-add", help="Add a schedule rule")
    p_add.add_argument("name")
    p_add.add_argument("--interval", type=int, default=60, help="Minutes between captures")
    p_add.add_argument("--keys", nargs="*", help="Env var keys to capture (default: all)")
    p_add.add_argument("--tags", nargs="*", help="Tags to apply to captured snapshot")
    p_add.set_defaults(func=cmd_schedule_add)

    p_rm = subparsers.add_parser("schedule-remove", help="Remove a schedule rule")
    p_rm.add_argument("name")
    p_rm.set_defaults(func=cmd_schedule_remove)

    p_ls = subparsers.add_parser("schedule-list", help="List schedule rules")
    p_ls.set_defaults(func=cmd_schedule_list)

    p_run = subparsers.add_parser("schedule-run", help="Run all due schedule rules")
    p_run.set_defaults(func=cmd_schedule_run)
