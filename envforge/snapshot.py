"""Core snapshot module for capturing and restoring environment variable sets."""

import os
import json
import datetime
from typing import Optional


class Snapshot:
    """Represents a named snapshot of environment variables."""

    def __init__(self, name: str, variables: dict, description: str = "", created_at: Optional[str] = None):
        self.name = name
        self.variables = variables
        self.description = description
        self.created_at = created_at or datetime.datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        """Serialize snapshot to a dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at,
            "variables": self.variables,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Snapshot":
        """Deserialize snapshot from a dictionary."""
        return cls(
            name=data["name"],
            variables=data["variables"],
            description=data.get("description", ""),
            created_at=data.get("created_at"),
        )

    @classmethod
    def capture(cls, name: str, keys: Optional[list] = None, description: str = "") -> "Snapshot":
        """Capture current environment variables into a snapshot.

        Args:
            name: Snapshot name.
            keys: Optional list of specific env var keys to capture. Captures all if None.
            description: Optional description for the snapshot.
        """
        if keys is not None:
            variables = {k: os.environ[k] for k in keys if k in os.environ}
        else:
            variables = dict(os.environ)
        return cls(name=name, variables=variables, description=description)

    def apply(self, overwrite: bool = True) -> None:
        """Apply snapshot variables to the current process environment.

        Args:
            overwrite: If True, overwrite existing env vars. If False, skip existing keys.
        """
        for key, value in self.variables.items():
            if overwrite or key not in os.environ:
                os.environ[key] = value

    def diff(self, other: "Snapshot") -> dict:
        """Return the difference between this snapshot and another.

        Returns a dict with 'added', 'removed', and 'changed' keys.
        """
        added = {k: other.variables[k] for k in other.variables if k not in self.variables}
        removed = {k: self.variables[k] for k in self.variables if k not in other.variables}
        changed = {
            k: {"from": self.variables[k], "to": other.variables[k]}
            for k in self.variables
            if k in other.variables and self.variables[k] != other.variables[k]
        }
        return {"added": added, "removed": removed, "changed": changed}

    def __repr__(self) -> str:
        return f"Snapshot(name={self.name!r}, vars={len(self.variables)}, created_at={self.created_at!r})"
