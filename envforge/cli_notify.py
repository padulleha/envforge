"""CLI commands for managing notification rules."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

from envforge.notify import NotificationRule


def _rules_path(store_path: str) -> Path:
    return Path(store_path).parent / "notifications.json"


def _load_rules(store_path: str) -> List[NotificationRule]:
    p = _rules_path(store_path)
    if not p.exists():
        return []
    data = json.loads(p.read_text())
    return [NotificationRule.from_dict(r) for r in data]


def _save_rules(store_path: str, rules: List[NotificationRule]) -> None:
    p = _rules_path(store_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps([r.to_dict() for r in rules], indent=2))


def cmd_notify_add(args) -> int:
    rules = _load_rules(args.store)
    rule = NotificationRule(
        event=args.event,
        handler=args.handler,
        snapshot_filter=getattr(args, "filter", None),
        detail=getattr(args, "detail", "") or "",
    )
    rules.append(rule)
    _save_rules(args.store, rules)
    print(f"Notification rule added: {args.event} -> {args.handler}")
    return 0


def cmd_notify_remove(args) -> int:
    rules = _load_rules(args.store)
    before = len(rules)
    rules = [r for r in rules if not (r.event == args.event and r.handler == args.handler)]
    if len(rules) == before:
        print(f"No matching rule found for event={args.event} handler={args.handler}")
        return 1
    _save_rules(args.store, rules)
    print(f"Removed {before - len(rules)} rule(s).")
    return 0


def cmd_notify_list(args) -> int:
    rules = _load_rules(args.store)
    if not rules:
        print("No notification rules defined.")
        return 0
    for i, r in enumerate(rules):
        filt = r.snapshot_filter or "*"
        detail = f" [{r.detail}]" if r.detail else ""
        print(f"  {i+1}. event={r.event}  handler={r.handler}  filter={filt}{detail}")
    return 0


def register_notify_commands(subparsers, parent_parser) -> None:
    p = subparsers.add_parser("notify", help="Manage notification rules")
    sub = p.add_subparsers(dest="notify_cmd")

    add_p = sub.add_parser("add", parents=[parent_parser], help="Add a notification rule")
    add_p.add_argument("event", help="Event name (capture, apply, delete, ...)")
    add_p.add_argument("handler", help="Handler name (e.g. shell)")
    add_p.add_argument("--filter", default=None, help="Snapshot name glob filter")
    add_p.add_argument("--detail", default="", help="Handler detail (e.g. shell command)")
    add_p.set_defaults(func=cmd_notify_add)

    rm_p = sub.add_parser("remove", parents=[parent_parser], help="Remove notification rules")
    rm_p.add_argument("event", help="Event name")
    rm_p.add_argument("handler", help="Handler name")
    rm_p.set_defaults(func=cmd_notify_remove)

    ls_p = sub.add_parser("list", parents=[parent_parser], help="List notification rules")
    ls_p.set_defaults(func=cmd_notify_list)
