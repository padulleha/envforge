"""Snapshot expiration: mark snapshots with a TTL and check if they have expired."""

from __future__ import annotations

import dataclasses
from datetime import datetime, timezone
from typing import Dict, List, Optional

DATE_FMT = "%Y-%m-%dT%H:%M:%SZ"


@dataclasses.dataclass
class ExpiryRecord:
    name: str
    expires_at: datetime
    reason: str = ""

    def is_expired(self, now: Optional[datetime] = None) -> bool:
        now = now or datetime.now(timezone.utc)
        return now >= self.expires_at

    def format(self) -> str:
        status = "EXPIRED" if self.is_expired() else "active"
        ts = self.expires_at.strftime(DATE_FMT)
        reason_part = f" ({self.reason})" if self.reason else ""
        return f"{self.name}: expires {ts}{reason_part} [{status}]"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "expires_at": self.expires_at.strftime(DATE_FMT),
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ExpiryRecord":
        return cls(
            name=data["name"],
            expires_at=datetime.strptime(data["expires_at"], DATE_FMT).replace(
                tzinfo=timezone.utc
            ),
            reason=data.get("reason", ""),
        )


def add_expiry(
    records: List[ExpiryRecord],
    name: str,
    expires_at: datetime,
    reason: str = "",
) -> List[ExpiryRecord]:
    """Add or update an expiry record for a snapshot."""
    updated = [r for r in records if r.name != name]
    updated.append(ExpiryRecord(name=name, expires_at=expires_at, reason=reason))
    return sorted(updated, key=lambda r: r.name)


def remove_expiry(records: List[ExpiryRecord], name: str) -> List[ExpiryRecord]:
    """Remove the expiry record for a snapshot."""
    return [r for r in records if r.name != name]


def get_expired(
    records: List[ExpiryRecord],
    now: Optional[datetime] = None,
) -> List[ExpiryRecord]:
    """Return all records that have passed their expiry time."""
    return [r for r in records if r.is_expired(now)]


def records_to_dict(records: List[ExpiryRecord]) -> List[dict]:
    return [r.to_dict() for r in records]


def records_from_dict(data: List[dict]) -> List[ExpiryRecord]:
    return [ExpiryRecord.from_dict(d) for d in data]
