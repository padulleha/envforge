"""Score snapshots based on configurable quality metrics."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envforge.snapshot import Snapshot


@dataclass
class ScoreBreakdown:
    key_count: int = 0
    non_empty_ratio: float = 0.0
    has_description: bool = False
    has_tags: bool = False
    unique_prefix_count: int = 0

    def to_dict(self) -> dict:
        return {
            "key_count": self.key_count,
            "non_empty_ratio": round(self.non_empty_ratio, 4),
            "has_description": self.has_description,
            "has_tags": self.has_tags,
            "unique_prefix_count": self.unique_prefix_count,
        }


@dataclass
class SnapshotScore:
    name: str
    score: float
    breakdown: ScoreBreakdown = field(default_factory=ScoreBreakdown)

    def summary(self) -> str:
        grade = _grade(self.score)
        return f"{self.name}: {self.score:.1f}/100 ({grade})"

    def format_text(self) -> str:
        b = self.breakdown
        lines = [
            self.summary(),
            f"  Keys          : {b.key_count}",
            f"  Non-empty     : {b.non_empty_ratio * 100:.0f}%",
            f"  Has description: {'yes' if b.has_description else 'no'}",
            f"  Has tags       : {'yes' if b.has_tags else 'no'}",
            f"  Unique prefixes: {b.unique_prefix_count}",
        ]
        return "\n".join(lines)


def _grade(score: float) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 55:
        return "C"
    if score >= 35:
        return "D"
    return "F"


def _unique_prefixes(keys: List[str]) -> int:
    prefixes = set()
    for k in keys:
        parts = k.split("_")
        if parts:
            prefixes.add(parts[0].upper())
    return len(prefixes)


def score_snapshot(snapshot: Snapshot) -> SnapshotScore:
    """Compute a quality score (0-100) for a snapshot."""
    env = snapshot.variables
    keys = list(env.keys())
    total = len(keys)

    breakdown = ScoreBreakdown()
    breakdown.key_count = total

    if total == 0:
        return SnapshotScore(name=snapshot.name, score=0.0, breakdown=breakdown)

    non_empty = sum(1 for v in env.values() if v.strip())
    breakdown.non_empty_ratio = non_empty / total

    breakdown.has_description = bool(getattr(snapshot, "description", None))
    breakdown.has_tags = bool(getattr(snapshot, "tags", None))
    breakdown.unique_prefix_count = _unique_prefixes(keys)

    score = 0.0
    # Key count: up to 25 pts (saturates at 20 keys)
    score += min(total / 20, 1.0) * 25
    # Non-empty ratio: up to 30 pts
    score += breakdown.non_empty_ratio * 30
    # Description: 15 pts
    score += 15 if breakdown.has_description else 0
    # Tags: 10 pts
    score += 10 if breakdown.has_tags else 0
    # Prefix diversity: up to 20 pts (saturates at 5 prefixes)
    score += min(breakdown.unique_prefix_count / 5, 1.0) * 20

    return SnapshotScore(name=snapshot.name, score=round(score, 2), breakdown=breakdown)
