"""Coder agent — writes Python scripts to fulfill tasks."""

from __future__ import annotations

from pathlib import Path

from agno.agent import Agent

from factory.agents.base import create_agent
from factory.config import Config
from factory.tools.file_io import make_list_files, make_read_file, make_write_file

CODER_INSTRUCTIONS = [
    "You are an expert Python developer specializing in machine learning with MLX on Apple Silicon.",
    "Your job is to write complete, runnable Python scripts that fulfill the given task.",
    "ALWAYS write the script to a file using the write_file tool. The main script should be named 'script.py'.",
    "Write self-contained scripts — include all imports, avoid external dependencies not in the standard library or common ML packages (mlx, numpy, etc).",
    "If you receive an error report from a previous attempt, carefully analyze the traceback and fix the specific issue.",
    "Do NOT apologize or explain at length. Write the corrected code immediately.",
    "After writing the file, briefly explain what you wrote and any key design decisions.",
]


def create_coder(workspace: Path, config: Config) -> Agent:
    """Create the Coder agent with file I/O tools."""
    tools = [
        make_write_file(workspace),
        make_read_file(workspace),
        make_list_files(workspace),
    ]
    return create_agent(
        name="Coder",
        instructions=CODER_INSTRUCTIONS,
        tools=tools,
        config=config,
    )
