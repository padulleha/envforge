"""Tests for envforge.transform."""
import pytest
from envforge.transform import (
    TransformRule,
    TransformError,
    parse_rule,
    apply_transform_chain,
    transform_snapshot_values,
)


# ---------------------------------------------------------------------------
# TransformRule.apply
# ---------------------------------------------------------------------------

def test_prefix_prepends_string():
    rule = TransformRule(op="prefix", arg1="PROD_")
    assert rule.apply("VALUE") == "PROD_VALUE"


def test_suffix_appends_string():
    rule = TransformRule(op="suffix", arg1="_TEST")
    assert rule.apply("VALUE") == "VALUE_TEST"


def test_upper_uppercases():
    assert TransformRule(op="upper").apply("hello") == "HELLO"


def test_lower_lowercases():
    assert TransformRule(op="lower").apply("HELLO") == "hello"


def test_strip_removes_whitespace():
    assert TransformRule(op="strip").apply("  hi  ") == "hi"


def test_replace_substitutes():
    rule = TransformRule(op="replace", arg1="foo", arg2="bar")
    assert rule.apply("foobar") == "barbar"


def test_re_replace_substitutes():
    rule = TransformRule(op="re_replace", arg1=r"\d+", arg2="NUM")
    assert rule.apply("port8080") == "portNUM"


def test_unknown_op_raises():
    rule = TransformRule(op="explode")
    with pytest.raises(TransformError):
        rule.apply("x")


# ---------------------------------------------------------------------------
# to_dict / from_dict roundtrip
# ---------------------------------------------------------------------------

def test_roundtrip():
    rule = TransformRule(op="replace", arg1="a", arg2="b")
    assert TransformRule.from_dict(rule.to_dict()) == rule


def test_str_no_args():
    assert str(TransformRule(op="upper")) == "upper"


def test_str_with_args():
    assert str(TransformRule(op="prefix", arg1="X")) == "prefix:X"


# ---------------------------------------------------------------------------
# parse_rule
# ---------------------------------------------------------------------------

def test_parse_rule_no_args():
    r = parse_rule("upper")
    assert r.op == "upper" and r.arg1 == ""


def test_parse_rule_one_arg():
    r = parse_rule("prefix:PROD_")
    assert r.op == "prefix" and r.arg1 == "PROD_"


def test_parse_rule_two_args():
    r = parse_rule("replace:old:new")
    assert r.op == "replace" and r.arg1 == "old" and r.arg2 == "new"


# ---------------------------------------------------------------------------
# apply_transform_chain
# ---------------------------------------------------------------------------

def test_chain_applies_in_order():
    rules = [TransformRule(op="lower"), TransformRule(op="prefix", arg1="env_")]
    assert apply_transform_chain("HELLO", rules) == "env_hello"


def test_chain_empty_is_identity():
    assert apply_transform_chain("VALUE", []) == "VALUE"


# ---------------------------------------------------------------------------
# transform_snapshot_values
# ---------------------------------------------------------------------------

def _vars():
    return {"A": "hello", "B": "world", "C": "123"}


def test_transform_all_keys():
    result = transform_snapshot_values(_vars(), [TransformRule(op="upper")])
    assert result == {"A": "HELLO", "B": "WORLD", "C": "123"}


def test_transform_selected_keys():
    result = transform_snapshot_values(_vars(), [TransformRule(op="upper")], keys=["A"])
    assert result["A"] == "HELLO"
    assert result["B"] == "world"  # untouched


def test_transform_does_not_mutate_original():
    original = _vars()
    transform_snapshot_values(original, [TransformRule(op="upper")])
    assert original["A"] == "hello"


def test_transform_missing_key_in_keys_is_ignored():
    result = transform_snapshot_values(_vars(), [TransformRule(op="upper")], keys=["Z"])
    assert result == _vars()  # nothing changed
