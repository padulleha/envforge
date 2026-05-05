"""Export snapshots to various shell-compatible formats."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from envforge.snapshot import Snapshot


def to_shell_export(snapshot: "Snapshot", shell: str = "bash") -> str:
    """Return a shell script that exports all variables in the snapshot.

    Args:
        snapshot: The snapshot to export.
        shell: Target shell ('bash', 'fish', or 'powershell').

    Returns:
        A string containing shell commands to export the variables.
    """
    if shell in ("bash", "zsh", "sh"):
        return _to_posix_export(snapshot)
    elif shell == "fish":
        return _to_fish_export(snapshot)
    elif shell in ("powershell", "pwsh"):
        return _to_powershell_export(snapshot)
    else:
        raise ValueError(f"Unsupported shell: {shell!r}. Choose from: bash, zsh, sh, fish, powershell.")


def _escape_posix(value: str) -> str:
    """Escape a value for use in POSIX shell single-quoted strings."""
    return value.replace("'", "'\"'\"'")


def _to_posix_export(snapshot: "Snapshot") -> str:
    lines = [f"# envforge snapshot: {snapshot.name}"]
    if snapshot.description:
        lines.append(f"# {snapshot.description}")
    lines.append("")
    for key, value in sorted(snapshot.variables.items()):
        escaped = _escape_posix(value)
        lines.append(f"export {key}='{escaped}'")
    return "\n".join(lines) + "\n"


def _to_fish_export(snapshot: "Snapshot") -> str:
    lines = [f"# envforge snapshot: {snapshot.name}"]
    if snapshot.description:
        lines.append(f"# {snapshot.description}")
    lines.append("")
    for key, value in sorted(snapshot.variables.items()):
        escaped = value.replace("\\", "\\\\").replace("'", "\\'")
        lines.append(f"set -x {key} '{escaped}'")
    return "\n".join(lines) + "\n"


def _to_powershell_export(snapshot: "Snapshot") -> str:
    lines = [f"# envforge snapshot: {snapshot.name}"]
    if snapshot.description:
        lines.append(f"# {snapshot.description}")
    lines.append("")
    for key, value in sorted(snapshot.variables.items()):
        escaped = value.replace("'", "''")
        lines.append(f"$env:{key} = '{escaped}'")
    return "\n".join(lines) + "\n"


def to_dotenv(snapshot: "Snapshot") -> str:
    """Export snapshot as a .env file format."""
    lines = [f"# envforge snapshot: {snapshot.name}"]
    if snapshot.description:
        lines.append(f"# {snapshot.description}")
    lines.append("")
    for key, value in sorted(snapshot.variables.items()):
        needs_quotes = any(c in value for c in (' ', '\t', '#', '"', "'", '\n'))
        if needs_quotes:
            escaped = value.replace('"', '\\"')
            lines.append(f'{key}="{escaped}"')
        else:
            lines.append(f"{key}={value}")
    return "\n".join(lines) + "\n"
