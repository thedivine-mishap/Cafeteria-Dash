# systems/kitchen.py
import pygame
from settings import RECIPES, COOKING_TIMES, WOOD_TEXTURE, CERAMIC, RICH_CREAM, BLACK, WARM_TERRACOTTA, GREEN_ACCENT, RED_ACCENT, GRAY, VIBRANT_GOLD

class Kitchen:
    def __init__(self, inventory, max_slots=4, stats=None):
        self.inventory = inventory
        self.slots = [] # List of active cooking tasks
        self.max_slots = max_slots
        self.stats = stats  # Optional GameStats for tracking

    def start_cooking(self, dish_name):
        # 1. Check if we have an empty stove
        if len(self.slots) >= self.max_slots:
            print("Kitchen is full!")
            return (False, "full")

        # 2. Check if we have ingredients
        recipe = RECIPES[dish_name]
        missing = {}
        for ingredient, qty in recipe.items():
            have = self.inventory.items.get(ingredient, 0)
            if have < qty:
                missing[ingredient] = qty - have

        if missing:
            # Return missing ingredients with quantities required
            print(f"Missing ingredients for {dish_name}: {missing}")
            return (False, missing)

        # 3. Deduct ingredients
        for ingredient, qty in recipe.items():
            self.inventory.items[ingredient] -= qty

        # 4. Start the timer
        # Task format: [Name, Time_Left, Total_Time]
        new_task = {
            "name": dish_name,
            "time": COOKING_TIMES[dish_name],
            "total": COOKING_TIMES[dish_name]
        }
        self.slots.append(new_task)
        print(f"Started cooking {dish_name}")
        return (True, None)

    def buy_stove(self, cost=50):
        """Purchase an additional stove. Returns True if successful."""
        if self.inventory.can_afford(cost):
            self.inventory.money -= cost
            self.max_slots += 1
            print(f"Bought a new stove! Total: {self.max_slots}")
            return True
        print("Not enough money for a new stove!")
        return False

    def update(self, dt):
        # Loop backwards so we can remove items safely
        for task in self.slots[:]:
            task["time"] -= dt
            
            # If cooking is done
            if task["time"] <= 0:
                self.inventory.cooked_food[task["name"]] += 1
                self.slots.remove(task)
                print(f"{task['name']} is ready!")
                # Notify stats tracker if available
                if self.stats:
                    self.stats.record_cook_finished(task["name"])

    def draw(self, surface, cur_w, cur_h):
        # 1. Draw Large Kitchen Counter across the bottom
        counter_h = 160
        counter_y = cur_h - counter_h
        counter_rect = pygame.Rect(0, counter_y, cur_w, counter_h)
        # Wood texture base
        pygame.draw.rect(surface, WOOD_TEXTURE, counter_rect)
        pygame.draw.rect(surface, (100, 60, 20), counter_rect, 4) # Darker edge
        
        # 2. Draw Storage Bins (Left side placeholder for Buy buttons)
        bin_w, bin_h = 70, 70
        bin_start_x = 20
        bin_y = counter_y + 40
        
        # Draw 4 bins (Rice, Egg, Veggie, Chicken)
        bin_labels = ["Rice", "Egg", "Veg", "Chk"]
        bin_counts = [
            self.inventory.items.get("Rice", 0),
            self.inventory.items.get("Egg", 0),
            self.inventory.items.get("Veggie", 0),
            self.inventory.items.get("Chicken", 0)
        ]
        
        for i in range(4):
            bx = bin_start_x + (i * (bin_w + 20))
            # Draw bin (like a sack or box)
            pygame.draw.rect(surface, RICH_CREAM, (bx, bin_y, bin_w, bin_h), border_radius=10)
            pygame.draw.rect(surface, GRAY, (bx, bin_y, bin_w, bin_h), 2, border_radius=10)
            
            # Label
            font = pygame.font.SysFont("trebuchetms", 12, bold=True)
            surface.blit(font.render(bin_labels[i], True, BLACK), (bx + 5, bin_y + 5))
            
            # Draw Count in the center of the bin
            count_font = pygame.font.SysFont("trebuchetms", 24, bold=True)
            count_surf = count_font.render(str(bin_counts[i]), True, WARM_TERRACOTTA)
            surface.blit(count_surf, (bx + bin_w//2 - count_surf.get_width()//2, bin_y + 30))

        # 3. Draw Stoves (Center-Right side)
        slot_w, slot_h = 70, 70
        margin = 15
        cols = min(6, self.max_slots)
        rows = (self.max_slots - 1) // 6 + 1
        
        total_width = cols * (slot_w + margin)
        total_height = rows * (slot_h + margin)
        
        # Position stoves to the right of the bins
        start_x = bin_start_x + (4 * (bin_w + 20)) + 40
        start_y = counter_y + 40
        
        for i in range(self.max_slots):
            col = i % 6
            row = i // 6
            rect = pygame.Rect(start_x + (col * (slot_w + margin)), start_y + (row * (slot_h + margin)), slot_w, slot_h)
            
            # Draw Ceramic Stove Top
            pygame.draw.rect(surface, CERAMIC, rect, border_radius=12)
            pygame.draw.rect(surface, GRAY, rect, 2, border_radius=12)
            
            # If there is a task in this slot, draw the dish icon and progress
            if i < len(self.slots):
                task = self.slots[i]
                ratio = task["time"] / task["total"]
                
                # --- Draw Placeholder Dish Icons ---
                center_x, center_y = rect.centerx, rect.centery - 10
                
                if task["name"] == "Fried Rice":
                    # Orange mound
                    pygame.draw.circle(surface, WARM_TERRACOTTA, (center_x, center_y), 18)
                    pygame.draw.circle(surface, (200, 120, 60), (center_x, center_y), 18, 2)
                elif task["name"] == "Chicken Rice":
                    # Yellow mound with a brown piece
                    pygame.draw.circle(surface, VIBRANT_GOLD, (center_x, center_y), 18)
                    pygame.draw.rect(surface, WOOD_TEXTURE, (center_x - 10, center_y - 5, 20, 10), border_radius=4)
                elif task["name"] == "Omelet":
                    # Yellow oval
                    pygame.draw.ellipse(surface, VIBRANT_GOLD, (center_x - 20, center_y - 15, 40, 30))
                    pygame.draw.ellipse(surface, WARM_TERRACOTTA, (center_x - 20, center_y - 15, 40, 30), 2)
                
                # --- Pill-shaped Progress Bar ---
                bar_w, bar_h = 50, 8
                bar_x = rect.centerx - bar_w // 2
                bar_y = rect.bottom - 15
                
                # Background of bar
                pygame.draw.rect(surface, RICH_CREAM, (bar_x, bar_y, bar_w, bar_h), border_radius=4)
                
                # Fill of bar (Green filling up)
                fill_width = int(bar_w * max(0, 1 - ratio))
                if fill_width > 0:
                    pygame.draw.rect(surface, GREEN_ACCENT, (bar_x, bar_y, fill_width, bar_h), border_radius=4)
            else:
                # Empty burner rings just for aesthetic
                pygame.draw.circle(surface, BLACK, rect.center, 15, 2)
                pygame.draw.circle(surface, BLACK, rect.center, 5, 2)