"""Scheduled snapshot capture: define recurring capture rules for snapshots."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class ScheduleRule:
    """A rule describing when and how to auto-capture a snapshot."""

    name: str
    keys: List[str] = field(default_factory=list)  # empty = all env vars
    interval_minutes: int = 60
    last_run: Optional[str] = None  # ISO-8601 string
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "keys": self.keys,
            "interval_minutes": self.interval_minutes,
            "last_run": self.last_run,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ScheduleRule":
        return cls(
            name=data["name"],
            keys=data.get("keys", []),
            interval_minutes=data.get("interval_minutes", 60),
            last_run=data.get("last_run"),
            tags=data.get("tags", []),
        )

    def is_due(self, now: Optional[datetime] = None) -> bool:
        """Return True if the rule has never run or interval has elapsed."""
        if self.last_run is None:
            return True
        now = now or datetime.utcnow()
        last = datetime.fromisoformat(self.last_run)
        elapsed = (now - last).total_seconds() / 60
        return elapsed >= self.interval_minutes

    def mark_run(self, now: Optional[datetime] = None) -> None:
        self.last_run = (now or datetime.utcnow()).isoformat()


class ScheduleStore:
    """Persist schedule rules to a JSON file."""

    def __init__(self, path: str) -> None:
        self.path = path
        self.rules: List[ScheduleRule] = []
        self._load()

    def _load(self) -> None:
        try:
            with open(self.path, "r") as fh:
                data = json.load(fh)
            self.rules = [ScheduleRule.from_dict(r) for r in data.get("rules", [])]
        except FileNotFoundError:
            self.rules = []

    def _save(self) -> None:
        with open(self.path, "w") as fh:
            json.dump({"rules": [r.to_dict() for r in self.rules]}, fh, indent=2)

    def add(self, rule: ScheduleRule) -> None:
        self.rules = [r for r in self.rules if r.name != rule.name]
        self.rules.append(rule)
        self._save()

    def remove(self, name: str) -> bool:
        before = len(self.rules)
        self.rules = [r for r in self.rules if r.name != name]
        if len(self.rules) < before:
            self._save()
            return True
        return False

    def get(self, name: str) -> Optional[ScheduleRule]:
        return next((r for r in self.rules if r.name == name), None)

    def due_rules(self, now: Optional[datetime] = None) -> List[ScheduleRule]:
        return [r for r in self.rules if r.is_due(now)]
