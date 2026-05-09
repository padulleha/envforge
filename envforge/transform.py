"""Value transformation rules for snapshots (prefix, suffix, upper, lower, replace)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import re


CHAIN_SEP = "|"


class TransformError(ValueError):
    pass


@dataclass
class TransformRule:
    op: str          # prefix | suffix | upper | lower | replace | strip
    arg1: str = ""   # first argument (pattern for replace, value for prefix/suffix)
    arg2: str = ""   # second argument (replacement for replace)

    def apply(self, value: str) -> str:
        if self.op == "prefix":
            return self.arg1 + value
        elif self.op == "suffix":
            return value + self.arg1
        elif self.op == "upper":
            return value.upper()
        elif self.op == "lower":
            return value.lower()
        elif self.op == "strip":
            return value.strip()
        elif self.op == "replace":
            return value.replace(self.arg1, self.arg2)
        elif self.op == "re_replace":
            return re.sub(self.arg1, self.arg2, value)
        else:
            raise TransformError(f"Unknown transform op: {self.op!r}")

    def to_dict(self) -> dict:
        return {"op": self.op, "arg1": self.arg1, "arg2": self.arg2}

    @classmethod
    def from_dict(cls, d: dict) -> "TransformRule":
        return cls(op=d["op"], arg1=d.get("arg1", ""), arg2=d.get("arg2", ""))

    def __str__(self) -> str:
        parts = [self.op]
        if self.arg1:
            parts.append(self.arg1)
        if self.arg2:
            parts.append(self.arg2)
        return ":".join(parts)


def parse_rule(spec: str) -> TransformRule:
    """Parse a rule from a colon-separated spec string, e.g. 'prefix:PROD_'."""
    parts = spec.split(":", 2)
    op = parts[0].strip()
    arg1 = parts[1] if len(parts) > 1 else ""
    arg2 = parts[2] if len(parts) > 2 else ""
    return TransformRule(op=op, arg1=arg1, arg2=arg2)


def apply_transform_chain(value: str, rules: list[TransformRule]) -> str:
    """Apply a sequence of rules to a single value."""
    for rule in rules:
        value = rule.apply(value)
    return value


def transform_snapshot_values(
    variables: dict[str, str],
    rules: list[TransformRule],
    keys: Optional[list[str]] = None,
) -> dict[str, str]:
    """Return a new dict with transform rules applied to selected keys."""
    result = dict(variables)
    target_keys = keys if keys is not None else list(variables.keys())
    for k in target_keys:
        if k in result:
            result[k] = apply_transform_chain(result[k], rules)
    return result
