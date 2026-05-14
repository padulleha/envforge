"""Snapshot formatting: render a snapshot as a human-readable table or compact summary."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envforge.snapshot import Snapshot


@dataclass
class FormatOptions:
    max_value_length: int = 60
    show_index: bool = True
    show_types: bool = False
    title: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "max_value_length": self.max_value_length,
            "show_index": self.show_index,
            "show_types": self.show_types,
            "title": self.title,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FormatOptions":
        return cls(
            max_value_length=data.get("max_value_length", 60),
            show_index=data.get("show_index", True),
            show_types=data.get("show_types", False),
            title=data.get("title"),
        )


def _truncate(value: str, max_len: int) -> str:
    if len(value) <= max_len:
        return value
    return value[: max_len - 3] + "..."


def _infer_type(value: str) -> str:
    if value.lower() in ("true", "false"):
        return "bool"
    try:
        int(value)
        return "int"
    except ValueError:
        pass
    try:
        float(value)
        return "float"
    except ValueError:
        pass
    return "str"


def format_table(snapshot: Snapshot, options: Optional[FormatOptions] = None) -> str:
    """Render snapshot variables as an aligned text table."""
    if options is None:
        options = FormatOptions()

    rows: List[tuple] = []
    for key, value in sorted(snapshot.variables.items()):
        truncated = _truncate(value, options.max_value_length)
        if options.show_types:
            rows.append((key, truncated, _infer_type(value)))
        else:
            rows.append((key, truncated))

    if not rows:
        return f"Snapshot '{snapshot.name}' has no variables."

    col_widths = [max(len(r[i]) for r in rows) for i in range(len(rows[0]))]
    headers = ["KEY", "VALUE", "TYPE"][: len(rows[0])]
    col_widths = [max(col_widths[i], len(headers[i])) for i in range(len(col_widths))]

    sep = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
    header_row = "| " + " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers)) + " |"

    lines = []
    title = options.title or f"Snapshot: {snapshot.name}"
    lines.append(title)
    lines.append(sep)
    lines.append(header_row)
    lines.append(sep)
    for idx, row in enumerate(rows):
        prefix = f"{idx + 1:>3}  " if options.show_index else ""
        line = "| " + " | ".join(str(row[i]).ljust(col_widths[i]) for i in range(len(row))) + " |"
        if options.show_index:
            line = f"{idx + 1:>3}  {line}"
        lines.append(line)
    lines.append(sep)
    return "\n".join(lines)


def format_compact(snapshot: Snapshot) -> str:
    """One-line-per-variable compact output: KEY=VALUE."""
    if not snapshot.variables:
        return ""
    return "\n".join(
        f"{k}={v}" for k, v in sorted(snapshot.variables.items())
    )
