# simulation/simulator.py
"""
Visual Pygame-based cafeteria simulator.

Runs the same game logic as main.py but with automated decisions
(auto-serve, auto-cook, auto-buy) at accelerated speed.
Renders everything so it looks like a fast-forwarded game.
"""

import pygame
import numpy as np
import random
import sys
import os

# Add project root to path so we can import project modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from settings import (
    WIDTH, HEIGHT, RECIPES, MENU_PRICES, INGREDIENT_PRICES,
    COOKING_TIMES, PATIENCE_MEAN, PATIENCE_STD, SimConfig,
)
from simulation.metrics import GameStats


# ── Lightweight entities (no sprite images needed) ────────────────────

class SimCustomer:
    """Minimal customer for simulation — no Pygame sprites/images."""

    def __init__(self, pos, order, arrival_time):
        self.x, self.y = pos
        self.order = order
        self.arrival_time = arrival_time

        # Patience from normal distribution (same as entities/customer.py)
        self.patience = max(10, np.random.normal(PATIENCE_MEAN, PATIENCE_STD))
        self.max_patience = self.patience

        self.served = False
        self.alive = True

    def update(self, dt):
        self.patience -= dt
        if self.patience <= 0:
            self.alive = False


class SimKitchen:
    """Minimal kitchen for simulation — mirrors systems/kitchen.py logic."""

    def __init__(self, inventory_items, cooked_food, max_slots, stats):
        self.items = inventory_items       # dict reference
        self.cooked_food = cooked_food     # dict reference
        self.max_slots = max_slots
        self.stats = stats
        self.slots = []                    # list of cooking tasks

    def start_cooking(self, dish_name):
        if len(self.slots) >= self.max_slots:
            return False

        recipe = RECIPES[dish_name]
        # Check ingredients
        for ingredient, qty in recipe.items():
            if self.items.get(ingredient, 0) < qty:
                return False

        # Deduct ingredients
        for ingredient, qty in recipe.items():
            self.items[ingredient] -= qty

        self.slots.append({
            "name": dish_name,
            "time": COOKING_TIMES[dish_name],
            "total": COOKING_TIMES[dish_name],
        })
        return True

    def update(self, dt):
        for task in self.slots[:]:
            task["time"] -= dt
            if task["time"] <= 0:
                self.cooked_food[task["name"]] += 1
                self.stats.dishes_cooked[task["name"]] += 1
                self.slots.remove(task)


# ── Main Simulator ────────────────────────────────────────────────────

class CafeteriaSimulator:
    """Runs one visual simulation with the given config and returns stats."""

    # ── Drawing constants ─────────────────────────────────────────────
    # Vertical queues: queues laid out horizontally (columns), customers stacked vertically
    QUEUE_X_BASE = 80       # left margin for first queue column
    QUEUE_X_SPACING = 160   # horizontal spacing between queue columns
    QUEUE_START_Y = 120     # top position for customers in each queue
    CUSTOMER_SPACING = 110   # vertical spacing between customers in a queue (increased)
    CUSTOMER_SIZE = 30
    STOVE_START_X = 420
    STOVE_Y = 480
    STOVE_W, STOVE_H = 65, 45
    SPEED_MULTIPLIER = 8           # game-time runs this many × real-time

    # ── Colors ────────────────────────────────────────────────────────
    from settings import (
        BG_COLOR as SIM_BG_COLOR,
        RICH_CREAM, BLACK, WARM_TERRACOTTA, VIBRANT_GOLD,
        GREEN_ACCENT, RED_ACCENT, GRAY, CERAMIC
    )
    BG_COLOR = SIM_BG_COLOR
    QUEUE_LABEL_COLOR = RICH_CREAM
    CUSTOMER_COLORS = {
        "Fried Rice": WARM_TERRACOTTA,
        "Chicken Rice": VIBRANT_GOLD,
        "Omelet": RICH_CREAM,
    }
    STOVE_EMPTY = GRAY
    STOVE_FILL = GREEN_ACCENT
    TEXT_COLOR = RICH_CREAM
    DIM_TEXT = GRAY
    GOLD = VIBRANT_GOLD
    RED = RED_ACCENT
    GREEN = GREEN_ACCENT

    RESTOCK_THRESHOLD = 3          # auto-buy when stock drops below this

    def __init__(self, config: SimConfig, run_index: int = 1,
                 total_runs: int = 1, screen=None, clock=None):
        self.config = config
        self.run_index = run_index
        self.total_runs = total_runs
        self.stats = GameStats()

        # Pygame setup — reuse existing screen/clock if provided
        self.owns_display = screen is None
        if self.owns_display:
            pygame.init()
            info = pygame.display.Info()
            # Borderless windowed mode to avoid exclusive-fullscreen minimizing
            self.screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.NOFRAME)
            self.clock = pygame.time.Clock()
        else:
            self.screen = screen
            self.clock = clock

        self._update_caption()

        # Fonts - use same family as main UI for consistency
        self.font = pygame.font.SysFont("trebuchetms", 16, bold=True)
        self.font_sm = pygame.font.SysFont("trebuchetms", 13)
        self.font_lg = pygame.font.SysFont("trebuchetms", 22, bold=True)
        self.font_title = pygame.font.SysFont("trebuchetms", 28, bold=True)

        # Inventory
        self.money = config.starting_money
        self.items = {k: v for k, v in config.initial_ingredients.items()}
        self.cooked_food = {"Fried Rice": 0, "Chicken Rice": 0, "Omelet": 0}

        # Kitchen
        self.kitchen = SimKitchen(
            self.items, self.cooked_food, config.num_stoves, self.stats
        )

        # Queues — list of lists
        self.queues = [[] for _ in range(config.num_queues)]

        # Timing
        self.sim_clock = 0.0
        self.spawn_timer = self._next_arrival()
        # Track lost customers across the run for early termination
        self.lost_total = 0
        
        # Simulation UI Buttons
        from ui.button import Button
        from settings import GRAY, RED_ACCENT, GREEN_ACCENT, TERRACOTTA
        
        self.buttons = []
        self.action_requested = None
        
        def decrease_speed():
            self.SPEED_MULTIPLIER = max(1, self.SPEED_MULTIPLIER - 1)
        
        def increase_speed():
            self.SPEED_MULTIPLIER = min(50, self.SPEED_MULTIPLIER + 1)
            
        def trigger_pause():
            self.action_requested = 'PAUSE'

        self.btn_speed_down = Button(0, 0, 40, 40, "-", GRAY, (230, 215, 200), decrease_speed)
        self.btn_speed_up = Button(0, 0, 40, 40, "+", GRAY, (230, 215, 200), increase_speed)
        self.btn_pause = Button(0, 0, 100, 40, "Pause", RED_ACCENT, (245, 180, 165), trigger_pause)
        self.buttons.extend([self.btn_speed_down, self.btn_speed_up, self.btn_pause])
        
        # Action Grid (Visual only)
        self.btn_cook_rice = Button(0, 0, 120, 40, "Cook Rice", TERRACOTTA, RED_ACCENT, None)
        self.btn_cook_chk = Button(0, 0, 120, 40, "Cook Chk", TERRACOTTA, RED_ACCENT, None)
        self.btn_cook_ome = Button(0, 0, 120, 40, "Cook Omelet", TERRACOTTA, RED_ACCENT, None)
        self.btn_buy_stove = Button(0, 0, 120, 40, "Buy Stove $50", GRAY, (230, 215, 200), None)
        self.buttons.extend([self.btn_cook_rice, self.btn_cook_chk, self.btn_cook_ome, self.btn_buy_stove])

    def check_hover(self, mouse_pos):
        for btn in self.buttons:
            btn.check_hover(mouse_pos)
            
    def handle_event(self, event):
        self.action_requested = None
        for btn in self.buttons:
            btn.handle_event(event)
        return self.action_requested

    def _update_caption(self):
        c = self.config
        pygame.display.set_caption("Cafeteria Dash")

    def _next_arrival(self):
        return np.random.exponential(1 / self.config.arrival_rate)

    # ── Automated strategies ──────────────────────────────────────────

    def _auto_buy(self):
        """Restock ingredients that fall below threshold."""
        for item, count in self.items.items():
            while count < self.RESTOCK_THRESHOLD and self.money >= INGREDIENT_PRICES[item]:
                self.money -= INGREDIENT_PRICES[item]
                self.items[item] += 1
                self.stats.total_ingredient_cost += INGREDIENT_PRICES[item]
                count = self.items[item]

    def _auto_cook(self):
        """Cook the dish with the highest pending demand in queues."""
        if len(self.kitchen.slots) >= self.config.num_stoves:
            return

        # Count demand per dish across all queues
        demand = {}
        for q in self.queues:
            for c in q:
                demand[c.order] = demand.get(c.order, 0) + 1

        # Subtract already-available cooked food
        net_demand = {}
        for dish, count in demand.items():
            net = count - self.cooked_food.get(dish, 0)
            if net > 0:
                net_demand[dish] = net

        # Also subtract dishes currently being cooked
        for task in self.kitchen.slots:
            if task["name"] in net_demand:
                net_demand[task["name"]] -= 1
                if net_demand[task["name"]] <= 0:
                    del net_demand[task["name"]]

        if not net_demand:
            return

        # Cook the most demanded dish (fill all free stoves)
        sorted_dishes = sorted(net_demand.items(), key=lambda x: -x[1])
        for dish, _ in sorted_dishes:
            if len(self.kitchen.slots) >= self.config.num_stoves:
                break
            self.kitchen.start_cooking(dish)

    def _auto_serve(self):
        """Serve the front customer in each queue if food is available."""
        for q in self.queues:
            if not q:
                continue
            front = q[0]
            if self.cooked_food.get(front.order, 0) > 0:
                # Serve
                self.cooked_food[front.order] -= 1
                self.money += MENU_PRICES[front.order]
                front.served = True
                front.alive = False

                self.stats.customers_served += 1
                self.stats.total_revenue += MENU_PRICES[front.order]
                wait = self.sim_clock - front.arrival_time
                self.stats.total_wait_time += wait

    # ── Main run ──────────────────────────────────────────────────────

    def run(self) -> GameStats:
        """Run the simulation to completion and return stats."""
        # Backwards compatible: run() remains available but delegates to step()
        running = True
        while running and self.sim_clock < self.config.sim_duration:
            real_dt = self.clock.tick(60) / 1000.0        # cap at 60 FPS
            running = self.step(real_dt)

        # Finalize
        self.stats.finalize(self.sim_clock)
        return self.stats

    def step(self, real_dt: float) -> bool:
        """Advance the simulator by one frame. Returns False when finished.

        This non-blocking method allows embedding the simulator inside another
        application's main loop (e.g., `main.py`). `real_dt` is seconds of
        real time since last frame (not accelerated).
        """
        # Clamp and accelerate
        real_dt = min(real_dt, 0.05)
        dt = real_dt * self.SPEED_MULTIPLIER

        # Spawn customers (center columns horizontally and stack bottom-up)
        self.spawn_timer -= dt
        while self.spawn_timer <= 0:
            shortest_idx = min(range(len(self.queues)), key=lambda i: len(self.queues[i]))
            q = self.queues[shortest_idx]

            # compute centered start x for the columns using current screen width
            cur_w, cur_h = self.screen.get_size()
            total_cols = max(1, self.config.num_queues)
            total_width = (total_cols - 1) * self.QUEUE_X_SPACING
            start_x = (cur_w - total_width) // 2

            queue_x = start_x + shortest_idx * self.QUEUE_X_SPACING

            # base y sits above the counter area (counter height ~180)
            base_y = cur_h - 180 - 20
            queue_y = base_y - len(q) * self.CUSTOMER_SPACING

            # Only spawn if there's room above (don't spawn off the top of the screen)
            if queue_y > 80:
                order = random.choice(list(RECIPES.keys()))
                # spawn slightly above final position for visual drop
                spawn_y = queue_y - 40
                cust = SimCustomer((queue_x, spawn_y), order, self.sim_clock)
                q.append(cust)
                self.stats.customers_arrived += 1

            self.spawn_timer += self._next_arrival()

        # Update customers
        for q in self.queues:
            for c in q:
                c.update(dt)

        # Queue maintenance (stack bottom-up, aligned to centered columns)
        cur_w, cur_h = self.screen.get_size()
        total_cols = max(1, self.config.num_queues)
        total_width = (total_cols - 1) * self.QUEUE_X_SPACING
        start_x = (cur_w - total_width) // 2

        for q_idx, q in enumerate(self.queues):
            lost_this = sum(1 for c in q if not c.alive and not c.served)
            if lost_this:
                self.lost_total += lost_this
                self.stats.customers_lost += lost_this
            q[:] = [c for c in q if c.alive]
            for i, c in enumerate(q):
                # compute target positions: x centered per column, y stacked from base upwards
                qx = start_x + q_idx * self.QUEUE_X_SPACING
                base_y = cur_h - 180 - 20
                target_y = base_y - (i + 0) * self.CUSTOMER_SPACING
                c.x = qx
                if c.y > target_y:
                    c.y = max(target_y, c.y - 800 * dt)
                else:
                    c.y = target_y

        # Game over
        if self.lost_total >= self.config.max_lost:
            self.stats.finalize(self.sim_clock)
            return False

        # Automated strategy
        self._auto_buy()
        self._auto_cook()
        self._auto_serve()

        # Kitchen
        self.kitchen.update(dt)

        # Advance clock
        self.sim_clock += dt

        # Draw current state (caller will flip)
        self._draw(self.lost_total)

        # Continue running
        if self.sim_clock >= self.config.sim_duration:
            self.stats.finalize(self.sim_clock)
            return False
        return True

    # ── Drawing ───────────────────────────────────────────────────────

    def _draw(self, lost_total):
        self.screen.fill(self.BG_COLOR)
        cur_w, cur_h = self.screen.get_size()
        
        # ── Wooden Kitchen Counter ───────────────────────────────────────
        counter_y = cur_h - 180
        counter_rect = pygame.Rect(0, counter_y, cur_w, 180)
        pygame.draw.rect(self.screen, (160, 100, 60), counter_rect) # Wood base
        pygame.draw.rect(self.screen, (130, 80, 45), counter_rect, 4) # Wood border
        pygame.draw.line(self.screen, (100, 60, 30), (0, counter_y + 15), (cur_w, counter_y + 15), 3) # Counter lip
        
        # ── Spice Jars Shelf ──────────────────────────────────────────────
        shelf_y = counter_y - 120
        pygame.draw.rect(self.screen, (100, 60, 30), (0, shelf_y, 250, 15), border_radius=4) # Wood shelf
        pygame.draw.rect(self.screen, (80, 45, 20), (0, shelf_y, 250, 15), 2, border_radius=4)
        # Jars
        pygame.draw.rect(self.screen, (220, 120, 100), (30, shelf_y - 30, 20, 30), border_radius=3)
        pygame.draw.rect(self.screen, (240, 240, 240), (30, shelf_y - 35, 20, 5)) # Lid
        
        pygame.draw.rect(self.screen, (120, 200, 120), (60, shelf_y - 25, 15, 25), border_radius=3)
        pygame.draw.rect(self.screen, (240, 240, 240), (60, shelf_y - 30, 15, 5))
        
        pygame.draw.rect(self.screen, (220, 200, 100), (90, shelf_y - 35, 25, 35), border_radius=3)
        pygame.draw.rect(self.screen, (240, 240, 240), (90, shelf_y - 40, 25, 5))
        
        pygame.draw.rect(self.screen, (200, 200, 200), (130, shelf_y - 20, 15, 20), border_radius=3)
        pygame.draw.rect(self.screen, (240, 240, 240), (130, shelf_y - 25, 15, 5))

        # ── Top Data Card ────────────────────────────────────────────────
        card_rect = pygame.Rect(20, 20, cur_w - 40, 60)
        pygame.draw.rect(self.screen, self.TEXT_COLOR, card_rect, border_radius=12) # Rich Cream bg
        pygame.draw.rect(self.screen, self.GOLD, card_rect, 3, border_radius=12) # Gold border
        
        cfg = self.config
        
        # Helper for drawing stat blocks
        def draw_stat(x, label, val, color):
            lbl_surf = self.font_sm.render(label, True, self.DIM_TEXT)
            val_surf = self.font.render(val, True, color)
            self.screen.blit(lbl_surf, (x, 25))
            self.screen.blit(val_surf, (x, 42))
            return x + max(lbl_surf.get_width(), val_surf.get_width()) + 30

        x = 40
        x = draw_stat(x, "Queues", str(cfg.num_queues), (50, 50, 50))
        x = draw_stat(x, "Stoves", str(cfg.num_stoves), (50, 50, 50))
        x = draw_stat(x, "Rate", str(cfg.arrival_rate), (50, 50, 50))
        
        # # Vertical divider
        # pygame.draw.line(self.screen, (200, 190, 180), (x-15, 30), (x-15, 60), 2)
        
        # x = draw_stat(x, "Time", f"{int(self.sim_clock)}s / {int(cfg.sim_duration)}s", (50, 50, 50))
        # x = draw_stat(x, "Money", f"${self.money:.0f}", (50, 150, 80))
        # x = draw_stat(x, "Served", str(self.stats.customers_served), (50, 150, 80))
        
        # Lost Customers (Silhouettes)
        lbl_surf = self.font_sm.render("Lost", True, self.DIM_TEXT)
        self.screen.blit(lbl_surf, (x, 25))
        for i in range(cfg.max_lost):
            sil_x = x + i * 15
            sil_y = 52
            color = self.RED if i < lost_total else (200, 190, 180)
            pygame.draw.circle(self.screen, color, (sil_x, sil_y - 6), 4)
            pygame.draw.ellipse(self.screen, color, (sil_x - 6, sil_y, 12, 10))
            
        # ── Speed and Run Controls ──
        run_txt = f"Run {self.run_index}/{self.total_runs}"
        run_surf = self.font.render(run_txt, True, (150, 150, 150))
        # shift run text left so controls fit inside the card
        run_x = max(40, card_rect.right - 420)
        self.screen.blit(run_surf, (run_x, 40))

        # Place speed controls shifted left to make room for Pause inside the card
        self.btn_speed_down.set_position(card_rect.right - 260, card_rect.y + 12)
        spd_txt = f"{self.SPEED_MULTIPLIER}x"
        spd_surf = self.font.render(spd_txt, True, (50, 50, 50))
        self.screen.blit(spd_surf, (card_rect.right - 210, card_rect.y + 18))
        self.btn_speed_up.set_position(card_rect.right - 180, card_rect.y + 12)

        # Place Pause button inside the stat card (aligned to right edge)
        pause_w, pause_h = 100, 40
        pause_x = card_rect.right - 12 - pause_w
        pause_y = card_rect.y + (card_rect.height - pause_h) // 2
        self.btn_pause.set_position(pause_x, pause_y)

        # Instruction box (right side) - styled to match the stat card
        instruct_w = 300
        instruct_h = 64
        instruct_rect = pygame.Rect(cur_w - instruct_w - 20, card_rect.bottom + 12, instruct_w, instruct_h)
        pygame.draw.rect(self.screen, self.TEXT_COLOR, instruct_rect, border_radius=12)
        pygame.draw.rect(self.screen, self.GOLD, instruct_rect, 3, border_radius=12)

        # Wrapped instruction text
        instr_txt = "Press ESC to stop the simulation and return to main menu"
        def wrap_text(text, font, max_width):
            words = text.split()
            lines = []
            cur = ''
            for w in words:
                test = (cur + ' ' + w).strip() if cur else w
                if font.size(test)[0] <= max_width:
                    cur = test
                else:
                    if cur:
                        lines.append(cur)
                    cur = w
            if cur:
                lines.append(cur)
            return lines

        padding = 12
        lines = wrap_text(instr_txt, self.font_sm, instruct_rect.width - padding*2)
        for i, line in enumerate(lines[:3]):
            y = instruct_rect.y + padding + i * (self.font_sm.get_height() + 2)
            surf = self.font_sm.render(line, True, (60, 60, 60))
            self.screen.blit(surf, (instruct_rect.x + padding, y))

        # ── Queues ────────────────────────────────────────────────────
        total_cols = max(1, self.config.num_queues)
        total_width = (total_cols - 1) * self.QUEUE_X_SPACING
        start_x = (cur_w - total_width) // 2

        for qi, q in enumerate(self.queues):
            x = start_x + qi * self.QUEUE_X_SPACING

            # Draw vertical path for the queue (from a bit higher to counter area)
            path_top = 60
            path_bottom = counter_y - 40

            for c in q:
                color = self.CUSTOMER_COLORS.get(c.order, (180, 180, 180))
                cx, cy = int(c.x), int(c.y)

                # Draw expressive character (placeholder using shapes)
                # Body
                pygame.draw.ellipse(self.screen, color, (cx, cy + 10, self.CUSTOMER_SIZE, self.CUSTOMER_SIZE - 5))
                # Head
                head_color = (255, 220, 180) # Generic skin tone
                pygame.draw.circle(self.screen, head_color, (cx + self.CUSTOMER_SIZE//2, cy + 5), 10)
                # Eyes
                pygame.draw.circle(self.screen, (0, 0, 0), (cx + self.CUSTOMER_SIZE//2 - 3, cy + 3), 2)
                pygame.draw.circle(self.screen, (0, 0, 0), (cx + self.CUSTOMER_SIZE//2 + 3, cy + 3), 2)

                # Patience bar
                ratio = max(0, c.patience / c.max_patience)
                bar_w = self.CUSTOMER_SIZE
                if ratio > 0.5:
                    bar_col = self.GREEN
                elif ratio > 0.2:
                    bar_col = self.GOLD
                else:
                    bar_col = self.RED
                pygame.draw.rect(self.screen, (40, 40, 40), (cx, cy - 12, bar_w, 6), border_radius=2)
                pygame.draw.rect(self.screen, bar_col, (cx, cy - 12, int(bar_w * ratio), 6), border_radius=2)

                # Order label (bubble) positioned above the customer to avoid overlap
                bubble_rect = pygame.Rect(cx - 5, cy - 35, 60, 18)
                pygame.draw.rect(self.screen, self.TEXT_COLOR, bubble_rect, border_radius=8)
                order_surf = self.font_sm.render(c.order[:8], True, (50, 50, 50)) # Slightly longer abbreviation allowed
                self.screen.blit(order_surf, (cx + 2, cy - 33))

        # ── Inventory Storage Bins ────────────────────────────────────
        from settings import CERAMIC
        bin_start_x = 20
        bin_y = counter_y + 40
        bin_w = 70
        for i, (item, count) in enumerate(self.items.items()):
            bx = bin_start_x + i * (bin_w + 20)
            # Bin body
            pygame.draw.rect(self.screen, self.TEXT_COLOR, (bx, bin_y, bin_w, 60), border_radius=10)
            pygame.draw.rect(self.screen, (220, 210, 200), (bx, bin_y, bin_w, 60), 2, border_radius=10)
            
            # Item Icon (Placeholder circle)
            icon_col = self.GREEN if item == "Veggie" else (240, 200, 150)
            pygame.draw.circle(self.screen, icon_col, (bx + bin_w//2, bin_y + 20), 12)
            
            # Count
            col = self.TEXT_COLOR if count >= self.RESTOCK_THRESHOLD else self.RED
            badge_rect = pygame.Rect(bx + bin_w//2 - 15, bin_y + 35, 30, 20)
            pygame.draw.rect(self.screen, (60, 50, 40), badge_rect, border_radius=5)
            cnt_surf = self.font.render(str(count), True, col)
            self.screen.blit(cnt_surf, cnt_surf.get_rect(center=badge_rect.center))

        # ── Ready Food (Chef) ──────────────────────────────────────────
        chef_x = bin_start_x + 4 * (bin_w + 20) + 40
        chef_y = counter_y - 60
        # (Left chef drawing removed in simulator — keep chef_x for stove layout)

        # Mirror Chef and Thought Bubbles on the right side
        chef2_x = cur_w - 80
        chef2_y = chef_y
        # Draw Chef body (mirrored)
        pygame.draw.rect(self.screen, (240, 240, 240), (chef2_x - 20, chef2_y + 30, 40, 50), border_radius=10) # Coat
        pygame.draw.circle(self.screen, (255, 220, 180), (chef2_x, chef2_y + 15), 18) # Head
        pygame.draw.rect(self.screen, (250, 250, 250), (chef2_x - 15, chef2_y - 15, 30, 20)) # Hat base
        pygame.draw.ellipse(self.screen, (250, 250, 250), (chef2_x - 25, chef2_y - 25, 50, 20)) # Hat top

        # Thought Bubbles for Ready Food (mirrored to the left of the chef)
        bubble_x2 = chef2_x - 160
        bubble_y2 = chef2_y - 40
        for dish, count in self.cooked_food.items():
            col = (50, 150, 80) if count > 0 else (140, 140, 140)
            pygame.draw.ellipse(self.screen, (250, 245, 235), (bubble_x2, bubble_y2, 110, 35))
            pygame.draw.ellipse(self.screen, (200, 190, 180), (bubble_x2, bubble_y2, 110, 35), 2)

            # small connector circles (toward the chef)
            pygame.draw.circle(self.screen, (250, 245, 235), (bubble_x2 + 115, bubble_y2 + 25), 6)
            pygame.draw.circle(self.screen, (250, 245, 235), (bubble_x2 + 125, bubble_y2 + 35), 4)

            txt_surf = self.font_sm.render(f"{dish[:4]}: {count}", True, col)
            self.screen.blit(txt_surf, (bubble_x2 + 15, bubble_y2 + 10))
            bubble_y2 += 45

        # ── Stoves ────────────────────────────────────────────────────
        stove_start_x = chef_x + 180
        stove_y = counter_y + 20
        for i in range(self.config.num_stoves):
            col = i % 4
            row = i // 4
            sx = stove_start_x + col * (self.STOVE_W + 20)
            sy = stove_y + row * (self.STOVE_H + 30)
            
            # Ceramic Hob
            rect = pygame.Rect(sx, sy, self.STOVE_W, self.STOVE_H)
            pygame.draw.rect(self.screen, CERAMIC, rect, border_radius=8)
            pygame.draw.rect(self.screen, (200, 190, 180), rect, 2, border_radius=8)
            
            # Burner circles
            pygame.draw.circle(self.screen, (40, 40, 40), (sx + self.STOVE_W//2, sy + self.STOVE_H//2), 16)
            pygame.draw.circle(self.screen, (80, 50, 50), (sx + self.STOVE_W//2, sy + self.STOVE_H//2), 12)

            if i < len(self.kitchen.slots):
                task = self.kitchen.slots[i]
                ratio = 1 - (task["time"] / task["total"])
                
                # Cooking Pot
                pot_rect = pygame.Rect(sx + self.STOVE_W//2 - 14, sy + self.STOVE_H//2 - 14, 28, 28)
                pygame.draw.rect(self.screen, (60, 60, 70), pot_rect, border_radius=5)
                
                # Progress bar over the pot
                bar_w = self.STOVE_W
                bar_rect = pygame.Rect(sx, sy - 15, bar_w, 8)
                pygame.draw.rect(self.screen, (60, 60, 60), bar_rect, border_radius=3)
                fill_rect = pygame.Rect(sx, sy - 15, int(bar_w * ratio), 8)
                pygame.draw.rect(self.screen, self.STOVE_FILL, fill_rect, border_radius=3)
                
                name_surf = self.font_sm.render(task["name"][:4], True, (255, 255, 255))
                self.screen.blit(name_surf, (sx + 10, sy - 30))
                
        # ── Control Buttons ──
        # Draw buttons grid in bottom right
        grid_start_x = cur_w - 320
        grid_start_y = counter_y + 40
        self.btn_cook_rice.set_position(grid_start_x, grid_start_y)
        self.btn_cook_chk.set_position(grid_start_x + 140, grid_start_y)
        self.btn_cook_ome.set_position(grid_start_x, grid_start_y + 60)
        self.btn_buy_stove.set_position(grid_start_x + 140, grid_start_y + 60)
        
        for btn in self.buttons:
            btn.draw(self.screen)

        # ── Progress bar ──────────────────────────────────────────────
        bar_y = cur_h - 20
        progress = min(1.0, self.sim_clock / self.config.sim_duration)
        pygame.draw.rect(self.screen, (50, 50, 55), (0, bar_y, cur_w, 20))
        pygame.draw.rect(self.screen, (70, 140, 230), (0, bar_y, int(cur_w * progress), 20))
        pct_txt = f"{int(progress * 100)}%"
        pct_surf = self.font_sm.render(pct_txt, True, (255, 255, 255))
        self.screen.blit(pct_surf, pct_surf.get_rect(center=(cur_w // 2, bar_y + 10)))

    def cleanup(self):
        """Call when done with this simulator instance."""
        if self.owns_display:
            pygame.quit()
