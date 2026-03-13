"""Orchestrator — drives the Coder → Sheriff feedback loop."""

from __future__ import annotations

import hashlib
import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from factory.agents.coder import create_coder
from factory.agents.sheriff import create_sheriff
from factory.config import Config
from factory.models import AttemptRecord, RunResult, Task, TaskStatus

console = Console()


def _error_hash(text: str) -> str:
    """Hash the last 5 lines of an error for stagnation detection."""
    lines = text.strip().splitlines()[-5:]
    return hashlib.md5("\n".join(lines).encode()).hexdigest()


def _build_coder_prompt(task: Task, attempt: int, error_report: str | None) -> str:
    """Build the prompt for the Coder agent."""
    parts = [f"## Task\n{task.description}"]

    if task.constraints:
        parts.append("## Constraints")
        for c in task.constraints:
            parts.append(f"- {c}")

    if error_report:
        parts.append(f"## Previous Attempt #{attempt - 1} Failed")
        parts.append(error_report)
        parts.append(
            "\nFix the issues described above. Write the corrected script.py file."
        )

    return "\n\n".join(parts)


def _build_sheriff_prompt(attempt: int) -> str:
    """Build the prompt for the Sheriff agent."""
    return (
        f"## Review Attempt #{attempt}\n\n"
        "Read the file `script.py`, then execute it using `execute_code`.\n"
        "Evaluate whether it runs successfully and produces correct output.\n"
        "Respond with your VERDICT (PASS or FAIL) and analysis."
    )


def run_task(task: Task, config: Config) -> RunResult:
    """Run the full Coder → Sheriff loop for a task."""
    # Set up workspace
    workspace = Path(config.workspace_dir) / task.name
    workspace.mkdir(parents=True, exist_ok=True)

    max_attempts = task.max_attempts or config.agent.max_attempts

    # Create agents
    coder = create_coder(workspace, config)
    sheriff = create_sheriff(workspace, config)

    result = RunResult(task=task, status=TaskStatus.RUNNING)
    error_report: str | None = None
    error_hashes: list[str] = []
    total_tokens = 0

    console.print(
        Panel(
            f"[bold]{task.name}[/bold]\n{task.description}",
            title="Starting Task",
            border_style="blue",
        )
    )

    for attempt in range(1, max_attempts + 1):
        console.print(f"\n[bold cyan]━━━ Attempt {attempt}/{max_attempts} ━━━[/bold cyan]")
        attempt_start = time.time()

        # --- Coder turn ---
        console.print("[yellow]Coder[/yellow] is writing code...")
        coder_prompt = _build_coder_prompt(task, attempt, error_report)

        try:
            coder_response = coder.run(coder_prompt)
            coder_text = coder_response.content if coder_response else ""
        except Exception as e:
            console.print(f"[red]Coder error: {e}[/red]")
            result.attempts.append(
                AttemptRecord(
                    attempt=attempt,
                    status=TaskStatus.FAILED,
                    error_summary=f"Coder LLM error: {e}",
                )
            )
            continue

        # Check script was written
        script_path = workspace / "script.py"
        if not script_path.exists():
            console.print("[red]Coder did not write script.py[/red]")
            error_report = (
                "VERDICT: FAIL\n"
                "## Error Type: MissingFile\n"
                "## Analysis: You did not write script.py. Use the write_file tool to create it.\n"
                "## Suggested Fix: Call write_file('script.py', <your code>)"
            )
            result.attempts.append(
                AttemptRecord(
                    attempt=attempt,
                    status=TaskStatus.FAILED,
                    error_summary="Coder did not produce script.py",
                )
            )
            continue

        console.print("[green]Coder wrote script.py[/green]")

        # --- Sheriff turn ---
        console.print("[yellow]Sheriff[/yellow] is reviewing and executing...")
        sheriff_prompt = _build_sheriff_prompt(attempt)

        try:
            sheriff_response = sheriff.run(sheriff_prompt)
            sheriff_text = sheriff_response.content if sheriff_response else ""
        except Exception as e:
            console.print(f"[red]Sheriff error: {e}[/red]")
            result.attempts.append(
                AttemptRecord(
                    attempt=attempt,
                    status=TaskStatus.FAILED,
                    error_summary=f"Sheriff LLM error: {e}",
                )
            )
            continue

        duration = time.time() - attempt_start

        # --- Evaluate verdict ---
        passed = "VERDICT: PASS" in sheriff_text.upper() if sheriff_text else False

        if passed:
            console.print(
                f"[bold green]Attempt {attempt} PASSED[/bold green] ({duration:.1f}s)"
            )
            result.attempts.append(
                AttemptRecord(
                    attempt=attempt,
                    status=TaskStatus.SUCCESS,
                    duration_seconds=duration,
                    script_path=str(script_path),
                )
            )
            result.status = TaskStatus.SUCCESS
            result.final_script = script_path.read_text()
            break
        else:
            console.print(
                f"[bold red]Attempt {attempt} FAILED[/bold red] ({duration:.1f}s)"
            )
            error_report = sheriff_text

            # Stagnation detection
            eh = _error_hash(sheriff_text or "")
            error_hashes.append(eh)
            stag = config.agent.stagnation_threshold
            if len(error_hashes) >= stag and len(set(error_hashes[-stag:])) == 1:
                console.print(
                    f"[bold red]Stagnation detected: same error {stag} times in a row. Stopping.[/bold red]"
                )
                result.attempts.append(
                    AttemptRecord(
                        attempt=attempt,
                        status=TaskStatus.FAILED,
                        error_summary="Stagnation: repeated identical error",
                        duration_seconds=duration,
                    )
                )
                break

            result.attempts.append(
                AttemptRecord(
                    attempt=attempt,
                    status=TaskStatus.FAILED,
                    error_summary=(sheriff_text or "")[:200],
                    duration_seconds=duration,
                )
            )

        # Token budget check
        total_tokens += config.agent.max_tokens_per_turn * 2  # rough estimate
        if total_tokens >= config.agent.total_token_budget:
            console.print("[bold red]Token budget exhausted. Stopping.[/bold red]")
            break

    if result.status != TaskStatus.SUCCESS:
        result.status = TaskStatus.FAILED

    _print_summary(result)
    return result


def _print_summary(result: RunResult) -> None:
    """Print a summary table of the run."""
    table = Table(title="Run Summary")
    table.add_column("Attempt", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Duration", style="green")
    table.add_column("Notes")

    for rec in result.attempts:
        status_style = "green" if rec.status == TaskStatus.SUCCESS else "red"
        table.add_row(
            str(rec.attempt),
            f"[{status_style}]{rec.status.value}[/{status_style}]",
            f"{rec.duration_seconds:.1f}s",
            rec.error_summary[:80] if rec.error_summary else "",
        )

    console.print(table)
    console.print(
        f"\n[bold]Final status: "
        f"{'[green]SUCCESS' if result.status == TaskStatus.SUCCESS else '[red]FAILED'}[/bold]"
        f" after {result.num_attempts} attempt(s)"
    )
    if result.final_script:
        console.print(
            f"[green]Script saved at: {result.attempts[-1].script_path}[/green]"
        )
