"""Tests for envforge.archive module."""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import pytest

from envforge.archive import (
    ARCHIVE_VERSION,
    ArchiveError,
    ArchiveResult,
    export_archive,
    import_archive,
)
from envforge.snapshot import Snapshot


def _make_snap(name: str, vars: dict | None = None) -> Snapshot:
    return Snapshot(name=name, variables=vars or {"KEY": "val"})


# --- export_archive ---

def test_export_creates_file(tmp_path: Path) -> None:
    dest = str(tmp_path / "out.env.gz")
    result = export_archive([_make_snap("s1")], dest)
    assert Path(dest).exists()
    assert isinstance(result, ArchiveResult)
    assert result.count == 1
    assert result.path == dest


def test_export_result_str(tmp_path: Path) -> None:
    dest = str(tmp_path / "out.env.gz")
    result = export_archive([_make_snap("s1")], dest)
    assert "1" in str(result)
    assert dest in str(result)


def test_export_multiple_snapshots(tmp_path: Path) -> None:
    dest = str(tmp_path / "multi.env.gz")
    snaps = [_make_snap("a"), _make_snap("b"), _make_snap("c")]
    result = export_archive(snaps, dest)
    assert result.count == 3


def test_export_empty_list_raises() -> None:
    with pytest.raises(ArchiveError, match="No snapshots"):
        export_archive([], "/tmp/unused.gz")


def test_export_bundle_structure(tmp_path: Path) -> None:
    dest = str(tmp_path / "bundle.env.gz")
    export_archive([_make_snap("snap1", {"A": "1"})], dest)
    with gzip.open(dest, "rb") as fh:
        bundle = json.loads(fh.read().decode())
    assert bundle["version"] == ARCHIVE_VERSION
    assert len(bundle["snapshots"]) == 1
    assert bundle["snapshots"][0]["name"] == "snap1"


# --- import_archive ---

def test_import_roundtrip(tmp_path: Path) -> None:
    dest = str(tmp_path / "rt.env.gz")
    original = [_make_snap("x", {"FOO": "bar"}), _make_snap("y", {"BAZ": "qux"})]
    export_archive(original, dest)
    restored = import_archive(dest)
    assert len(restored) == 2
    names = {s.name for s in restored}
    assert names == {"x", "y"}
    foo_snap = next(s for s in restored if s.name == "x")
    assert foo_snap.variables["FOO"] == "bar"


def test_import_missing_file_raises() -> None:
    with pytest.raises(ArchiveError, match="not found"):
        import_archive("/nonexistent/path.gz")


def test_import_wrong_version_raises(tmp_path: Path) -> None:
    dest = tmp_path / "bad.gz"
    bundle = {"version": 99, "snapshots": []}
    with gzip.open(dest, "wb") as fh:
        fh.write(json.dumps(bundle).encode())
    with pytest.raises(ArchiveError, match="Unsupported archive version"):
        import_archive(str(dest))


def test_import_corrupt_file_raises(tmp_path: Path) -> None:
    dest = tmp_path / "corrupt.gz"
    dest.write_bytes(b"not gzip data")
    with pytest.raises(ArchiveError, match="Failed to read archive"):
        import_archive(str(dest))
