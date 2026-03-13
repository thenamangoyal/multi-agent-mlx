# Multi-Agent MLX Software Factory

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19002113.svg)](https://doi.org/10.5281/zenodo.19002113)

A fully local, zero-API-key multi-agent system where two AI agents collaborate to write and debug Python scripts — running entirely on Apple Silicon using [MLX](https://github.com/ml-explore/mlx).

**Blog post:** [Two AI Agents, One MacBook, Zero API Keys](https://namangoyal.com/blog/2026/multi-agent-factory/) — interactive simulation, real scenario walkthroughs, and design lessons.

**Agent A (Coder)** writes Python scripts. **Agent B (Sheriff)** executes them, reads the terminal stack traces, and forces the Coder to fix its bugs. The loop continues until the code works or bounded autonomy limits kick in.

Cloud APIs for AI agents cost ~$0.10+ every time agents get stuck in a thought loop. This system costs $0, runs offline, and keeps your code 100% private.

## Architecture

### Single Server, Two Personas

The critical design decision for 16GB Apple Silicon: both agents share a **single `mlx_lm.server` instance** serving one pre-trained model. They are two system-prompt identities hitting the same local OpenAI-compatible endpoint, taking sequential turns. A Python orchestrator (not an LLM) drives the coordination.

```
User Task Description
        │
        ▼
  ┌─────────────┐                    ┌──────────────┐
  │  Coder       │   writes code      │  Sheriff      │
  │  (Agent A)   │ ────────────────►  │  (Agent B)    │
  │              │                    │               │
  │  System:     │                    │  System:      │
  │  "Write code"│  error report /    │  "Run & test" │
  │              │ ◄──────────────── │               │
  └─────────────┘    fix requests     └──────────────┘
        │                                   │
        └──────── same mlx_lm.server ──────┘
                  localhost:8080
                  (one model, two personas)
```

This is a **coordinator pattern** — the orchestrator asks the Coder to generate code, runs it in a sandboxed subprocess, then feeds the execution results to the Sheriff for analysis. If the Sheriff reports failure, the error report goes back to the Coder. No free-form multi-agent chat, no model swapping.

**Why the orchestrator executes directly:** Small quantized models (4-bit 7B) are unreliable at tool calling — they often output code in markdown instead of invoking tools. The orchestrator handles the mechanical execution step, while the LLMs focus on what they're good at: the Coder *generates* code, the Sheriff *analyzes* results and suggests fixes.

### Memory Budget (16GB M1 Pro)

| Component | RAM | Notes |
|-----------|-----|-------|
| macOS + system | ~3–4 GB | Baseline overhead |
| Qwen2.5-Coder-7B-4bit | ~4 GB | Single model loaded once |
| KV cache | ~1–2 GB | 2048 prompt cache |
| Python + subprocess sandbox | ~0.5 GB | Agent code + executed scripts |
| **Total** | **~9–10 GB** | **6–7 GB headroom on 16 GB** |

Running two separate 7B models would blow past 16 GB. The single-server-two-persona approach is what makes this viable on consumer hardware.

## The Self-Correcting Feedback Loop

This is the core innovation. Most coding agents generate and hope. This one generates, tests, reads errors, and iterates:

```
ORCHESTRATOR LOOP (max N iterations, default 5):

  1. CODER TURN (LLM call)
     Input: task description + (if retry) Sheriff's error report
     Output: Python script (via tool call or markdown code block extraction)

  2. EXECUTION (orchestrator, not LLM)
     Runs `python script.py` in sandboxed subprocess with timeout
     Captures stdout, stderr, exit code

  3. SHERIFF TURN (LLM call)
     Input: script content + stdout + stderr + exit code
     Output: VERDICT (PASS/FAIL) + analysis + suggested fix

     → PASS: loop ends ✓
     → FAIL: error report → back to step 1

  3. BOOKKEEPING
     Track attempts, detect stagnation, enforce token budget
```

### Error Report Format (Sheriff → Coder)

The Sheriff produces structured reports so the Coder gets actionable context:

```
VERDICT: FAIL
## Error Type: ImportError
## Traceback:
  File "script.py", line 3, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'
## Analysis: The script imports PyTorch but only MLX is available locally.
## Suggested Fix: Replace torch imports with mlx equivalents.
```

## Bounded Autonomy

Three layers prevent agents from getting stuck in infinite loops:

1. **Hard limits** (configurable): `max_attempts=5`, `execution_timeout=60s`, `llm_timeout=120s`
2. **Stagnation detection**: Hashes the last 5 lines of each error traceback. If the same hash appears 3 times consecutively, the system injects a meta-prompt ("you've been producing the same error") and hard-stops after one more failure
3. **Token budget**: Tracks total tokens across all turns with a hard cap (default 50K tokens) to prevent runaway context accumulation

## Quick Start

### Prerequisites

- macOS with Apple Silicon (M1/M2/M3/M4)
- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager

### Install

```bash
git clone https://github.com/thenamangoyal/multi-agent-mlx.git
cd multi-agent-mlx
uv sync
```

### Run (3 commands)

```bash
# 1. Start the local MLX server (auto-downloads model on first run, ~4 GB)
uv run factory server start

# 2. In another terminal, run a task
uv run factory run "Write a Python script that prints the first 20 Fibonacci numbers"

# 3. Or use a task file with constraints
uv run factory run --task examples/fibonacci.yaml
```

### All-in-one (auto-starts and stops server)

```bash
uv run factory run "Write a script that trains a simple MLP on MNIST using MLX"
```

## Supported Models

All models are **pre-trained checkpoints** downloaded as-is from HuggingFace. `mlx_lm.server` auto-downloads on first use — no fine-tuning, no adapters, no training required.

| Model | RAM | Use Case | HuggingFace ID |
|-------|-----|----------|----------------|
| **Qwen2.5-Coder-7B-Instruct-4bit** | ~4 GB | Default — best coding quality for 16 GB | `mlx-community/Qwen2.5-Coder-7B-Instruct-4bit` |
| Qwen2.5-Coder-1.5B-4bit | ~1 GB | Lightweight fallback, fast iteration | `mlx-community/Qwen2.5-Coder-1.5B-4bit` |
| Qwen2.5-Coder-14B-Instruct-4bit | ~8 GB | Higher quality for 32 GB+ Macs | `mlx-community/Qwen2.5-Coder-14B-Instruct-4bit` |
| Qwen2.5-Coder-32B-8bit | ~18 GB | Best quality for 64 GB+ Macs | `mlx-community/Qwen2.5-Coder-32B-8bit` |

Any model compatible with `mlx_lm.server` works — just pass `--model <hf-id>`:

```bash
uv run factory run --model mlx-community/Qwen2.5-Coder-1.5B-4bit "Write hello world"
```

## Configuration

Override defaults via CLI flags or a `factory.yaml` file in the project root:

```yaml
server:
  model: mlx-community/Qwen2.5-Coder-7B-Instruct-4bit
  host: 127.0.0.1
  port: 8080

agent:
  max_attempts: 5
  execution_timeout: 60    # seconds per script run
  llm_timeout: 120         # seconds per LLM call
  max_tokens_per_turn: 8192
  total_token_budget: 100000
  temperature: 0.0
  stagnation_threshold: 3  # same error N times → stop
```

### CLI Options

```
factory run [DESCRIPTION]
  --task, -t PATH          Task YAML file
  --model, -m TEXT         Override model (HuggingFace ID)
  --max-attempts, -n INT   Max Coder↔Sheriff cycles
  --timeout INT            Execution timeout per script (seconds)
  --config, -c PATH        Config YAML file
  --no-server              Skip auto-starting server (use existing)

factory server start       Start the MLX inference server
factory server status      Check if server is running
factory server stop        Stop the server
```

### Server Management

The MLX server consumes ~4 GB of RAM while running. You should stop it when not in use:

```bash
# Check if the server is running
uv run factory server status
# or: curl -s http://127.0.0.1:8080/v1/models

# Stop the server
uv run factory server stop
# or: pkill -f "mlx_lm.server"

# Check for any lingering processes
ps aux | grep mlx_lm.server | grep -v grep
```

The `factory run` command auto-starts and auto-stops the server by default. Use `--no-server` if you want to manage the server lifecycle manually.

### Task Files

Define reusable tasks as YAML:

```yaml
# examples/mnist_mlx.yaml
name: mnist-mlx
description: |
  Write a complete Python script that trains a 2-layer MLP on MNIST using MLX.
  Print training loss each epoch and final test accuracy.
constraints:
  - Use mlx and mlx.nn for the model
  - Must complete training in under 120 seconds
max_attempts: 5
timeout: 180
```

## Project Structure

```
multi-agent-mlx/
├── src/factory/
│   ├── cli.py              # Typer CLI entry point
│   ├── config.py           # Dataclass-based configuration
│   ├── models.py           # Task, ExecutionResult, RunResult models
│   ├── orchestrator.py     # Core Coder→Sheriff feedback loop
│   ├── server.py           # MLX server lifecycle (start/stop/health)
│   ├── agents/
│   │   ├── base.py         # Agno + OpenAILike wrapper for local server
│   │   ├── coder.py        # Coder agent (writes code)
│   │   └── sheriff.py      # Sheriff agent (executes + reviews)
│   └── tools/
│       ├── file_io.py      # Sandboxed write_file, read_file, list_files
│       └── executor.py     # Subprocess execution with timeout
├── tests/                  # 20 tests covering tools, executor, orchestrator
├── examples/               # fibonacci.yaml, mnist_mlx.yaml
└── workspace/output/       # Runtime output (gitignored)
```

## How It Works Under the Hood

### MLX Server as OpenAI-Compatible Endpoint

`mlx_lm.server` exposes `/v1/chat/completions` and `/v1/models` endpoints that mimic the OpenAI API. This means any framework that speaks the OpenAI protocol works out of the box — no custom inference code needed.

```bash
# This is all it takes to start serving a model
mlx_lm.server --model mlx-community/Qwen2.5-Coder-7B-Instruct-4bit
```

### Agno Framework for Agent Orchestration

Each agent is an [Agno](https://github.com/agno-agi/agno) `Agent` with `OpenAILike` pointed at localhost:

```python
from agno.agent import Agent
from agno.models.openai import OpenAILike

agent = Agent(
    model=OpenAILike(
        id="Qwen2.5-Coder-7B-Instruct-4bit",
        base_url="http://127.0.0.1:8080/v1",
        api_key="not-needed",  # local server, no auth
    ),
    instructions=["You are an expert Python developer..."],
    tools=[write_file, read_file],  # plain Python functions
)
```

Tools are plain Python functions — no decorators required. The Coder gets file I/O tools; the Sheriff gets code execution + file reading.

### Sandboxed Execution

The Sheriff runs scripts via `subprocess.run()` with:
- `cwd` locked to the task workspace directory
- Path validation prevents directory traversal attacks
- Configurable timeout kills runaway scripts
- stdout/stderr captured and truncated to last 100 lines

### Stagnation Detection

Error deduplication uses MD5 hashes of the last 5 lines of each traceback:

```python
def _error_hash(text: str) -> str:
    lines = text.strip().splitlines()[-5:]
    return hashlib.md5("\n".join(lines).encode()).hexdigest()
```

If the same hash appears `stagnation_threshold` times consecutively (default 3), the orchestrator knows the Coder is stuck and terminates the loop.

## Tech Stack

| Component | Role |
|-----------|------|
| [MLX](https://github.com/ml-explore/mlx) | Apple Silicon ML framework |
| [mlx-lm](https://github.com/ml-explore/mlx-lm) | Local OpenAI-compatible LLM server |
| [Agno](https://github.com/agno-agi/agno) | Agent framework with tool calling |
| [Typer](https://typer.tiangolo.com/) | CLI framework |
| [Rich](https://rich.readthedocs.io/) | Terminal formatting and tables |
| [Pydantic](https://docs.pydantic.dev/) | Data validation |
| [uv](https://github.com/astral-sh/uv) | Fast Python package manager |

## Development

```bash
# Install with dev dependencies
uv sync --group dev

# Run all 20 tests
uv run pytest -v

# Run a quick smoke test (requires running MLX server)
uv run factory server start &
uv run factory run --no-server --max-attempts 2 "Write a script that prints hello world"
```

## Cost Comparison

| Setup | Cost per agent loop | Privacy | Latency |
|-------|--------------------:|---------|---------|
| GPT-4 API | ~$0.10–0.50 | Data sent to cloud | Network-dependent |
| Claude API | ~$0.05–0.30 | Data sent to cloud | Network-dependent |
| **This project (local MLX)** | **$0.00** | **100% on-device** | **~1–5s per turn** |

When agents get stuck in 10+ iteration loops, cloud costs compound fast. Locally, it's just electricity.

## Citation

If you use this in your research, please cite:

```bibtex
@software{goyal2026two-ai-agents-one-macbook-zero-api-keys,
  title   = {Two AI Agents, One MacBook, Zero API Keys},
  author  = {Goyal, Naman},
  year    = {2026},
  month   = {Mar},
  doi     = {10.5281/zenodo.19002113},
  url     = {https://namangoyal.com/blog/2026/multi-agent-factory/}
}
```

## License

MIT
