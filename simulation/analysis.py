# simulation/analysis.py
"""
Analysis, scoring, and visualization for experiment results.

Provides:
  - Weighted composite efficiency score
  - Min-max normalization
  - Best-config finder
  - Summary table printer
  - 2×2 matplotlib plot
"""

import pandas as pd
import numpy as np


# ── Scoring ───────────────────────────────────────────────────────────

DEFAULT_WEIGHTS = {
    "profit": 0.35,
    "loss_rate_inv": 0.25,       # inverted: lower loss = better
    "avg_wait_inv": 0.25,        # inverted: lower wait = better
    "throughput": 0.15,
}


def _min_max(series: pd.Series) -> pd.Series:
    """Min-max normalize a Series to [0, 1]."""
    lo, hi = series.min(), series.max()
    if hi - lo == 0:
        return pd.Series(0.5, index=series.index)
    return (series - lo) / (hi - lo)


def add_efficiency_scores(
    df: pd.DataFrame,
    weights: dict | None = None,
) -> pd.DataFrame:
    """Add an 'efficiency_score' column to the DataFrame.

    Formula:
        score = w_profit     * norm(profit)
              + w_loss_inv   * norm(1 − loss_rate)
              + w_wait_inv   * norm(1 − avg_wait_time / max_wait)
              + w_throughput  * norm(throughput)
    """
    w = weights or DEFAULT_WEIGHTS
    df = df.copy()

    df["norm_profit"] = _min_max(df["profit"])
    df["norm_loss_inv"] = _min_max(1 - df["loss_rate"])
    df["norm_wait_inv"] = _min_max(
        1 - df["avg_wait_time"] / df["avg_wait_time"].max()
        if df["avg_wait_time"].max() > 0
        else df["avg_wait_time"]
    )
    df["norm_throughput"] = _min_max(df["throughput"])

    df["efficiency_score"] = (
        w["profit"] * df["norm_profit"]
        + w["loss_rate_inv"] * df["norm_loss_inv"]
        + w["avg_wait_inv"] * df["norm_wait_inv"]
        + w["throughput"] * df["norm_throughput"]
    )
    df["efficiency_score"] = df["efficiency_score"].round(4)
    return df


# ── Best config ───────────────────────────────────────────────────────

def find_best_config(df: pd.DataFrame) -> dict:
    """Return the config with the highest *average* efficiency score."""
    group_cols = ["num_queues", "num_stoves", "arrival_rate", "initial_stock"]
    grouped = (
        df.groupby(group_cols)
        .agg(
            avg_efficiency=("efficiency_score", "mean"),
            avg_profit=("profit", "mean"),
            avg_loss_rate=("loss_rate", "mean"),
            avg_wait=("avg_wait_time", "mean"),
            avg_throughput=("throughput", "mean"),
            avg_served=("customers_served", "mean"),
        )
        .reset_index()
        .sort_values("avg_efficiency", ascending=False)
    )
    best = grouped.iloc[0].to_dict()
    # Round for readability
    for k in best:
        if isinstance(best[k], float):
            best[k] = round(best[k], 4)
    return best


# ── Summary table ─────────────────────────────────────────────────────

def print_summary_table(df: pd.DataFrame) -> None:
    """Print a grouped summary table to the console."""
    group_cols = ["num_queues", "num_stoves", "arrival_rate", "initial_stock"]
    agg = (
        df.groupby(group_cols)
        .agg(
            profit_mean=("profit", "mean"),
            profit_std=("profit", "std"),
            loss_mean=("loss_rate", "mean"),
            wait_mean=("avg_wait_time", "mean"),
            served_mean=("customers_served", "mean"),
            score_mean=("efficiency_score", "mean"),
        )
        .reset_index()
        .sort_values("score_mean", ascending=False)
    )

    print("\n" + "=" * 100)
    print("  EXPERIMENT SUMMARY (sorted by efficiency score)")
    print("=" * 100)
    header = (
        f"{'Q':>3} {'S':>3} {'rate':>6} {'Stock':>6} | "
        f"{'Profit':>9} {'Loss%':>7} {'Wait(s)':>8} {'Served':>7} | "
        f"{'Score':>7}"
    )
    print(header)
    print("-" * 100)
    for _, r in agg.iterrows():
        line = (
            f"{int(r['num_queues']):>3} {int(r['num_stoves']):>3} "
            f"{r['arrival_rate']:>6.2f} {int(r['initial_stock']):>6} | "
            f"${r['profit_mean']:>8.1f} {r['loss_mean']*100:>6.1f}% "
            f"{r['wait_mean']:>8.1f} {r['served_mean']:>7.1f} | "
            f"{r['score_mean']:>7.4f}"
        )
        print(line)
    print()


# ── Visualization ─────────────────────────────────────────────────────

def plot_results(df: pd.DataFrame) -> None:
    """Generate a 2x2 matplotlib figure with key analysis charts."""
    try:
        import matplotlib
        matplotlib.use("TkAgg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("  [!] matplotlib not installed - skipping plots.")
        print("      Install with: pip install matplotlib")
        return

    group_cols = ["num_queues", "num_stoves", "arrival_rate", "initial_stock"]
    agg = (
        df.groupby(group_cols)
        .agg(
            profit=("profit", "mean"),
            loss_rate=("loss_rate", "mean"),
            avg_wait=("avg_wait_time", "mean"),
            throughput=("throughput", "mean"),
            score=("efficiency_score", "mean"),
        )
        .reset_index()
    )

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Cafeteria Simulation - Experiment Results", fontsize=16, fontweight="bold")

    # ── 1. Profit by (queues × stoves) ────────────────────────────────
    ax = axes[0, 0]
    pivot = agg.groupby(["num_queues", "num_stoves"])["profit"].mean().unstack()
    pivot.plot(kind="bar", ax=ax, colormap="viridis")
    ax.set_title("Avg Profit by Queues × Stoves")
    ax.set_xlabel("Number of Queues")
    ax.set_ylabel("Profit ($)")
    ax.legend(title="Stoves")
    ax.tick_params(axis='x', rotation=0)

    # ── 2. Loss rate heatmap ──────────────────────────────────────────
    ax = axes[0, 1]
    heat = agg.groupby(["num_queues", "num_stoves"])["loss_rate"].mean().unstack()
    im = ax.imshow(heat.values, cmap="RdYlGn_r", aspect="auto")
    ax.set_xticks(range(len(heat.columns)))
    ax.set_xticklabels(heat.columns)
    ax.set_yticks(range(len(heat.index)))
    ax.set_yticklabels(heat.index)
    ax.set_xlabel("Number of Stoves")
    ax.set_ylabel("Number of Queues")
    ax.set_title("Avg Loss Rate (lower = better)")
    fig.colorbar(im, ax=ax, label="Loss Rate")
    # Annotate cells
    for i in range(len(heat.index)):
        for j in range(len(heat.columns)):
            val = heat.values[i, j]
            ax.text(j, i, f"{val:.1%}", ha="center", va="center",
                    color="black", fontsize=9, fontweight="bold")

    # ── 3. Wait time vs stoves (one line per queue count) ─────────────
    ax = axes[1, 0]
    for nq in sorted(agg["num_queues"].unique()):
        sub = agg[agg["num_queues"] == nq].groupby("num_stoves")["avg_wait"].mean()
        ax.plot(sub.index, sub.values, marker="o", label=f"{nq} queue(s)")
    ax.set_title("Avg Wait Time vs. Stoves")
    ax.set_xlabel("Number of Stoves")
    ax.set_ylabel("Avg Wait Time (s)")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # ── 4. Top 10 configs by efficiency score ─────────────────────────
    ax = axes[1, 1]
    top = (
        agg.sort_values("score", ascending=False)
        .head(10)
        .reset_index(drop=True)
    )
    labels = [
        f"Q{int(r['num_queues'])} S{int(r['num_stoves'])}\n{r['arrival_rate']}"
        for _, r in top.iterrows()
    ]
    colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(top)))
    ax.barh(range(len(top)), top["score"], color=colors)
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("Efficiency Score")
    ax.set_title("Top 10 Configurations")
    ax.invert_yaxis()

    plt.tight_layout()
    plt.savefig(
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "experiment_plots.png"),
        dpi=150
    )
    print("  Plots saved to experiment_plots.png")
    plt.show()


# Needed for the save path in plot_results
import os
