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
- Orchestrator handles script execution directly (small models unreliably call tools)
- Coder generates code (via tools or markdown fallback extraction)
- Sheriff analyzes execution results (stdout/stderr/exit code fed into its prompt)
- Bounded autonomy: max attempts, stagnation detection, token budget

## Server Lifecycle
- The MLX server uses ~4 GB RAM. Always stop it after completing tasks: `pkill -f "mlx_lm.server"`
- Before running scenarios or tasks, check if server is up: `curl -s http://127.0.0.1:8080/v1/models`
- If server is down, start it: `uv run factory server start` or `python -m mlx_lm server --model mlx-community/Qwen2.5-Coder-7B-Instruct-4bit --port 8080`
- After all scenario runs and commits are done, stop the server to free RAM
- Never leave the server running between conversations

## Conventions
- uv package manager, pyproject.toml
- src/factory/ layout with hatchling build
- Dataclass config, Pydantic models
- Agno framework with OpenAILike for local server
- Always commit and push only after verification (tests pass, runs succeed)
- Show intermediate outputs during long-running tasks — don't go silent
- Monitor scenario runs actively; if 2-3 attempts fail with the same error, intervene (simplify task or add hints) rather than exhausting all attempts
