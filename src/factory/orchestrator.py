"""Orchestrator — drives the Coder → Sheriff feedback loop."""

from __future__ import annotations

import hashlib
import json
import shutil
import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
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


def _save_attempt_artifacts(
    workspace: Path, attempt: int, script_path: Path, sheriff_text: str | None
) -> None:
    """Save per-attempt artifacts for blog/debugging."""
    attempt_dir = workspace / f"attempt_{attempt}"
    attempt_dir.mkdir(parents=True, exist_ok=True)

    if script_path.exists():
        shutil.copy2(script_path, attempt_dir / "script.py")

    if sheriff_text:
        (attempt_dir / "sheriff_report.txt").write_text(sheriff_text)


def _save_summary(workspace: Path, result: RunResult, total_duration: float) -> None:
    """Save a JSON summary of the run for blog presentation."""
    summary = {
        "task_name": result.task.name,
        "task_description": result.task.description,
        "status": result.status.value,
        "num_attempts": result.num_attempts,
        "total_duration_seconds": round(total_duration, 2),
        "attempts": [
            {
                "attempt": rec.attempt,
                "status": rec.status.value,
                "duration_seconds": round(rec.duration_seconds, 2),
                "error_summary": rec.error_summary,
            }
            for rec in result.attempts
        ],
    }

    if result.final_script:
        summary["final_script_path"] = str(workspace / "script.py")
        import subprocess
        try:
            proc = subprocess.run(
                ["python", str(workspace / "script.py")],
                cwd=str(workspace),
                capture_output=True,
                text=True,
                timeout=60,
            )
            summary["final_stdout"] = proc.stdout
            summary["final_stderr"] = proc.stderr
            summary["final_exit_code"] = proc.returncode
        except Exception:
            pass

    (workspace / "summary.json").write_text(json.dumps(summary, indent=2))


def run_task(task: Task, config: Config) -> RunResult:
    """Run the full Coder → Sheriff loop for a task."""
    workspace = Path(config.workspace_dir) / task.name
    workspace.mkdir(parents=True, exist_ok=True)

    max_attempts = task.max_attempts or config.agent.max_attempts
    run_start = time.time()

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
        console.print(f"\n[bold cyan]{'━' * 60}[/bold cyan]")
        console.print(f"[bold cyan]  Attempt {attempt}/{max_attempts}[/bold cyan]")
        console.print(f"[bold cyan]{'━' * 60}[/bold cyan]")
        attempt_start = time.time()

        # --- Coder turn ---
        console.print("\n[yellow]🔧 Coder[/yellow] is writing code...")
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

        coder_duration = time.time() - attempt_start
        console.print(f"[dim]Coder responded in {coder_duration:.1f}s[/dim]")

        # Show Coder's commentary
        if coder_text:
            preview = coder_text[:500]
            if len(coder_text) > 500:
                preview += "..."
            console.print(Panel(preview, title="Coder Response", border_style="yellow"))

        # Check script was written
        script_path = workspace / "script.py"
        if not script_path.exists():
            console.print("[red]Coder did not write script.py![/red]")
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

        # Show the generated script
        script_content = script_path.read_text()
        line_count = len(script_content.splitlines())
        console.print(f"\n[green]Coder wrote script.py ({line_count} lines)[/green]")
        console.print(
            Syntax(script_content, "python", theme="monokai", line_numbers=True)
        )

        # --- Sheriff turn ---
        sheriff_start = time.time()
        console.print("\n[yellow]🔍 Sheriff[/yellow] is reviewing and executing...")
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

        sheriff_duration = time.time() - sheriff_start
        duration = time.time() - attempt_start
        console.print(f"[dim]Sheriff responded in {sheriff_duration:.1f}s[/dim]")

        # Show Sheriff's full report
        if sheriff_text:
            console.print(
                Panel(sheriff_text, title="Sheriff Report", border_style="red" if "FAIL" in (sheriff_text or "").upper() else "green")
            )

        # Save per-attempt artifacts
        _save_attempt_artifacts(workspace, attempt, script_path, sheriff_text)

        # --- Evaluate verdict ---
        passed = "VERDICT: PASS" in sheriff_text.upper() if sheriff_text else False

        if passed:
            console.print(
                f"\n[bold green]✅ Attempt {attempt} PASSED[/bold green] ({duration:.1f}s)"
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
                f"\n[bold red]❌ Attempt {attempt} FAILED[/bold red] ({duration:.1f}s)"
            )
            error_report = sheriff_text

            # Stagnation detection
            eh = _error_hash(sheriff_text or "")
            error_hashes.append(eh)
            stag = config.agent.stagnation_threshold
            if len(error_hashes) >= stag and len(set(error_hashes[-stag:])) == 1:
                console.print(
                    f"[bold red]⚠️  Stagnation detected: same error {stag} times in a row. Stopping.[/bold red]"
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
        total_tokens += config.agent.max_tokens_per_turn * 2
        if total_tokens >= config.agent.total_token_budget:
            console.print("[bold red]Token budget exhausted. Stopping.[/bold red]")
            break

    if result.status != TaskStatus.SUCCESS:
        result.status = TaskStatus.FAILED

    total_duration = time.time() - run_start
    _print_summary(result)
    _save_summary(workspace, result, total_duration)

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
