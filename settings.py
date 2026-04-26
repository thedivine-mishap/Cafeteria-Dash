# settings.py
import numpy as np
from dataclasses import dataclass, field
from typing import Dict
# Screen
WIDTH = 800
HEIGHT = 600
FPS = 60

# Colors (Cozy Palette)
# Colors (Vibrant Cozy Palette)
BG_COLOR = (26, 54, 54)          # Deep Teal
RICH_CREAM = (253, 246, 227)     # For bright UI panels
WHITE = RICH_CREAM               # Alias
BLACK = (44, 62, 80)             # Deep Navy/Charcoal for text
WARM_TERRACOTTA = (211, 84, 0)   # Vibrant Terracotta
TERRACOTTA = WARM_TERRACOTTA     # Alias
VIBRANT_GOLD = (243, 156, 18)    # Pop of Gold
WOOD_TEXTURE = (139, 90, 43)     # Rich Wood brown
CERAMIC = (236, 240, 241)        # Ceramic off-white
GREEN_ACCENT = (39, 174, 96)     # Vibrant Emerald/Matcha
RED_ACCENT = (231, 76, 60)       # Vibrant Coral/Red
GRAY = (149, 165, 166)           # Cool gray for inactive states

# Game balance (we'll tune later)
ARRIVAL_RATE = 0.2          # customers per second
MAX_COOKING_SLOTS = 4




# Customer Settings
ARRIVAL_RATE = 0.1  # Average customers per second (λ)
PATIENCE_MEAN = 20  # Average patience in seconds
PATIENCE_STD = 5    # Standard deviation

# settings.py

# Food & Recipes
# Format: "Dish Name": {"Ingredient": Qty}
RECIPES = {
    "Fried Rice": {"Rice": 1, "Egg": 1, "Veggie": 1},
    "Chicken Rice": {"Rice": 1, "Chicken": 1},
    "Omelet": {"Egg": 2, "Veggie": 1}
}

# Selling Price (How much money you get)
MENU_PRICES = {
    "Fried Rice": 15,
    "Chicken Rice": 20,
    "Omelet": 10
}

# Cost to buy ingredients (for the shop later)
INGREDIENT_PRICES = {
    "Rice": 2,
    "Egg": 1,
    "Veggie": 2,
    "Chicken": 5
}

# settings.py

COOKING_TIMES = {
    "Fried Rice": 5,    # 5 seconds
    "Chicken Rice": 8,  # 8 seconds
    "Omelet": 3         # 3 seconds
}


# ── Simulation experiment configuration ──────────────────────────────
@dataclass
class SimConfig:
    """Bundles all tunable parameters for a single simulation run.

    The interactive game (main.py) ignores this and uses the constants above.
    The experiment framework passes a SimConfig to the simulator.
    """
    num_queues: int = 1
    num_stoves: int = 4
    initial_ingredients: Dict[str, int] = field(default_factory=lambda: {
        "Rice": 5, "Egg": 5, "Veggie": 5, "Chicken": 5
    })
    starting_money: float = 100.0
    arrival_rate: float = 0.1       # λ for Poisson process
    sim_duration: float = 300.0     # seconds of game-time per run
    max_lost: int = 5               # game-over threshold