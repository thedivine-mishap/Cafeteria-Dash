# simulation/experiment.py
"""
Grid-search experiment framework.

Generates all combinations of (num_queues, num_stoves, arrival_rate,
initial_ingredients), runs each configuration multiple times via the
visual Pygame simulator, and collects results into a DataFrame.

Usage:
    python -m simulation.experiment
"""

import itertools
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
import pandas as pd

from settings import SimConfig
from simulation.simulator import CafeteriaSimulator
from simulation.analysis import (
    add_efficiency_scores,
    find_best_config,
    print_summary_table,
    plot_results,
)


# ── Default parameter grid ────────────────────────────────────────────
PARAM_GRID = {
    "num_queues": [1, 2],
    "num_stoves": [2, 4],
    "arrival_rate": [0.08, 0.1],
    "initial_ingredients": [
        {"Rice": 3, "Egg": 3, "Veggie": 3, "Chicken": 3},     # low
        {"Rice": 10, "Egg": 10, "Veggie": 10, "Chicken": 10},  # high
    ],
}

RUNS_PER_CONFIG = 2        # repeat each config to average out randomness
SIM_DURATION = 150.0       # 5 minutes of game-time per run


def build_configs(grid: dict) -> list[SimConfig]:
    """Expand the parameter grid into a list of SimConfig objects."""
    keys = list(grid.keys())
    values = [grid[k] for k in keys]

    configs = []
    for combo in itertools.product(*values):
        kwargs = dict(zip(keys, combo))
        kwargs["sim_duration"] = SIM_DURATION
        configs.append(SimConfig(**kwargs))
    return configs


def run_experiments(
    grid: dict | None = None,
    runs_per_config: int = RUNS_PER_CONFIG,
) -> pd.DataFrame:
    """Run all experiments and return a results DataFrame."""
    if grid is None:
        grid = PARAM_GRID

    configs = build_configs(grid)
    total_configs = len(configs)
    total_runs = total_configs * runs_per_config
    print(f"\n{'='*60}")
    print(f"  Cafeteria Simulation Experiment")
    print(f"  {total_configs} configurations x {runs_per_config} runs = {total_runs} simulations")
    print(f"{'='*60}\n")

    rows = []

    # Initialize Pygame once — reuse across all runs
    pygame.init()
    info = pygame.display.Info()
    # Use borderless windowed so OS screenshot tools and overlays function normally
    screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.NOFRAME)
    clock = pygame.time.Clock()

    run_counter = 0
    for ci, config in enumerate(configs):
        for ri in range(runs_per_config):
            run_counter += 1
            print(
                f"  [{run_counter}/{total_runs}]  "
                f"Q={config.num_queues}  S={config.num_stoves}  "
                f"rate={config.arrival_rate}  "
                f"Ingr={sum(config.initial_ingredients.values())}  "
                f"(run {ri+1}/{runs_per_config})"
            )

            sim = CafeteriaSimulator(
                config,
                run_index=ri + 1,
                total_runs=runs_per_config,
                screen=screen,
                clock=clock,
            )
            stats = sim.run()

            # Build row
            row = {
                "config_id": ci,
                "run": ri + 1,
                "num_queues": config.num_queues,
                "num_stoves": config.num_stoves,
                "arrival_rate": config.arrival_rate,
                "initial_stock": sum(config.initial_ingredients.values()),
            }
            row.update(stats.to_dict())
            rows.append(row)

    pygame.quit()

    df = pd.DataFrame(rows)
    return df


# ── CLI entry point ──────────────────────────────────────────────────

def main():
    start = time.time()
    df = run_experiments()
    elapsed = time.time() - start
    print(f"\n  Completed in {elapsed:.1f}s\n")

    # Analysis
    df = add_efficiency_scores(df)
    print_summary_table(df)
    best = find_best_config(df)

    print("\n" + "=" * 60)
    print("  BEST CONFIGURATION")
    print("=" * 60)
    for k, v in best.items():
        print(f"    {k}: {v}")
    print()

    # Save raw data
    out_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "experiment_results.csv",
    )
    df.to_csv(out_path, index=False)
    print(f"  Raw data saved to {out_path}")

    # Plots (blocks until user closes window)
    plot_results(df)


if __name__ == "__main__":
    main()
