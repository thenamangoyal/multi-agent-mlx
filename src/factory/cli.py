"""CLI for the multi-agent factory."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from factory.config import Config
from factory.models import Task
from factory.server import health_check, start_server, stop_server

app = typer.Typer(
    name="factory",
    help="Local multi-agent software factory on Apple Silicon.",
    no_args_is_help=True,
)
server_app = typer.Typer(help="Manage the MLX inference server.")
app.add_typer(server_app, name="server")

console = Console()


@app.command()
def run(
    description: Optional[str] = typer.Argument(
        None, help="Task description (or use --task for YAML file)"
    ),
    task: Optional[Path] = typer.Option(None, "--task", "-t", help="Path to task YAML file"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Override model ID"),
    max_attempts: Optional[int] = typer.Option(
        None, "--max-attempts", "-n", help="Max retry attempts"
    ),
    timeout: Optional[int] = typer.Option(
        None, "--timeout", help="Execution timeout per script run (seconds)"
    ),
    config_path: Optional[Path] = typer.Option(None, "--config", "-c", help="Config file path"),
    no_server: bool = typer.Option(
        False, "--no-server", help="Skip auto-starting the server (assume it's running)"
    ),
) -> None:
    """Run the Coder → Sheriff feedback loop on a task."""
    if not description and not task:
        console.print("[red]Provide a task description or --task file.[/red]")
        raise typer.Exit(1)

    # Load config
    cfg = Config.load(config_path)
    if model:
        cfg.server.model = model
    if max_attempts:
        cfg.agent.max_attempts = max_attempts
    if timeout:
        cfg.agent.execution_timeout = timeout

    # Parse task
    if task:
        t = Task.from_yaml(task)
    else:
        t = Task.from_string(description)  # type: ignore

    # Apply task-level overrides
    if t.max_attempts:
        cfg.agent.max_attempts = t.max_attempts
    if t.timeout:
        cfg.agent.execution_timeout = t.timeout

    # Start server if needed
    proc = None
    if not no_server:
        proc = start_server(cfg.server)

    try:
        from factory.orchestrator import run_task

        result = run_task(t, cfg)
        raise typer.Exit(0 if result.status.value == "success" else 1)
    finally:
        if proc:
            stop_server(proc)


@server_app.command("start")
def server_start(
    model: Optional[str] = typer.Option(None, "--model", "-m"),
    port: int = typer.Option(8080, "--port", "-p"),
) -> None:
    """Start the MLX inference server."""
    cfg = Config()
    if model:
        cfg.server.model = model
    cfg.server.port = port
    proc = start_server(cfg.server)
    if proc:
        console.print("[green]Server running. Press Ctrl+C to stop.[/green]")
        try:
            proc.wait()
        except KeyboardInterrupt:
            stop_server(proc)


@server_app.command("status")
def server_status(
    port: int = typer.Option(8080, "--port", "-p"),
) -> None:
    """Check if the MLX server is running."""
    if health_check("127.0.0.1", port):
        console.print(f"[green]Server is running on port {port}.[/green]")
    else:
        console.print(f"[red]No server detected on port {port}.[/red]")


@server_app.command("stop")
def server_stop() -> None:
    """Stop the server (if started by factory)."""
    console.print("[yellow]Use Ctrl+C on the running server process, or kill the process manually.[/yellow]")


if __name__ == "__main__":
    app()
