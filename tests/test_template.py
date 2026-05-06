"""Tests for envforge.template and envforge.cli_template."""

from __future__ import annotations

import json
import pytest

from envforge.template import (
    SnapshotTemplate,
    TemplateVar,
    TemplateMissingValueError,
)


# ---------------------------------------------------------------------------
# TemplateVar
# ---------------------------------------------------------------------------

def test_template_var_roundtrip():
    var = TemplateVar(key="DB_HOST", description="Database host", default="localhost", required=False)
    assert TemplateVar.from_dict(var.to_dict()) == var


def test_template_var_defaults():
    var = TemplateVar(key="X")
    assert var.required is True
    assert var.default is None
    assert var.description == ""


# ---------------------------------------------------------------------------
# SnapshotTemplate.render
# ---------------------------------------------------------------------------

def _make_template() -> SnapshotTemplate:
    return SnapshotTemplate(
        name="myapp",
        vars=[
            TemplateVar(key="APP_ENV", default="production", required=True),
            TemplateVar(key="SECRET_KEY", required=True),
            TemplateVar(key="DEBUG", default="false", required=False),
            TemplateVar(key="OPTIONAL_VAR", required=False),
        ],
    )


def test_render_uses_defaults():
    t = _make_template()
    result = t.render({"SECRET_KEY": "s3cr3t"})
    assert result["APP_ENV"] == "production"
    assert result["SECRET_KEY"] == "s3cr3t"
    assert result["DEBUG"] == "false"


def test_render_overrides_default():
    t = _make_template()
    result = t.render({"SECRET_KEY": "abc", "APP_ENV": "staging"})
    assert result["APP_ENV"] == "staging"


def test_render_missing_required_raises():
    t = _make_template()
    with pytest.raises(TemplateMissingValueError) as exc_info:
        t.render({})
    assert "SECRET_KEY" in exc_info.value.missing


def test_render_optional_no_default_excluded():
    t = _make_template()
    result = t.render({"SECRET_KEY": "x"})
    assert "OPTIONAL_VAR" not in result


def test_render_empty_overrides_ok():
    t = SnapshotTemplate(
        name="simple",
        vars=[TemplateVar(key="FOO", default="bar")],
    )
    result = t.render()
    assert result == {"FOO": "bar"}


# ---------------------------------------------------------------------------
# SnapshotTemplate serialization
# ---------------------------------------------------------------------------

def test_template_roundtrip():
    t = _make_template()
    restored = SnapshotTemplate.from_dict(t.to_dict())
    assert restored.name == t.name
    assert len(restored.vars) == len(t.vars)
    assert restored.vars[0].key == "APP_ENV"


def test_template_from_dict_missing_vars_defaults_empty():
    t = SnapshotTemplate.from_dict({"name": "empty"})
    assert t.vars == []
    assert t.description == ""


def test_missing_value_error_message():
    err = TemplateMissingValueError(["A", "B"])
    assert "A" in str(err)
    assert "B" in str(err)
