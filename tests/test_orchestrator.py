"""Tests for the orchestrator (with mocked LLM calls)."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from factory.config import Config
from factory.models import Task, TaskStatus
from factory.orchestrator import _error_hash, _build_coder_prompt


def test_error_hash_same_input():
    a = _error_hash("line1\nline2\nline3")
    b = _error_hash("line1\nline2\nline3")
    assert a == b


def test_error_hash_different_input():
    a = _error_hash("error A")
    b = _error_hash("error B")
    assert a != b


def test_build_coder_prompt_first_attempt():
    task = Task(name="test", description="Write hello world", constraints=["Use print()"])
    prompt = _build_coder_prompt(task, attempt=1, error_report=None)
    assert "Write hello world" in prompt
    assert "Use print()" in prompt
    assert "Failed" not in prompt


def test_build_coder_prompt_with_error():
    task = Task(name="test", description="Write hello world")
    prompt = _build_coder_prompt(task, attempt=2, error_report="VERDICT: FAIL\nNameError")
    assert "Write hello world" in prompt
    assert "FAIL" in prompt
    assert "NameError" in prompt


def test_task_from_string():
    t = Task.from_string("Write a fibonacci calculator")
    assert t.description == "Write a fibonacci calculator"
    assert t.name  # should have auto-generated name


def test_task_from_yaml(tmp_path: Path):
    yaml_content = """
name: test-task
description: Write hello world
constraints:
  - Use print only
max_attempts: 3
"""
    p = tmp_path / "task.yaml"
    p.write_text(yaml_content)
    t = Task.from_yaml(p)
    assert t.name == "test-task"
    assert t.max_attempts == 3
    assert len(t.constraints) == 1
