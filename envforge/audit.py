"""Audit log for envforge — tracks who applied which snapshot and when."""

from __future__ import annotations

import getpass
import platform
import socket
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class AuditEntry:
    action: str          # e.g. "apply", "capture", "delete"
    snapshot_name: str
    timestamp: str       # ISO-8601
    user: str
    hostname: str
    detail: Optional[str] = None

    def to_dict(self) -> dict:
        d = {
            "action": self.action,
            "snapshot_name": self.snapshot_name,
            "timestamp": self.timestamp,
            "user": self.user,
            "hostname": self.hostname,
        }
        if self.detail is not None:
            d["detail"] = self.detail
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "AuditEntry":
        return cls(
            action=data["action"],
            snapshot_name=data["snapshot_name"],
            timestamp=data["timestamp"],
            user=data["user"],
            hostname=data["hostname"],
            detail=data.get("detail"),
        )

    def format(self) -> str:
        detail_part = f" ({self.detail})" if self.detail else ""
        return (
            f"[{self.timestamp}] {self.action.upper()} '{self.snapshot_name}'"
            f" by {self.user}@{self.hostname}{detail_part}"
        )


@dataclass
class AuditLog:
    entries: List[AuditEntry] = field(default_factory=list)

    def record(self, action: str, snapshot_name: str, detail: Optional[str] = None) -> AuditEntry:
        entry = AuditEntry(
            action=action,
            snapshot_name=snapshot_name,
            timestamp=datetime.now(timezone.utc).isoformat(),
            user=_current_user(),
            hostname=_current_host(),
            detail=detail,
        )
        self.entries.append(entry)
        return entry

    def for_snapshot(self, name: str) -> List[AuditEntry]:
        return [e for e in self.entries if e.snapshot_name == name]

    def to_dict(self) -> dict:
        return {"entries": [e.to_dict() for e in self.entries]}

    @classmethod
    def from_dict(cls, data: dict) -> "AuditLog":
        return cls(entries=[AuditEntry.from_dict(d) for d in data.get("entries", [])])


def _current_user() -> str:
    try:
        return getpass.getuser()
    except Exception:
        return "unknown"


def _current_host() -> str:
    try:
        return socket.gethostname()
    except Exception:
        return platform.node() or "unknown"
