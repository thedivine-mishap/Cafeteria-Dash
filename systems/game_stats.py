# systems/game_stats.py
"""
Performance tracking and strategy evaluation for interactive gameplay.

GameStats passively records every player decision and game event,
then produces feedback and a rating at the end of a session.
No automation — all actions are initiated by the player.
"""

from collections import defaultdict


class GameStats:
    """Tracks all performance metrics during one interactive game session."""

    def __init__(self):
        # ── Customer counters ─────────────────────────────────────────
        self.total_arrived = 0
        self.total_served = 0
        self.total_lost = 0

        # ── Wait-time tracking ────────────────────────────────────────
        self.total_wait_time = 0.0          # sum of served-customer wait times
        self._wait_times = []               # individual wait times (for analysis)

        # ── Financial tracking ────────────────────────────────────────
        self.total_revenue = 0.0
        self.total_spent_on_ingredients = 0.0
        self.total_spent_on_stoves = 0.0

        # ── Ingredient tracking ───────────────────────────────────────
        self.buy_counts = defaultdict(int)   # how many of each ingredient bought
        self.peak_stock = defaultdict(int)   # max stock reached per ingredient

        # ── Cooking tracking ──────────────────────────────────────────
        self.cook_counts = defaultdict(int)  # how many of each dish cooked
        self.dishes_served = defaultdict(int)  # how many of each dish served
        self.peak_concurrent_cooking = 0

        # ── Stove utilization snapshots ───────────────────────────────
        self._stove_busy_samples = 0
        self._stove_total_samples = 0

        # ── Queue tracking ────────────────────────────────────────────
        self.peak_queue_length = 0
        self._queue_length_sum = 0
        self._queue_snapshots = 0

        # ── Action counting (for actions-per-minute) ──────────────────
        self._total_actions = 0     # buy + cook + serve actions

        # ── Derived metrics (set by finalize) ─────────────────────────
        self.game_duration = 0.0
        self.avg_wait_time = 0.0
        self.serve_rate = 0.0
        self.loss_rate = 0.0
        self.profit = 0.0
        self.stove_utilization = 0.0
        self.avg_queue_length = 0.0
        self.actions_per_minute = 0.0
        self.efficiency_score = 0.0

    # ── Recording methods (called from main.py) ──────────────────────

    def record_customer_arrived(self):
        """Call when a new customer spawns into the queue."""
        self.total_arrived += 1

    def record_customer_served(self, wait_time, dish, revenue):
        """Call when a customer is successfully served.

        Args:
            wait_time: seconds the customer waited (game_elapsed - arrival_time)
            dish: name of the dish served
            revenue: money earned from serving
        """
        self.total_served += 1
        self.total_wait_time += wait_time
        self._wait_times.append(wait_time)
        self.total_revenue += revenue
        self.dishes_served[dish] += 1
        self._total_actions += 1

    def record_customer_lost(self):
        """Call when a customer leaves due to running out of patience."""
        self.total_lost += 1

    def record_ingredient_bought(self, ingredient, cost):
        """Call when a player buys an ingredient.

        Args:
            ingredient: name of the ingredient (e.g. "Rice")
            cost: how much it cost
        """
        self.buy_counts[ingredient] += 1
        self.total_spent_on_ingredients += cost
        self._total_actions += 1

    def record_stove_bought(self, cost):
        """Call when a player purchases an additional stove."""
        self.total_spent_on_stoves += cost
        self._total_actions += 1

    def record_cook_started(self, dish):
        """Call when a player starts cooking a dish."""
        self.cook_counts[dish] += 1
        self._total_actions += 1

    def record_cook_finished(self, dish):
        """Call when a dish finishes cooking (timer expires)."""
        pass  # tracked via cook_counts at start; here for completeness

    def record_queue_snapshot(self, queue_length):
        """Call every frame to sample queue length."""
        self._queue_snapshots += 1
        self._queue_length_sum += queue_length
        if queue_length > self.peak_queue_length:
            self.peak_queue_length = queue_length

    def record_stove_snapshot(self, active_stoves, max_stoves):
        """Call every frame to sample stove utilization."""
        self._stove_busy_samples += active_stoves
        self._stove_total_samples += max_stoves

    def record_stock_snapshot(self, inventory_items):
        """Call periodically to track peak stock levels.

        Args:
            inventory_items: dict of {ingredient: count}
        """
        for item, count in inventory_items.items():
            if count > self.peak_stock[item]:
                self.peak_stock[item] = count

    # ── Finalization ──────────────────────────────────────────────────

    def finalize(self, game_duration):
        """Compute all derived metrics. Call once at end of game.

        Args:
            game_duration: total elapsed game time in seconds
        """
        self.game_duration = game_duration

        # Average wait time
        if self.total_served > 0:
            self.avg_wait_time = self.total_wait_time / self.total_served
        else:
            self.avg_wait_time = 0.0

        # Serve rate (fraction of customers served)
        if self.total_arrived > 0:
            self.serve_rate = self.total_served / self.total_arrived
        else:
            self.serve_rate = 0.0

        # Loss rate (fraction of customers lost)
        if self.total_arrived > 0:
            self.loss_rate = self.total_lost / self.total_arrived
        else:
            self.loss_rate = 0.0

        # Profit
        total_spent = self.total_spent_on_ingredients + self.total_spent_on_stoves
        self.profit = self.total_revenue - total_spent

        # Stove utilization
        if self._stove_total_samples > 0:
            self.stove_utilization = self._stove_busy_samples / self._stove_total_samples
        else:
            self.stove_utilization = 0.0

        # Average queue length
        if self._queue_snapshots > 0:
            self.avg_queue_length = self._queue_length_sum / self._queue_snapshots
        else:
            self.avg_queue_length = 0.0

        # Actions per minute
        if game_duration > 0:
            self.actions_per_minute = self._total_actions / (game_duration / 60.0)
        else:
            self.actions_per_minute = 0.0

        # Efficiency score (composite)
        self._compute_efficiency_score()

    def _compute_efficiency_score(self):
        """Compute weighted efficiency score in [0, 1].

        Formula:
            score = 0.35 * serve_rate
                  + 0.25 * (1 - loss_rate)
                  + 0.25 * profit_ratio
                  + 0.15 * stove_utilization
        """
        # Profit ratio: clamp between 0 and 1
        # We consider $300+ as "perfect" profit
        if self.total_revenue > 0:
            profit_ratio = min(1.0, max(0.0, self.profit / 300.0))
        else:
            profit_ratio = 0.0

        self.efficiency_score = (
            0.35 * self.serve_rate
            + 0.25 * (1.0 - self.loss_rate)
            + 0.25 * profit_ratio
            + 0.15 * min(1.0, self.stove_utilization)
        )
        self.efficiency_score = round(self.efficiency_score, 4)

    # ── Rating ────────────────────────────────────────────────────────

    def get_rating(self):
        """Return a tuple of (stars, label) based on efficiency score.

        Returns:
            (str, str) e.g. ("***", "Efficient")
        """
        if self.efficiency_score >= 0.75:
            return ("***", "Efficient")
        elif self.efficiency_score >= 0.50:
            return ("**", "Average")
        else:
            return ("*", "Poor")

    # ── Strategy Feedback ─────────────────────────────────────────────

    def generate_feedback(self):
        """Analyze stats and return a list of (icon, message) feedback tuples.

        Returns:
            list of (str, str, tuple) → (icon, message, color_rgb)
        """
        feedback = []
        RED = (255, 80, 80)
        YELLOW = (255, 220, 80)
        GREEN = (80, 230, 100)

        # ── Critical issues ──────────────────────────────────────────
        if self.loss_rate > 0.4:
            feedback.append((
                "✗",
                "Too many customers left! Your serving speed needs major improvement.",
                RED,
            ))
        elif self.loss_rate > 0.2:
            feedback.append((
                "!",
                "Several customers left unhappy. Try to serve faster.",
                YELLOW,
            ))

        # ── Wait time ────────────────────────────────────────────────
        if self.avg_wait_time > 15:
            feedback.append((
                "!",
                f"Avg wait was {self.avg_wait_time:.1f}s — cook popular dishes in advance.",
                YELLOW,
            ))
        elif self.avg_wait_time > 10:
            feedback.append((
                "!",
                f"Avg wait was {self.avg_wait_time:.1f}s — could be faster.",
                YELLOW,
            ))

        # ── Stove utilization ────────────────────────────────────────
        if self.stove_utilization < 0.3:
            feedback.append((
                "!",
                "Stoves were idle most of the time. Cook more aggressively!",
                YELLOW,
            ))
        elif self.stove_utilization > 0.9:
            feedback.append((
                "~",
                "Stoves were maxed out. Consider buying more stoves.",
                YELLOW,
            ))

        # ── Queue ────────────────────────────────────────────────────
        if self.peak_queue_length > 8:
            feedback.append((
                "!",
                f"Queue peaked at {self.peak_queue_length}. Pre-cook before rushes!",
                YELLOW,
            ))

        # ── Overstocking ─────────────────────────────────────────────
        total_bought = sum(self.buy_counts.values())
        total_used_in_cooking = sum(self.cook_counts.values())  # rough proxy
        if total_bought > 0 and total_used_in_cooking < total_bought * 0.3:
            feedback.append((
                "!",
                "You bought many ingredients but cooked very few dishes — wasted money.",
                YELLOW,
            ))

        # ── Spending ratio ───────────────────────────────────────────
        total_spent = self.total_spent_on_ingredients + self.total_spent_on_stoves
        if self.total_revenue > 0 and total_spent > self.total_revenue * 0.7:
            feedback.append((
                "!",
                "Ingredient/stove costs ate into your profits significantly.",
                YELLOW,
            ))

        # ── Activity level ───────────────────────────────────────────
        if self.game_duration > 30 and self.actions_per_minute < 2:
            feedback.append((
                "!",
                "You were too passive. Act faster to keep up with demand.",
                YELLOW,
            ))

        # ── Positive feedback ────────────────────────────────────────
        if self.serve_rate >= 0.8:
            feedback.append((
                "✓",
                f"Great serving! {self.serve_rate:.0%} of customers left happy.",
                GREEN,
            ))

        if self.profit >= 100:
            feedback.append((
                "✓",
                f"Excellent profit of ${self.profit:.0f}! You ran a lean kitchen.",
                GREEN,
            ))
        elif self.profit >= 50:
            feedback.append((
                "✓",
                f"Decent profit of ${self.profit:.0f}. Room for improvement.",
                GREEN,
            ))

        if self.stove_utilization >= 0.5 and self.stove_utilization <= 0.85:
            feedback.append((
                "✓",
                "Good stove management — balanced between idle and overload.",
                GREEN,
            ))

        # ── If no feedback, give a generic one ───────────────────────
        if not feedback:
            feedback.append((
                "~",
                "Not enough data to evaluate. Play a longer session!",
                YELLOW,
            ))

        return feedback

    # ── Bottleneck detection ──────────────────────────────────────────

    def get_bottleneck(self):
        """Identify the primary bottleneck in the player's strategy.

        Returns:
            (str, str) → (bottleneck_name, description)
        """
        issues = {}

        # Queue bottleneck: customers arriving faster than being served
        if self.loss_rate > 0.3:
            issues["Queue Management"] = self.loss_rate

        # Cooking bottleneck: stoves maxed out
        if self.stove_utilization > 0.85:
            issues["Kitchen Capacity"] = self.stove_utilization

        # Inventory bottleneck: couldn't cook because of missing ingredients
        # (approximate: if cook_count is low relative to demand)
        if self.total_arrived > 5 and sum(self.cook_counts.values()) < self.total_arrived * 0.4:
            issues["Ingredient Supply"] = 0.8

        # Speed bottleneck: player not acting fast enough
        if self.game_duration > 30 and self.actions_per_minute < 2:
            issues["Player Speed"] = 0.7

        if not issues:
            return ("None", "No major bottlenecks detected. Well played!")

        worst = max(issues, key=issues.get)
        descriptions = {
            "Queue Management": "Customers are leaving faster than you can serve them.",
            "Kitchen Capacity": "Your stoves can't keep up with demand. Buy more stoves.",
            "Ingredient Supply": "You didn't have enough ingredients to cook what was needed.",
            "Player Speed": "You need to click/press keys faster to keep up with orders.",
        }
        return (worst, descriptions.get(worst, ""))
