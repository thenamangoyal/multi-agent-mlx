#!/usr/bin/env python3
"""Generate blog-quality visualizations from scenario outputs.

Run after scenarios complete:
    uv run python scenarios/generate_visuals.py
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

SCENARIOS_DIR = Path(__file__).parent
OUTPUT_DIR = SCENARIOS_DIR / "visuals"
OUTPUT_DIR.mkdir(exist_ok=True)

plt.rcParams.update({
    "figure.facecolor": "#1a1a2e",
    "axes.facecolor": "#16213e",
    "axes.edgecolor": "#e94560",
    "axes.labelcolor": "#eee",
    "text.color": "#eee",
    "xtick.color": "#aaa",
    "ytick.color": "#aaa",
    "grid.color": "#333",
    "font.size": 12,
})


def plot_decision_boundary():
    """Plot the learned decision boundary from Scenario 3."""
    npz_path = SCENARIOS_DIR / "scenario_3_neural_net" / "results" / "model_data.npz"
    if not npz_path.exists():
        print(f"Skipping decision boundary: {npz_path} not found")
        return

    data = np.load(npz_path)
    X, y, W, b = data["X"], data["y"].ravel(), data["W"], data["b"]

    fig, ax = plt.subplots(figsize=(8, 6))

    # Create mesh grid for decision boundary
    x_min, x_max = X[:, 0].min() - 0.5, X[:, 0].max() + 0.5
    y_min, y_max = X[:, 1].min() - 0.5, X[:, 1].max() + 0.5
    xx, yy = np.meshgrid(np.linspace(x_min, x_max, 200),
                         np.linspace(y_min, y_max, 200))
    grid = np.c_[xx.ravel(), yy.ravel()]

    # Forward pass on grid
    Z = grid @ W + b
    A = 1 / (1 + np.exp(-Z))
    A = A.reshape(xx.shape)

    # Contour fill
    ax.contourf(xx, yy, A, levels=np.linspace(0, 1, 50), cmap="RdYlBu_r", alpha=0.8)
    ax.contour(xx, yy, A, levels=[0.5], colors=["#e94560"], linewidths=2)

    # Scatter data points
    colors = ["#0f3460" if yi == 0 else "#e94560" for yi in y]
    ax.scatter(X[:, 0], X[:, 1], c=colors, edgecolors="white", s=30, linewidths=0.5, zorder=5)

    ax.set_title("Decision Boundary — Agent-Written Neural Network", fontsize=14, fontweight="bold")
    ax.set_xlabel("Feature 1")
    ax.set_ylabel("Feature 2")

    out = OUTPUT_DIR / "decision_boundary.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")


def plot_revenue_chart():
    """Plot revenue by product from Scenario 2's CSV data."""
    import csv

    csv_path = SCENARIOS_DIR / "scenario_2_csv" / "results" / "sales_data.csv"
    if not csv_path.exists():
        print(f"Skipping revenue chart: {csv_path} not found")
        return

    revenue_by_product = {}
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            product = row["product"]
            revenue = int(row["units"]) * float(row["price_per_unit"])
            revenue_by_product[product] = revenue_by_product.get(product, 0) + revenue

    products = sorted(revenue_by_product, key=revenue_by_product.get, reverse=True)
    revenues = [revenue_by_product[p] for p in products]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(products, revenues, color=["#e94560", "#0f3460", "#533483"],
                  edgecolor="white", linewidth=0.5)

    for bar, rev in zip(bars, revenues):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 500,
                f"${rev:,.0f}", ha="center", va="bottom", fontsize=11, fontweight="bold")

    ax.set_title("Revenue by Product — Agent-Generated Analysis", fontsize=14, fontweight="bold")
    ax.set_ylabel("Total Revenue ($)")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax.grid(axis="y", alpha=0.3)

    out = OUTPUT_DIR / "revenue_by_product.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")


def plot_scenario_summary():
    """Plot cross-scenario comparison chart."""
    import json

    summary_path = SCENARIOS_DIR / "run_summary.json"
    if not summary_path.exists():
        print(f"Skipping summary chart: {summary_path} not found")
        return

    summary = json.loads(summary_path.read_text())
    scenarios = summary["scenarios"]

    names = [s["task_name"].replace("-", "\n") for s in scenarios]
    durations = [s["duration"] for s in scenarios]
    attempts = [s["attempts"] for s in scenarios]
    statuses = [s["status"] for s in scenarios]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Duration bar chart
    colors = ["#27ae60" if s == "success" else "#e94560" for s in statuses]
    ax1.barh(names, durations, color=colors, edgecolor="white", linewidth=0.5)
    ax1.set_xlabel("Duration (seconds)")
    ax1.set_title("Time per Scenario", fontsize=13, fontweight="bold")
    for i, (d, a) in enumerate(zip(durations, attempts)):
        ax1.text(d + 1, i, f"{d:.0f}s ({a} attempt{'s' if a > 1 else ''})",
                 va="center", fontsize=10)

    # Attempts chart
    ax2.bar(range(len(names)), attempts, color=["#0f3460", "#533483", "#e94560"],
            edgecolor="white", linewidth=0.5)
    ax2.set_xticks(range(len(names)))
    ax2.set_xticklabels(names, fontsize=9)
    ax2.set_ylabel("Number of Attempts")
    ax2.set_title("Self-Correction Attempts", fontsize=13, fontweight="bold")
    ax2.set_ylim(0, max(attempts) + 1)

    fig.suptitle(f"Multi-Agent Factory — All Scenarios ($0.00 cost, {summary['total_duration_seconds']:.0f}s total)",
                 fontsize=14, fontweight="bold", y=1.02)
    fig.tight_layout()

    out = OUTPUT_DIR / "scenario_summary.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")


if __name__ == "__main__":
    print("Generating blog visuals...")
    plot_decision_boundary()
    plot_revenue_chart()
    plot_scenario_summary()
    print(f"\nAll visuals saved to: {OUTPUT_DIR}/")
