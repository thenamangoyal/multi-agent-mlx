"""Data models for tasks, results, and error reports."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import yaml


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class Task:
    name: str
    description: str
    constraints: list[str] = field(default_factory=list)
    max_attempts: int | None = None  # override config default
    timeout: int | None = None  # override config default

    @classmethod
    def from_yaml(cls, path: Path) -> "Task":
        raw = yaml.safe_load(path.read_text())
        return cls(
            name=raw.get("name", path.stem),
            description=raw["description"],
            constraints=raw.get("constraints", []),
            max_attempts=raw.get("max_attempts"),
            timeout=raw.get("timeout"),
        )

    @classmethod
    def from_string(cls, description: str) -> "Task":
        # Generate a short name from the description
        words = description.split()[:4]
        name = "-".join(w.lower() for w in words)
        return cls(name=name, description=description)


@dataclass
class ExecutionResult:
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False
    duration_seconds: float = 0.0


@dataclass
class AttemptRecord:
    attempt: int
    status: TaskStatus
    error_summary: str = ""
    duration_seconds: float = 0.0
    script_path: str = ""


@dataclass
class RunResult:
    task: Task
    status: TaskStatus
    attempts: list[AttemptRecord] = field(default_factory=list)
    final_script: str | None = None
    total_tokens_used: int = 0

    @property
    def num_attempts(self) -> int:
        return len(self.attempts)
