# Blog Showcase Scenarios

Three scenarios demonstrating the self-correcting multi-agent loop, designed to be run live and captured for blog presentation.

## The Narrative Arc

The scenarios build in complexity, each showcasing a different strength:

### Scenario 1: The Off-by-One Gauntlet
**Domain:** Pure algorithm (calendar generation)
**Strength:** Self-correcting loop catches *logical errors*, not just crashes

The Coder must generate a formatted calendar for March 2026 without using Python's `calendar` module. This requires computing day-of-week offsets correctly — a classic source of off-by-one bugs. The Sheriff validates the output against the expected format and catches when the weekday/weekend counts don't add up.

**Blog takeaway:** Local agents fix logic bugs, not just syntax errors.

### Scenario 2: The CSV Detective
**Domain:** Data pipeline (generate → persist → read → analyze)
**Strength:** Agents handle multi-step file I/O within sandboxed workspaces

The Coder builds a complete data analysis pipeline: generate 200 rows of synthetic sales data to CSV, read it back, compute revenue breakdowns, and print a formatted report with proper currency formatting (`$12,345.67`). The currency formatting spec (`{:,.2f}`) is notoriously tricky for small models.

**Blog takeaway:** Local agents orchestrate real-world data workflows.

### Scenario 3: Gradient Descent from Scratch
**Domain:** ML math (manual backpropagation)
**Strength:** The system's ceiling — iteratively debugging matrix calculus

The Coder implements a 2-layer neural network with manual backpropagation using only numpy. Shape mismatches, wrong gradient formulas, and numerical instability create a gauntlet of errors. Watching a 4-bit 7B model fix its own chain rule math across multiple iterations is the "wow" moment.

**Blog takeaway:** A $0 local system can debug linear algebra and calculus.

## Running

```bash
# From the project root — runs all 3 scenarios with auto server management
uv run python scenarios/run_all.py

# If you already have a server running
uv run python scenarios/run_all.py --no-server

# Use a smaller/faster model
uv run python scenarios/run_all.py --model mlx-community/Qwen2.5-Coder-1.5B-4bit
```

## Output

After running, each scenario directory contains a `results/` folder:

```
scenario_1_calendar/results/
├── attempt_1/
│   ├── script.py           # Code from first attempt
│   └── sheriff_report.txt  # Sheriff's error analysis
├── attempt_2/
│   ├── script.py           # Fixed code
│   └── sheriff_report.txt  # Sheriff's PASS verdict
├── script.py               # Final working script
└── summary.json            # Status, timing, final output
```

Cross-scenario results are saved to:
- `scenarios/full_run.log` — complete console output
- `scenarios/run_summary.json` — machine-readable summary with timing and status

## Cost Comparison

| Setup | Cost for 3 scenarios | Privacy |
|-------|---------------------:|---------|
| GPT-4 API (~15 agent turns) | ~$1.50–3.00 | Data sent to cloud |
| Claude API (~15 agent turns) | ~$0.75–1.50 | Data sent to cloud |
| **This project (local MLX)** | **$0.00** | **100% on-device** |
