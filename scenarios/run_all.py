#!/usr/bin/env python3
"""Run all three blog showcase scenarios and capture extensive logs.

Usage:
    # With server auto-management:
    uv run python scenarios/run_all.py

    # If you already have a server running:
    uv run python scenarios/run_all.py --no-server

    # Use a smaller model:
    uv run python scenarios/run_all.py --model mlx-community/Qwen2.5-Coder-1.5B-4bit
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from factory.config import Config
from factory.models import Task, TaskStatus
from factory.orchestrator import run_task
from factory.server import health_check, start_server, stop_server

SCENARIOS_DIR = Path(__file__).parent
SCENARIO_DIRS = [
    SCENARIOS_DIR / "scenario_1_calendar",
    SCENARIOS_DIR / "scenario_2_csv",
    SCENARIOS_DIR / "scenario_3_neural_net",
]

SCENARIO_TITLES = {
    "off-by-one-gauntlet": "Scenario 1: The Off-by-One Gauntlet (Pure Algorithm)",
    "csv-detective": "Scenario 2: The CSV Detective (Data Pipeline)",
    "gradient-descent-from-scratch": "Scenario 3: Gradient Descent from Scratch (ML Math)",
}


def setup_results_dir(scenario_dir: Path) -> Path:
    """Create a clean results directory for a scenario."""
    results_dir = scenario_dir / "results"
    if results_dir.exists():
        shutil.rmtree(results_dir)
    results_dir.mkdir(parents=True)
    return results_dir


def run_scenario(
    scenario_dir: Path, config: Config, console: Console
) -> dict:
    """Run a single scenario and capture all output."""
    task_path = scenario_dir / "task.yaml"
    task = Task.from_yaml(task_path)
    results_dir = setup_results_dir(scenario_dir)

    title = SCENARIO_TITLES.get(task.name, task.name)
    console.print(Panel(f"[bold magenta]{title}[/bold magenta]", border_style="magenta"))

    # Point workspace to the results directory
    config.workspace_dir = str(results_dir)

    start = time.time()
    result = run_task(task, config)
    duration = time.time() - start

    # Move artifacts from results/<task_name>/ up to results/
    task_workspace = results_dir / task.name
    if task_workspace.exists():
        for item in task_workspace.iterdir():
            dest = results_dir / item.name
            if dest.exists():
                if dest.is_dir():
                    shutil.rmtree(dest)
                else:
                    dest.unlink()
            shutil.move(str(item), str(dest))
        task_workspace.rmdir()

    return {
        "scenario": title,
        "task_name": task.name,
        "status": result.status.value,
        "attempts": result.num_attempts,
        "duration": round(duration, 1),
        "results_dir": str(results_dir),
    }


def main():
    parser = argparse.ArgumentParser(description="Run all blog showcase scenarios")
    parser.add_argument("--model", "-m", default=None, help="Override model ID")
    parser.add_argument(
        "--no-server", action="store_true", help="Skip server auto-start"
    )
    parser.add_argument("--port", "-p", type=int, default=8080, help="Server port")
    args = parser.parse_args()

    console = Console(record=True)

    console.print(
        Panel(
            "[bold]Multi-Agent MLX Software Factory[/bold]\n"
            "Blog Showcase: 3 Scenarios Demonstrating Self-Correcting Local AI Agents\n"
            "Zero API keys | 100% local | $0 cost",
            title="Blog Showcase Runner",
            border_style="blue",
        )
    )

    # Config
    config = Config()
    config.server.port = args.port
    if args.model:
        config.server.model = args.model

    console.print(f"\n[dim]Model: {config.server.model}[/dim]")
    console.print(f"[dim]Server: {config.server.host}:{config.server.port}[/dim]\n")

    # Start server if needed
    proc = None
    if not args.no_server:
        if not health_check(config.server.host, config.server.port):
            proc = start_server(config.server)
        else:
            console.print("[green]Server already running.[/green]\n")

    total_start = time.time()
    results = []

    try:
        for scenario_dir in SCENARIO_DIRS:
            if not (scenario_dir / "task.yaml").exists():
                console.print(f"[yellow]Skipping {scenario_dir.name}: no task.yaml[/yellow]")
                continue
            r = run_scenario(scenario_dir, config, console)
            results.append(r)
            console.print()  # blank line between scenarios
    finally:
        if proc:
            stop_server(proc)

    total_duration = time.time() - total_start

    # Final cross-scenario summary
    console.print(Panel("[bold]Cross-Scenario Summary[/bold]", border_style="green"))

    table = Table(title="All Scenarios")
    table.add_column("Scenario", style="cyan", max_width=50)
    table.add_column("Status", style="bold")
    table.add_column("Attempts", style="yellow")
    table.add_column("Duration", style="green")

    for r in results:
        status_style = "green" if r["status"] == "success" else "red"
        table.add_row(
            r["scenario"],
            f"[{status_style}]{r['status']}[/{status_style}]",
            str(r["attempts"]),
            f"{r['duration']}s",
        )

    console.print(table)
    console.print(f"\n[bold]Total time: {total_duration:.1f}s[/bold]")
    console.print(f"[bold]Cost: $0.00[/bold] (fully local)")

    # Save the full console log
    log_text = console.export_text()
    log_path = SCENARIOS_DIR / "full_run.log"
    log_path.write_text(log_text)
    console.print(f"\n[dim]Full log saved to: {log_path}[/dim]")

    # Save cross-scenario summary
    summary = {
        "model": config.server.model,
        "total_duration_seconds": round(total_duration, 2),
        "total_cost": "$0.00",
        "scenarios": results,
    }
    summary_path = SCENARIOS_DIR / "run_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))
    console.print(f"[dim]Summary saved to: {summary_path}[/dim]")


if __name__ == "__main__":
    main()
