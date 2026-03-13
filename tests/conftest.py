"""Shared test fixtures."""

import pytest
from pathlib import Path


@pytest.fixture
def tmp_workspace(tmp_path: Path) -> Path:
    """Create a temporary workspace directory."""
    ws = tmp_path / "workspace"
    ws.mkdir()
    return ws


@pytest.fixture
def sample_script(tmp_workspace: Path) -> Path:
    """Create a simple passing Python script."""
    script = tmp_workspace / "script.py"
    script.write_text("print('hello world')\n")
    return script


@pytest.fixture
def failing_script(tmp_workspace: Path) -> Path:
    """Create a Python script that raises an error."""
    script = tmp_workspace / "fail.py"
    script.write_text("raise ValueError('intentional error')\n")
    return script
