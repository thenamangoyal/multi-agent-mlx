"""File I/O tools for agents — sandboxed to task workspace."""

from __future__ import annotations

import os
from pathlib import Path


def _resolve_safe(workspace: Path, relative_path: str) -> Path:
    """Resolve a path ensuring it stays within the workspace sandbox."""
    resolved = (workspace / relative_path).resolve()
    if not str(resolved).startswith(str(workspace.resolve())):
        raise ValueError(f"Path escapes workspace sandbox: {relative_path}")
    return resolved


def make_write_file(workspace: Path):
    """Create a write_file tool bound to a workspace directory."""

    def write_file(path: str, content: str) -> str:
        """Write content to a file in the workspace. Path is relative to task directory."""
        target = _resolve_safe(workspace, path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        return f"Wrote {len(content)} chars to {path}"

    return write_file


def make_read_file(workspace: Path):
    """Create a read_file tool bound to a workspace directory."""

    def read_file(path: str) -> str:
        """Read a file from the workspace."""
        target = _resolve_safe(workspace, path)
        if not target.exists():
            return f"Error: file not found: {path}"
        content = target.read_text()
        if len(content) > 8000:
            return content[:8000] + f"\n\n... [truncated, {len(content)} total chars]"
        return content

    return read_file


def make_list_files(workspace: Path):
    """Create a list_files tool bound to a workspace directory."""

    def list_files(directory: str = ".") -> str:
        """List files in the workspace directory."""
        target = _resolve_safe(workspace, directory)
        if not target.is_dir():
            return f"Error: not a directory: {directory}"
        entries = []
        for root, dirs, files in os.walk(target):
            level = len(Path(root).relative_to(target).parts)
            indent = "  " * level
            entries.append(f"{indent}{Path(root).name}/")
            for f in sorted(files):
                entries.append(f"{indent}  {f}")
        return "\n".join(entries) if entries else "(empty directory)"

    return list_files
