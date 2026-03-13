# Multi-Agent MLX Software Factory

## Project
Local multi-agent system on Apple Silicon. Two SLM agents (Coder + Sheriff) collaborate via a shared mlx_lm.server to write and debug Python scripts autonomously.

## Commands
- `uv run factory run "task description"` — run the full agent loop
- `uv run factory server start` — start MLX server
- `uv run pytest` — run tests

## Architecture
- Single mlx_lm.server instance, both agents share it as two system-prompt personas
- Orchestrator (Python, not LLM) drives the Coder→Sheriff feedback loop
- Bounded autonomy: max attempts, stagnation detection, token budget

## Conventions
- uv package manager, pyproject.toml
- src/factory/ layout with hatchling build
- Dataclass config, Pydantic models
- Agno framework with OpenAILike for local server
