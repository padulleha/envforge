"""Notification hooks for snapshot events."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

# Registry of named notification handlers
_HANDLERS: Dict[str, Callable[[str, str, Optional[str]], None]] = {}


def register_handler(name: str, fn: Callable[[str, str, Optional[str]], None]) -> None:
    """Register a notification handler by name."""
    _HANDLERS[name] = fn


def get_handler(name: str) -> Optional[Callable[[str, str, Optional[str]], None]]:
    return _HANDLERS.get(name)


@dataclass
class NotificationRule:
    """A rule that triggers a notification on a specific event."""
    event: str          # e.g. 'capture', 'apply', 'delete'
    handler: str        # name of registered handler
    snapshot_filter: Optional[str] = None  # glob pattern or None for all
    detail: str = ""

    def to_dict(self) -> dict:
        return {
            "event": self.event,
            "handler": self.handler,
            "snapshot_filter": self.snapshot_filter,
            "detail": self.detail,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NotificationRule":
        return cls(
            event=data["event"],
            handler=data["handler"],
            snapshot_filter=data.get("snapshot_filter"),
            detail=data.get("detail", ""),
        )

    def matches(self, event: str, snapshot_name: str) -> bool:
        import fnmatch
        if self.event != event:
            return False
        if self.snapshot_filter is None:
            return True
        return fnmatch.fnmatch(snapshot_name, self.snapshot_filter)


def dispatch(rules: List[NotificationRule], event: str, snapshot_name: str) -> List[str]:
    """Dispatch notifications for matching rules. Returns list of handler names invoked."""
    invoked = []
    for rule in rules:
        if rule.matches(event, snapshot_name):
            fn = get_handler(rule.handler)
            if fn is not None:
                fn(event, snapshot_name, rule.detail or None)
                invoked.append(rule.handler)
    return invoked


def shell_notify_handler(event: str, snapshot_name: str, detail: Optional[str]) -> None:
    """Built-in handler: run a shell command stored in detail."""
    if not detail:
        return
    cmd = detail.format(event=event, snapshot=snapshot_name)
    subprocess.run(cmd, shell=True, check=False)


# Register built-in handlers
register_handler("shell", shell_notify_handler)
