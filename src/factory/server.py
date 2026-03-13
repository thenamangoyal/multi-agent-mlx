"""MLX server lifecycle management."""

from __future__ import annotations

import signal
import subprocess
import sys
import time

import httpx
from rich.console import Console

from factory.config import ServerConfig

console = Console()


def health_check(host: str, port: int, timeout: float = 5.0) -> bool:
    """Check if the mlx_lm server is responding."""
    try:
        r = httpx.get(f"http://{host}:{port}/v1/models", timeout=timeout)
        return r.status_code == 200
    except (httpx.ConnectError, httpx.ReadTimeout):
        return False


def start_server(config: ServerConfig) -> subprocess.Popen:
    """Start mlx_lm.server as a subprocess and wait until healthy."""
    if health_check(config.host, config.port):
        console.print(
            f"[green]Server already running on {config.host}:{config.port}[/green]"
        )
        return None  # type: ignore — caller checks for None

    console.print(
        f"[blue]Starting mlx_lm.server with model {config.model}...[/blue]"
    )

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "mlx_lm.server",
            "--model",
            config.model,
            "--host",
            config.host,
            "--port",
            str(config.port),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to become healthy
    max_wait = 120  # model download can take a while
    start = time.time()
    while time.time() - start < max_wait:
        if proc.poll() is not None:
            stderr = proc.stderr.read().decode() if proc.stderr else ""
            console.print(f"[red]Server exited unexpectedly:[/red]\n{stderr}")
            raise RuntimeError("mlx_lm.server failed to start")
        if health_check(config.host, config.port, timeout=2.0):
            console.print("[green]Server is ready.[/green]")
            return proc
        time.sleep(2)

    stop_server(proc)
    raise TimeoutError(
        f"Server did not become healthy within {max_wait}s. "
        "Model may still be downloading — try again."
    )


def stop_server(proc: subprocess.Popen | None) -> None:
    """Gracefully stop the server subprocess."""
    if proc is None or proc.poll() is not None:
        return
    console.print("[blue]Stopping server...[/blue]")
    proc.send_signal(signal.SIGTERM)
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
    console.print("[green]Server stopped.[/green]")
