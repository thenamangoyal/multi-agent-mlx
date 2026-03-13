"""Sheriff agent — executes code, reviews errors, produces fix reports."""

from __future__ import annotations

from pathlib import Path

from agno.agent import Agent

from factory.agents.base import create_agent
from factory.config import Config
from factory.tools.executor import make_execute_code
from factory.tools.file_io import make_read_file

SHERIFF_INSTRUCTIONS = [
    "You are a strict code reviewer and test executor.",
    "Your job is to execute the Coder's script and evaluate the result.",
    "First, read the script using read_file to understand what it does.",
    "Then execute it using execute_code.",
    "If the script succeeds (exit code 0 and produces expected output), respond with EXACTLY: 'VERDICT: PASS' followed by a brief summary of the output.",
    "If the script fails, produce a structured error report in this format:",
    "",
    "VERDICT: FAIL",
    "## Error Type: <type>",
    "## Traceback:",
    "<the relevant traceback lines>",
    "## Analysis:",
    "<your interpretation of what went wrong>",
    "## Suggested Fix:",
    "<specific, actionable fix suggestion>",
    "",
    "Be specific and concise. The Coder will use your report to fix the script.",
]


def create_sheriff(workspace: Path, config: Config) -> Agent:
    """Create the Sheriff agent with execution and read tools."""
    tools = [
        make_execute_code(workspace, timeout=config.agent.execution_timeout),
        make_read_file(workspace),
    ]
    return create_agent(
        name="Sheriff",
        instructions=SHERIFF_INSTRUCTIONS,
        tools=tools,
        config=config,
    )
