"""Template support: create snapshots from variable templates with defaults and required keys."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class TemplateMissingValueError(Exception):
    """Raised when a required template variable has no value."""

    def __init__(self, missing: List[str]):
        self.missing = missing
        super().__init__(f"Missing required template variables: {', '.join(missing)}")


@dataclass
class TemplateVar:
    key: str
    description: str = ""
    default: Optional[str] = None
    required: bool = True

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "description": self.description,
            "default": self.default,
            "required": self.required,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TemplateVar":
        return cls(
            key=data["key"],
            description=data.get("description", ""),
            default=data.get("default"),
            required=data.get("required", True),
        )


@dataclass
class SnapshotTemplate:
    name: str
    vars: List[TemplateVar] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "vars": [v.to_dict() for v in self.vars],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SnapshotTemplate":
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            vars=[TemplateVar.from_dict(v) for v in data.get("vars", [])],
        )

    def render(self, overrides: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Resolve template vars using overrides, then defaults. Raise on missing required."""
        overrides = overrides or {}
        result: Dict[str, str] = {}
        missing: List[str] = []

        for var in self.vars:
            if var.key in overrides:
                result[var.key] = overrides[var.key]
            elif var.default is not None:
                result[var.key] = var.default
            elif var.required:
                missing.append(var.key)
            # optional with no default: skip

        if missing:
            raise TemplateMissingValueError(missing)

        return result
