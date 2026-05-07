"""Import and export snapshots to/from portable file formats (JSON, dotenv)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from envforge.snapshot import Snapshot


class UnsupportedFormatError(Exception):
    pass


def export_snapshot(snapshot: Snapshot, path: str, fmt: Optional[str] = None) -> str:
    """Write a snapshot to *path* in the requested format.

    Format is inferred from the file extension when *fmt* is None.
    Supported formats: ``json``, ``dotenv`` / ``env``.

    Returns the resolved absolute path.
    """
    resolved = Path(path).expanduser().resolve()
    if fmt is None:
        fmt = resolved.suffix.lstrip(".").lower()
        if fmt in ("", "env"):
            fmt = "dotenv"

    if fmt == "json":
        data = snapshot.to_dict()
        resolved.write_text(json.dumps(data, indent=2), encoding="utf-8")
    elif fmt == "dotenv":
        lines = []
        for key, value in sorted(snapshot.variables.items()):
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            lines.append(f'{key}="{escaped}"')
        resolved.write_text("\n".join(lines) + "\n", encoding="utf-8")
    else:
        raise UnsupportedFormatError(f"Unknown export format: {fmt!r}")

    return str(resolved)


def import_snapshot(
    path: str,
    name: str,
    fmt: Optional[str] = None,
    description: str = "",
) -> Snapshot:
    """Read a snapshot from *path* and return a :class:`Snapshot`.

    Format is inferred from the file extension when *fmt* is None.
    """
    resolved = Path(path).expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"File not found: {resolved}")

    if fmt is None:
        suffix = resolved.suffix.lstrip(".").lower()
        fmt = "dotenv" if suffix in ("", "env") else suffix

    if fmt == "json":
        data = json.loads(resolved.read_text(encoding="utf-8"))
        snap = Snapshot.from_dict(data)
        snap.name = name
        if description:
            snap.description = description
        return snap
    elif fmt == "dotenv":
        variables: dict[str, str] = {}
        for raw_line in resolved.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, raw_value = line.partition("=")
            key = key.strip()
            value = raw_value.strip().strip('"').replace('\\"', '"').replace("\\\\", "\\")
            if key:
                variables[key] = value
        return Snapshot.capture(name=name, keys=list(variables.keys()) or None,
                                description=description, _env=variables)
    else:
        raise UnsupportedFormatError(f"Unknown import format: {fmt!r}")
