# settings.py
import numpy as np
# Screen
WIDTH = 800
HEIGHT = 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY  = (40, 40, 40)

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