"""Tests for envforge.snapshot_namespace."""
import pytest

from envforge.snapshot_namespace import (
    NamespaceTree,
    build_namespace_tree,
    group_by_namespace,
    infer_namespace,
)


# ---------------------------------------------------------------------------
# infer_namespace
# ---------------------------------------------------------------------------

def test_infer_namespace_with_dot():
    assert infer_namespace("prod.api") == "prod"


def test_infer_namespace_multiple_dots():
    assert infer_namespace("prod.api.v2") == "prod"


def test_infer_namespace_no_dot_returns_none():
    assert infer_namespace("mysnap") is None


def test_infer_namespace_empty_string_returns_none():
    assert infer_namespace("") is None


# ---------------------------------------------------------------------------
# group_by_namespace
# ---------------------------------------------------------------------------

def test_group_by_namespace_basic():
    names = ["prod.web", "prod.db", "dev.web", "local"]
    groups = group_by_namespace(names)
    assert set(groups["prod"]) == {"prod.web", "prod.db"}
    assert groups["dev"] == ["dev.web"]
    assert groups[""] == ["local"]


def test_group_by_namespace_all_namespaced():
    names = ["a.x", "a.y", "b.z"]
    groups = group_by_namespace(names)
    assert "" not in groups
    assert sorted(groups["a"]) == ["a.x", "a.y"]


def test_group_by_namespace_empty_list():
    assert group_by_namespace([]) == {}


def test_group_by_namespace_no_namespace():
    names = ["alpha", "beta"]
    groups = group_by_namespace(names)
    assert list(groups.keys()) == [""]
    assert sorted(groups[""]) == ["alpha", "beta"]


# ---------------------------------------------------------------------------
# NamespaceTree
# ---------------------------------------------------------------------------

def test_tree_insert_flat_name():
    tree = NamespaceTree(root="<root>")
    tree.insert("mysnap")
    assert "mysnap" in tree.snapshots
    assert not tree.children


def test_tree_insert_namespaced_creates_child():
    tree = NamespaceTree(root="<root>")
    tree.insert("prod.web")
    assert "prod" in tree.children
    assert "web" in tree.children["prod"].snapshots


def test_tree_insert_deep_nesting():
    tree = NamespaceTree(root="<root>")
    tree.insert("prod.api.v2")
    assert "prod" in tree.children
    assert "api" in tree.children["prod"].children
    assert "v2" in tree.children["prod"].children["api"].snapshots


# ---------------------------------------------------------------------------
# build_namespace_tree
# ---------------------------------------------------------------------------

def test_build_namespace_tree_mixed():
    names = ["prod.web", "dev.web", "local"]
    tree = build_namespace_tree(names)
    assert "local" in tree.snapshots
    assert "prod" in tree.children
    assert "dev" in tree.children


def test_build_namespace_tree_format_contains_names():
    names = ["prod.web", "prod.db", "local"]
    tree = build_namespace_tree(names)
    rendered = tree.format()
    assert "local" in rendered
    assert "[prod]" in rendered
    assert "web" in rendered
    assert "db" in rendered


def test_build_namespace_tree_empty():
    tree = build_namespace_tree([])
    assert tree.snapshots == []
    assert tree.children == {}
    assert tree.format() == ""
