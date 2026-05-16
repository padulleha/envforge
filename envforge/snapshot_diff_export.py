"""Export snapshot diffs to various formats (JSON, Markdown, CSV)."""
from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass
from typing import Literal

from envforge.diff import SnapshotDiff

ExportFormat = Literal["json", "markdown", "csv"]

UNSUPPORTED_FORMAT_MSG = "Unsupported diff export format: {fmt}"


@dataclass
class DiffExportResult:
    fmt: str
    content: str

    def __str__(self) -> str:  # pragma: no cover
        return self.content


def _to_json(diff: SnapshotDiff) -> str:
    data = {
        "added": {k: diff.other.variables.get(k, "") for k in diff.added},
        "removed": {k: diff.base.variables.get(k, "") for k in diff.removed},
        "changed": {
            k: {
                "before": diff.base.variables.get(k, ""),
                "after": diff.other.variables.get(k, ""),
            }
            for k in diff.changed
        },
    }
    return json.dumps(data, indent=2)


def _to_markdown(diff: SnapshotDiff) -> str:
    lines = ["# Snapshot Diff\n"]
    if diff.added:
        lines.append("## Added")
        for k in sorted(diff.added):
            lines.append(f"- `{k}` = `{diff.other.variables.get(k, '')}`")
        lines.append("")
    if diff.removed:
        lines.append("## Removed")
        for k in sorted(diff.removed):
            lines.append(f"- `{k}` = `{diff.base.variables.get(k, '')}`")
        lines.append("")
    if diff.changed:
        lines.append("## Changed")
        for k in sorted(diff.changed):
            before = diff.base.variables.get(k, "")
            after = diff.other.variables.get(k, "")
            lines.append(f"- `{k}`: `{before}` → `{after}`")
        lines.append("")
    if not diff.has_changes:
        lines.append("_No differences found._")
    return "\n".join(lines)


def _to_csv(diff: SnapshotDiff) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["change_type", "key", "before", "after"])
    for k in sorted(diff.added):
        writer.writerow(["added", k, "", diff.other.variables.get(k, "")])
    for k in sorted(diff.removed):
        writer.writerow(["removed", k, diff.base.variables.get(k, ""), ""])
    for k in sorted(diff.changed):
        writer.writerow(
            ["changed", k, diff.base.variables.get(k, ""), diff.other.variables.get(k, "")]
        )
    return buf.getvalue()


def export_diff(diff: SnapshotDiff, fmt: ExportFormat = "json") -> DiffExportResult:
    """Export a SnapshotDiff to the requested format string."""
    if fmt == "json":
        content = _to_json(diff)
    elif fmt == "markdown":
        content = _to_markdown(diff)
    elif fmt == "csv":
        content = _to_csv(diff)
    else:
        raise ValueError(UNSUPPORTED_FORMAT_MSG.format(fmt=fmt))
    return DiffExportResult(fmt=fmt, content=content)
