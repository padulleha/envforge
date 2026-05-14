"""Tests for envforge.chain module."""
import pytest
from envforge.chain import (
    SnapshotChain,
    add_chain,
    apply_chain,
    get_chain,
    remove_chain,
)


def _chain(name="mychain", steps=None, description=""):
    return SnapshotChain(name=name, steps=steps or ["s1", "s2"], description=description)


def test_chain_roundtrip():
    c = _chain(description="test desc")
    assert SnapshotChain.from_dict(c.to_dict()) == c


def test_chain_defaults():
    c = SnapshotChain(name="x", steps=["a"])
    assert c.description == ""


def test_chain_format_contains_name_and_steps():
    c = _chain(name="deploy", steps=["base", "prod"])
    text = c.format()
    assert "deploy" in text
    assert "base" in text
    assert "prod" in text


def test_chain_format_with_description():
    c = _chain(description="my desc")
    assert "my desc" in c.format()


def test_add_chain_creates_new():
    chains = add_chain([], "ci", ["a", "b"])
    assert len(chains) == 1
    assert chains[0].name == "ci"
    assert chains[0].steps == ["a", "b"]


def test_add_chain_replaces_existing():
    existing = [_chain(name="ci", steps=["old"])]
    chains = add_chain(existing, "ci", ["new1", "new2"])
    assert len(chains) == 1
    assert chains[0].steps == ["new1", "new2"]


def test_add_chain_sorted():
    chains = add_chain([], "z", ["x"])
    chains = add_chain(chains, "a", ["y"])
    assert chains[0].name == "a"
    assert chains[1].name == "z"


def test_add_chain_empty_name_raises():
    with pytest.raises(ValueError, match="name"):
        add_chain([], "", ["s1"])


def test_add_chain_empty_steps_raises():
    with pytest.raises(ValueError, match="step"):
        add_chain([], "ci", [])


def test_remove_chain_present():
    chains = [_chain(name="ci"), _chain(name="cd")]
    result = remove_chain(chains, "ci")
    assert len(result) == 1
    assert result[0].name == "cd"


def test_remove_chain_missing_raises():
    with pytest.raises(KeyError):
        remove_chain([], "ghost")


def test_get_chain_found():
    chains = [_chain(name="ci")]
    c = get_chain(chains, "ci")
    assert c is not None
    assert c.name == "ci"


def test_get_chain_not_found():
    assert get_chain([], "nope") is None


class _FakeSnap:
    def __init__(self, name):
        self.name = name
        self.applied = False
        self.overwrite_used = None

    def apply(self, overwrite=True):
        self.applied = True
        self.overwrite_used = overwrite


class _FakeStore:
    def __init__(self, snaps):
        self._snaps = {s.name: s for s in snaps}

    def get(self, name):
        return self._snaps.get(name)


def test_apply_chain_calls_apply_in_order():
    s1 = _FakeSnap("s1")
    s2 = _FakeSnap("s2")
    store = _FakeStore([s1, s2])
    chain = SnapshotChain(name="c", steps=["s1", "s2"])
    applied = apply_chain(chain, store)
    assert applied == ["s1", "s2"]
    assert s1.applied
    assert s2.applied


def test_apply_chain_missing_snapshot_raises():
    store = _FakeStore([])
    chain = SnapshotChain(name="c", steps=["missing"])
    with pytest.raises(KeyError, match="missing"):
        apply_chain(chain, store)


def test_apply_chain_passes_overwrite_flag():
    s1 = _FakeSnap("s1")
    store = _FakeStore([s1])
    chain = SnapshotChain(name="c", steps=["s1"])
    apply_chain(chain, store, overwrite=False)
    assert s1.overwrite_used is False
