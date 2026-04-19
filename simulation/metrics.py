# simulation/metrics.py
"""
Performance metrics collection for cafeteria simulation runs.

GameStats tracks everything during a simulation and computes derived
metrics (avg wait time, loss rate, profit, throughput, efficiency score)
once the run is finished.
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class GameStats:
    """Collects all performance metrics during one simulation run."""

    # ── Counters ──────────────────────────────────────────────────────
    customers_arrived: int = 0
    customers_served: int = 0
    customers_lost: int = 0

    # ── Timing ────────────────────────────────────────────────────────
    # Sum of (serve_time − arrival_time) for every served customer.
    total_wait_time: float = 0.0

    # ── Financial ─────────────────────────────────────────────────────
    total_revenue: float = 0.0
    total_ingredient_cost: float = 0.0

    # ── Per-dish breakdown ────────────────────────────────────────────
    dishes_cooked: Dict[str, int] = field(default_factory=lambda: {
        "Fried Rice": 0, "Chicken Rice": 0, "Omelet": 0
    })

    # ── Derived metrics (computed by finalize) ────────────────────────
    avg_wait_time: float = 0.0
    service_rate: float = 0.0       # customers served per second
    loss_rate: float = 0.0          # fraction of customers lost
    profit: float = 0.0             # revenue − ingredient cost
    throughput: float = 0.0         # dishes per minute

    def finalize(self, sim_duration: float) -> None:
        """Compute all derived metrics.  Call once at the end of a run.

        Args:
            sim_duration: Total simulation time in seconds.
        """
        # Average wait time
        if self.customers_served > 0:
            self.avg_wait_time = self.total_wait_time / self.customers_served
        else:
            self.avg_wait_time = 0.0

        # Service rate (customers / second)
        if sim_duration > 0:
            self.service_rate = self.customers_served / sim_duration
        else:
            self.service_rate = 0.0

        # Loss rate (fraction)
        if self.customers_arrived > 0:
            self.loss_rate = self.customers_lost / self.customers_arrived
        else:
            self.loss_rate = 0.0

        # Profit
        self.profit = self.total_revenue - self.total_ingredient_cost

        # Throughput (dishes per minute)
        total_dishes = sum(self.dishes_cooked.values())
        if sim_duration > 0:
            self.throughput = total_dishes / (sim_duration / 60.0)
        else:
            self.throughput = 0.0

    def to_dict(self) -> dict:
        """Return a flat dictionary suitable for a pandas DataFrame row."""
        return {
            "customers_arrived": self.customers_arrived,
            "customers_served": self.customers_served,
            "customers_lost": self.customers_lost,
            "total_wait_time": round(self.total_wait_time, 2),
            "total_revenue": round(self.total_revenue, 2),
            "total_ingredient_cost": round(self.total_ingredient_cost, 2),
            "avg_wait_time": round(self.avg_wait_time, 2),
            "service_rate": round(self.service_rate, 4),
            "loss_rate": round(self.loss_rate, 4),
            "profit": round(self.profit, 2),
            "throughput": round(self.throughput, 2),
        }
