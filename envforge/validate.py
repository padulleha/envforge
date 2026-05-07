"""Validate snapshot variable keys and values against configurable rules."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from envforge.snapshot import Snapshot

# Regex for a valid POSIX environment variable name
_VALID_KEY_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
_MAX_VALUE_LENGTH = 32_768  # 32 KiB – same limit as many shells


@dataclass
class ValidationIssue:
    key: str
    message: str
    severity: str = "error"  # "error" | "warning"

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.key}: {self.message}"


@dataclass
class ValidationResult:
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not any(i.severity == "error" for i in self.issues)

    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    def summary(self) -> str:
        if not self.issues:
            return "All variables are valid."
        e, w = len(self.errors), len(self.warnings)
        parts = []
        if e:
            parts.append(f"{e} error(s)")
        if w:
            parts.append(f"{w} warning(s)")
        return ", ".join(parts) + "."

    def format_text(self) -> str:
        if not self.issues:
            return self.summary()
        lines = [self.summary()]
        for issue in self.issues:
            lines.append(f"  {issue}")
        return "\n".join(lines)


def validate_snapshot(
    snapshot: Snapshot,
    max_value_length: int = _MAX_VALUE_LENGTH,
    forbidden_prefixes: Optional[List[str]] = None,
) -> ValidationResult:
    """Run validation rules against every key/value in *snapshot*."""
    result = ValidationResult()
    forbidden_prefixes = forbidden_prefixes or []

    if not snapshot.variables:
        result.issues.append(
            ValidationIssue("<snapshot>", "Snapshot contains no variables.", "warning")
        )
        return result

    for key, value in snapshot.variables.items():
        if not _VALID_KEY_RE.match(key):
            result.issues.append(
                ValidationIssue(key, f"Key '{key}' is not a valid POSIX variable name.")
            )

        if len(value) > max_value_length:
            result.issues.append(
                ValidationIssue(
                    key,
                    f"Value exceeds maximum length of {max_value_length} characters.",
                    "warning",
                )
            )

        for prefix in forbidden_prefixes:
            if key.startswith(prefix):
                result.issues.append(
                    ValidationIssue(
                        key,
                        f"Key starts with forbidden prefix '{prefix}'.",
                    )
                )
                break

    return result
