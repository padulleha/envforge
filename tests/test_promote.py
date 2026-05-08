"""Tests for envforge.promote."""
from __future__ import annotations

import pytest

from envforge.promote import (
    DEFAULT_TIERS,
    PromoteError,
    PromoteResult,
    _next_tier,
    promote_snapshot,
)
from envforge.snapshot import Snapshot


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _snap(name: str, variables: dict | None = None, tags=None) -> Snapshot:
    return Snapshot(
        name=name,
        variables=variables or {"KEY": "value"},
        tags=tags or [],
    )


class _FakeStore:
    def __init__(self, snaps=None):
        self._data: dict[str, Snapshot] = {s.name: s for s in (snaps or [])}

    def get(self, name: str):
        return self._data.get(name)

    def save(self, snap: Snapshot):
        self._data[snap.name] = snap


# ---------------------------------------------------------------------------
# _next_tier
# ---------------------------------------------------------------------------

def test_next_tier_dev_to_staging():
    assert _next_tier("dev", DEFAULT_TIERS) == "staging"


def test_next_tier_staging_to_prod():
    assert _next_tier("staging", DEFAULT_TIERS) == "prod"


def test_next_tier_last_raises():
    with pytest.raises(PromoteError, match="last tier"):
        _next_tier("prod", DEFAULT_TIERS)


def test_next_tier_unknown_raises():
    with pytest.raises(PromoteError, match="not found"):
        _next_tier("qa", DEFAULT_TIERS)


# ---------------------------------------------------------------------------
# promote_snapshot
# ---------------------------------------------------------------------------

def test_promote_auto_dest_name():
    store = _FakeStore([_snap("myapp-dev")])
    result = promote_snapshot(store, "myapp-dev", "dev")
    assert result.dest_name == "myapp-staging"
    assert store.get("myapp-staging") is not None


def test_promote_explicit_dest_name():
    store = _FakeStore([_snap("myapp-dev")])
    result = promote_snapshot(store, "myapp-dev", "dev", dest_name="custom-staging")
    assert result.dest_name == "custom-staging"


def test_promote_copies_variables():
    snap = _snap("app-dev", variables={"A": "1", "B": "2"})
    store = _FakeStore([snap])
    promote_snapshot(store, "app-dev", "dev")
    dest = store.get("app-staging")
    assert dest.variables == {"A": "1", "B": "2"}


def test_promote_keys_copied_count():
    snap = _snap("app-dev", variables={"X": "1", "Y": "2", "Z": "3"})
    store = _FakeStore([snap])
    result = promote_snapshot(store, "app-dev", "dev")
    assert result.keys_copied == 3


def test_promote_missing_source_raises():
    store = _FakeStore()
    with pytest.raises(PromoteError, match="not found"):
        promote_snapshot(store, "ghost", "dev")


def test_promote_no_overwrite_raises_if_dest_exists():
    store = _FakeStore([_snap("app-dev"), _snap("app-staging")])
    with pytest.raises(PromoteError, match="already exists"):
        promote_snapshot(store, "app-dev", "dev")


def test_promote_overwrite_flag_replaces_dest():
    store = _FakeStore([_snap("app-dev", {"NEW": "val"}), _snap("app-staging", {"OLD": "val"})])
    result = promote_snapshot(store, "app-dev", "dev", overwrite=True)
    assert result.overwritten is True
    assert store.get("app-staging").variables == {"NEW": "val"}


def test_promote_result_str_contains_tiers():
    result = PromoteResult(
        source_name="app-dev",
        dest_name="app-staging",
        tier_from="dev",
        tier_to="staging",
        keys_copied=2,
    )
    text = str(result)
    assert "dev" in text
    assert "staging" in text
    assert "app-dev" in text


def test_promote_custom_tiers():
    store = _FakeStore([_snap("app-alpha")])
    result = promote_snapshot(
        store, "app-alpha", "alpha",
        tiers=["alpha", "beta", "release"]
    )
    assert result.tier_to == "beta"
