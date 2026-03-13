# Multi-Agent MLX Software Factory

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19002113.svg)](https://doi.org/10.5281/zenodo.19002113)

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

**Blog post:** [Two AI Agents, One MacBook, Zero API Keys](https://namangoyal.com/blog/2026/multi-agent-factory/) — interactive demo, scenario walkthroughs, and design lessons learned.

## What is this?

Two AI agents sit on your MacBook. One writes code, the other runs it and tells the first what broke. They go back and forth until the code works — or until a hard limit stops them.

The whole thing runs locally on Apple Silicon using a single [MLX](https://github.com/ml-explore/mlx) inference server. No API keys, no cloud, no data leaves your machine. I built it to see whether two small local models could actually collaborate the way cloud-based agents do with GPT-4. The short answer is yes — with some interesting caveats about what 7B models can and can't self-correct.

Here's what it looks like in practice:

| Scenario | What it does | Attempts | Time |
|----------|-------------|:--------:|:----:|
| Calendar generation | Format March 2026 without the `calendar` module | 1 | 22s |
| CSV analytics pipeline | Generate 200 rows, compute revenue, format as `$12,345.67` | 3 | 159s |
| Neural net from scratch | Train a 2-layer MLP with manual backprop (numpy only) | 2 | 50s |

Total wall time: 3 min 50 sec. Total cost: $0.00.

## Quick start

You need macOS with Apple Silicon, Python 3.12+, and [uv](https://github.com/astral-sh/uv).

```bash
git clone https://github.com/thenamangoyal/multi-agent-mlx.git
cd multi-agent-mlx
uv sync

# Start the local MLX server (downloads ~4 GB model on first run)
uv run factory server start

# In another terminal, give it a task
uv run factory run "Write a Python script that prints the first 20 Fibonacci numbers"
```

Or skip the server management — `factory run` auto-starts and auto-stops it:

```bash
uv run factory run "Write a script that trains a simple MLP on MNIST using MLX"
```

Stop the server when you're done (`~4 GB` RAM):

```bash
uv run factory server stop
```

## How it's structured

```
src/factory/
├── cli.py              # Typer CLI (factory run, factory server start/stop)
├── config.py           # All defaults in one dataclass
├── models.py           # Task, ExecutionResult, RunResult
├── orchestrator.py     # The Coder → execute → Sheriff loop
├── server.py           # MLX server lifecycle
├── agents/
│   ├── base.py         # Agno + OpenAILike pointed at localhost
│   ├── coder.py        # "Write code for this task"
│   └── sheriff.py      # "Here's what happened when I ran it"
└── tools/
    ├── file_io.py      # Sandboxed file read/write
    └── executor.py     # subprocess.run with timeout + output capture
```

The important files if you want to change behavior:

- **`orchestrator.py`** — the main loop. This is where the Coder and Sheriff take turns, where stagnation detection lives, and where the retry logic happens. Start here.
- **`agents/coder.py`** and **`agents/sheriff.py`** — the system prompts that define each agent's personality. Change these to tweak how they write or review code.
- **`config.py`** — `max_attempts`, `execution_timeout`, `stagnation_threshold`, token budgets. All the knobs.
- **`tools/executor.py`** — how scripts get executed in a sandboxed subprocess.

Run the tests with:

```bash
uv run pytest -v
```

---

## How it works

### One server, two personas

Both agents share a single `mlx_lm.server` instance. They're just two different system prompts hitting the same local OpenAI-compatible endpoint. A Python orchestrator — not an LLM — drives the coordination.

This is the key design constraint for 16 GB machines. Running two separate 7B models would blow past memory. One model loaded once, two identities, sequential turns.

```
                    writes code
      Coder   ───────────────────►   Sheriff
    (Agent A)                       (Agent B)
              ◄───────────────────
                  error report /
                   fix requests

              both hit the same
              mlx_lm.server on
              localhost:8080
```

**Why the orchestrator executes code directly:** Small quantized models (4-bit 7B) are unreliable at tool calling — they often dump code in markdown instead of invoking tools. So the orchestrator handles the mechanical part (extraction, execution), and the LLMs focus on what they're actually good at: generating code and analyzing errors.

### The feedback loop

Each iteration of the loop:

1. **Coder turn** — receives the task (plus the Sheriff's error report on retries) and writes a Python script.
2. **Execution** — the orchestrator (not an LLM) runs the script in a sandboxed subprocess with a timeout, capturing stdout, stderr, and the exit code.
3. **Sheriff turn** — reads the script and execution output, returns a PASS/FAIL verdict with analysis and a suggested fix.

If the Sheriff says PASS, the loop ends. If FAIL, the error report goes back to step 1.

### Bounded autonomy

Three safety layers prevent runaway loops:

1. **Hard limits:** `max_attempts=5`, `execution_timeout=60s`, `llm_timeout=120s`
2. **Stagnation detection:** Hashes the last 5 lines of each error. If the same error appears 3 times in a row, the system knows the Coder is stuck and stops.
3. **Token budget:** Hard cap (default 50K) on total tokens across all turns.

### Memory budget (16 GB M1 Pro)

| Component | RAM |
|-----------|-----|
| macOS + system | ~3–4 GB |
| Qwen2.5-Coder-7B-4bit | ~4 GB |
| KV cache (2048 prompt) | ~1–2 GB |
| Python + sandbox | ~0.5 GB |
| **Total** | **~9–10 GB** |

That leaves 6–7 GB of headroom on a 16 GB machine.

## Configuration

Override defaults with CLI flags or a `factory.yaml` in the project root:

```yaml
server:
  model: mlx-community/Qwen2.5-Coder-7B-Instruct-4bit
  host: 127.0.0.1
  port: 8080

agent:
  max_attempts: 5
  execution_timeout: 60
  llm_timeout: 120
  max_tokens_per_turn: 8192
  total_token_budget: 100000
  temperature: 0.0
  stagnation_threshold: 3
```

### CLI

```
factory run [DESCRIPTION]
  --task, -t PATH          Task YAML file
  --model, -m TEXT         Override model (HuggingFace ID)
  --max-attempts, -n INT   Max Coder↔Sheriff cycles
  --timeout INT            Execution timeout per script (seconds)
  --no-server              Skip auto-starting server

factory server start       Start MLX server
factory server status      Check if running
factory server stop        Stop the server
```

### Task files

```yaml
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

### Models

Any `mlx_lm.server`-compatible model works. These are pre-trained checkpoints from HuggingFace — no fine-tuning needed.

| Model | RAM | Notes |
|-------|-----|-------|
| **Qwen2.5-Coder-7B-Instruct-4bit** | ~4 GB | Default, best for 16 GB |
| Qwen2.5-Coder-1.5B-4bit | ~1 GB | Fast but less capable |
| Qwen2.5-Coder-14B-Instruct-4bit | ~8 GB | Better quality, needs 32 GB+ |
| Qwen2.5-Coder-32B-8bit | ~18 GB | Best quality, needs 64 GB+ |

```bash
uv run factory run --model mlx-community/Qwen2.5-Coder-1.5B-4bit "Write hello world"
```

## Tech stack

[MLX](https://github.com/ml-explore/mlx) and [mlx-lm](https://github.com/ml-explore/mlx-lm) for inference, [Agno](https://github.com/agno-agi/agno) for agent orchestration, [Typer](https://typer.tiangolo.com/) for the CLI, [Rich](https://rich.readthedocs.io/) for terminal output, [Pydantic](https://docs.pydantic.dev/) for validation, [uv](https://github.com/astral-sh/uv) for package management.

## License

MIT
