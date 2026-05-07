"""Tests for envforge.import_export_file and related CLI commands."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from envforge.import_export_file import (
    UnsupportedFormatError,
    export_snapshot,
    import_snapshot,
)
from envforge.snapshot import Snapshot


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_snap(name: str = "test", variables: dict | None = None) -> Snapshot:
    env = variables or {"FOO": "bar", "NUM": "42"}
    return Snapshot.capture(name=name, keys=list(env.keys()), _env=env)


# ---------------------------------------------------------------------------
# export_snapshot — JSON
# ---------------------------------------------------------------------------

def test_export_json_creates_file(tmp_path: Path) -> None:
    snap = _make_snap()
    dest = str(tmp_path / "snap.json")
    out = export_snapshot(snap, dest)
    assert Path(out).exists()


def test_export_json_content_is_valid(tmp_path: Path) -> None:
    snap = _make_snap()
    dest = str(tmp_path / "snap.json")
    export_snapshot(snap, dest)
    data = json.loads(Path(dest).read_text())
    assert data["name"] == "test"
    assert data["variables"]["FOO"] == "bar"


def test_export_dotenv_creates_file(tmp_path: Path) -> None:
    snap = _make_snap()
    dest = str(tmp_path / "snap.env")
    export_snapshot(snap, dest)
    assert Path(dest).exists()


def test_export_dotenv_content_format(tmp_path: Path) -> None:
    snap = _make_snap(variables={"MY_VAR": "hello world"})
    dest = str(tmp_path / "snap.env")
    export_snapshot(snap, dest)
    content = Path(dest).read_text()
    assert 'MY_VAR="hello world"' in content


def test_export_unknown_format_raises(tmp_path: Path) -> None:
    snap = _make_snap()
    with pytest.raises(UnsupportedFormatError):
        export_snapshot(snap, str(tmp_path / "snap.xyz"), fmt="xyz")


# ---------------------------------------------------------------------------
# import_snapshot — JSON
# ---------------------------------------------------------------------------

def test_import_json_roundtrip(tmp_path: Path) -> None:
    snap = _make_snap(name="mysnap", variables={"A": "1", "B": "2"})
    dest = str(tmp_path / "snap.json")
    export_snapshot(snap, dest)
    loaded = import_snapshot(dest, name="mysnap")
    assert loaded.name == "mysnap"
    assert loaded.variables["A"] == "1"
    assert loaded.variables["B"] == "2"


def test_import_dotenv_roundtrip(tmp_path: Path) -> None:
    snap = _make_snap(variables={"KEY": "value"})
    dest = str(tmp_path / "snap.env")
    export_snapshot(snap, dest)
    loaded = import_snapshot(dest, name="dotenv_snap")
    assert loaded.name == "dotenv_snap"
    assert loaded.variables["KEY"] == "value"


def test_import_dotenv_skips_comments(tmp_path: Path) -> None:
    dotenv_file = tmp_path / "vars.env"
    dotenv_file.write_text('# comment\nALPHA="one"\n')
    loaded = import_snapshot(str(dotenv_file), name="c")
    assert "ALPHA" in loaded.variables
    assert len(loaded.variables) == 1


def test_import_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        import_snapshot(str(tmp_path / "no_such.json"), name="x")


def test_import_unknown_format_raises(tmp_path: Path) -> None:
    f = tmp_path / "data.xyz"
    f.write_text("{}")
    with pytest.raises(UnsupportedFormatError):
        import_snapshot(str(f), name="x", fmt="xyz")


def test_import_sets_description(tmp_path: Path) -> None:
    snap = _make_snap()
    dest = str(tmp_path / "snap.json")
    export_snapshot(snap, dest)
    loaded = import_snapshot(dest, name="desc_snap", description="my desc")
    assert loaded.description == "my desc"
