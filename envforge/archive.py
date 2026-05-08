"""Archive and restore snapshots to/from compressed bundle files."""

from __future__ import annotations

import gzip
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

from envforge.snapshot import Snapshot

ARCHIVE_VERSION = 1


class ArchiveError(Exception):
    pass


@dataclass
class ArchiveResult:
    path: str
    count: int

    def __str__(self) -> str:
        return f"Archived {self.count} snapshot(s) to {self.path}"


def export_archive(snapshots: List[Snapshot], dest: str) -> ArchiveResult:
    """Write a list of snapshots to a gzipped JSON bundle."""
    if not snapshots:
        raise ArchiveError("No snapshots provided for archiving.")

    bundle = {
        "version": ARCHIVE_VERSION,
        "snapshots": [s.to_dict() for s in snapshots],
    }
    dest_path = Path(dest)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(bundle, indent=2).encode("utf-8")
    with gzip.open(dest_path, "wb") as fh:
        fh.write(raw)
    return ArchiveResult(path=str(dest_path), count=len(snapshots))


def import_archive(src: str) -> List[Snapshot]:
    """Read snapshots from a gzipped JSON bundle."""
    src_path = Path(src)
    if not src_path.exists():
        raise ArchiveError(f"Archive file not found: {src}")
    try:
        with gzip.open(src_path, "rb") as fh:
            raw = fh.read()
        bundle = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise ArchiveError(f"Failed to read archive: {exc}") from exc

    version = bundle.get("version")
    if version != ARCHIVE_VERSION:
        raise ArchiveError(f"Unsupported archive version: {version}")

    snapshots_data = bundle.get("snapshots", [])
    return [Snapshot.from_dict(d) for d in snapshots_data]
