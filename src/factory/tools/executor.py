"""Code execution tool — runs scripts in a sandboxed subprocess."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from factory.models import ExecutionResult


def _truncate(text: str, max_lines: int = 100) -> str:
    """Keep the last max_lines of output."""
    lines = text.splitlines()
    if len(lines) > max_lines:
        return f"... [{len(lines) - max_lines} lines truncated]\n" + "\n".join(
            lines[-max_lines:]
        )
    return text


def execute_script(
    script_path: Path,
    workspace: Path,
    timeout: int = 60,
) -> ExecutionResult:
    """Execute a Python script in the workspace with timeout."""
    if not script_path.exists():
        return ExecutionResult(
            exit_code=1,
            stdout="",
            stderr=f"Script not found: {script_path}",
        )

    start = time.time()
    try:
        result = subprocess.run(
            ["python", str(script_path)],
            cwd=str(workspace),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        duration = time.time() - start
        return ExecutionResult(
            exit_code=result.returncode,
            stdout=_truncate(result.stdout),
            stderr=_truncate(result.stderr),
            duration_seconds=duration,
        )
    except subprocess.TimeoutExpired:
        duration = time.time() - start
        return ExecutionResult(
            exit_code=-1,
            stdout="",
            stderr=f"Script timed out after {timeout} seconds",
            timed_out=True,
            duration_seconds=duration,
        )


def make_execute_code(workspace: Path, timeout: int = 60):
    """Create an execute_code tool bound to a workspace directory."""

    def execute_code(script_path: str, timeout_override: int | None = None) -> str:
        """Execute a Python script and return stdout + stderr.

        Args:
            script_path: Path to the script, relative to workspace.
            timeout_override: Optional timeout in seconds (default from config).
        """
        full_path = (workspace / script_path).resolve()
        # Sandbox check
        if not str(full_path).startswith(str(workspace.resolve())):
            return "Error: path escapes workspace sandbox"

        t = timeout_override or timeout
        result = execute_script(full_path, workspace, t)

        parts = [f"Exit code: {result.exit_code}"]
        if result.timed_out:
            parts.append(f"TIMED OUT after {t}s")
        if result.stdout.strip():
            parts.append(f"--- stdout ---\n{result.stdout}")
        if result.stderr.strip():
            parts.append(f"--- stderr ---\n{result.stderr}")
        if not result.stdout.strip() and not result.stderr.strip():
            parts.append("(no output)")

        return "\n".join(parts)

    return execute_code
