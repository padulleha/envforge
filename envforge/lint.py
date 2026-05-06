"""Lint snapshots for common issues and best practices."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envforge.snapshot import Snapshot

# Keys that are generally risky to snapshot
_SENSITIVE_PATTERNS = (
    "SECRET",
    "PASSWORD",
    "PASSWD",
    "TOKEN",
    "API_KEY",
    "PRIVATE_KEY",
    "CREDENTIALS",
    "AUTH",
)

_EMPTY_VALUE_SEVERITY = "warning"
_SENSITIVE_SEVERITY = "warning"
_LARGE_VALUE_THRESHOLD = 512  # characters
_LARGE_VALUE_SEVERITY = "info"


@dataclass
class LintIssue:
    severity: str  # 'error' | 'warning' | 'info'
    key: str
    message: str

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.key}: {self.message}"


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(i.severity == "error" for i in self.issues)

    @property
    def has_warnings(self) -> bool:
        return any(i.severity == "warning" for i in self.issues)

    def summary(self) -> str:
        errors = sum(1 for i in self.issues if i.severity == "error")
        warnings = sum(1 for i in self.issues if i.severity == "warning")
        infos = sum(1 for i in self.issues if i.severity == "info")
        parts = []
        if errors:
            parts.append(f"{errors} error(s)")
        if warnings:
            parts.append(f"{warnings} warning(s)")
        if infos:
            parts.append(f"{infos} info(s)")
        return ", ".join(parts) if parts else "No issues found."


def lint_snapshot(snapshot: Snapshot) -> LintResult:
    """Run all lint checks on a snapshot and return a LintResult."""
    result = LintResult()

    if not snapshot.variables:
        result.issues.append(
            LintIssue("warning", "(snapshot)", "Snapshot contains no variables.")
        )
        return result

    for key, value in snapshot.variables.items():
        # Check for empty values
        if value == "":
            result.issues.append(
                LintIssue(_EMPTY_VALUE_SEVERITY, key, "Variable has an empty value.")
            )

        # Check for sensitive-looking keys
        upper_key = key.upper()
        for pattern in _SENSITIVE_PATTERNS:
            if pattern in upper_key:
                result.issues.append(
                    LintIssue(
                        _SENSITIVE_SEVERITY,
                        key,
                        f"Key name suggests sensitive data (matched pattern '{pattern}'). "
                        "Consider encrypting this snapshot.",
                    )
                )
                break

        # Check for unusually large values
        if len(value) > _LARGE_VALUE_THRESHOLD:
            result.issues.append(
                LintIssue(
                    _LARGE_VALUE_SEVERITY,
                    key,
                    f"Value is large ({len(value)} chars); consider whether this belongs in env.",
                )
            )

    return result
