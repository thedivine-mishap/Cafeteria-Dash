# systems/kitchen.py
import pygame
from settings import RECIPES, COOKING_TIMES

class Kitchen:
    def __init__(self, inventory):
        self.inventory = inventory
        self.slots = [] # List of active cooking tasks
        self.max_slots = 4

    def start_cooking(self, dish_name):
        # 1. Check if we have an empty stove
        if len(self.slots) >= self.max_slots:
            print("Kitchen is full!")
            return

        # 2. Check if we have ingredients
        recipe = RECIPES[dish_name]
        for ingredient, qty in recipe.items():
            if self.inventory.items.get(ingredient, 0) < qty:
                print(f"Missing {ingredient} for {dish_name}")
                return

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

    def update(self, dt):
        # Loop backwards so we can remove items safely
        for task in self.slots[:]:
            task["time"] -= dt
            
            # If cooking is done
            if task["time"] <= 0:
                self.inventory.cooked_food[task["name"]] += 1
                self.slots.remove(task)
                print(f"{task['name']} is ready!")

    def draw(self, surface):
        # Draw the 4 Stove Slots at the bottom right
        start_x = 400
        start_y = 500
        
        # Draw 4 empty boxes (stoves)
        for i in range(self.max_slots):
            rect = pygame.Rect(start_x + (i * 80), start_y, 70, 50)
            pygame.draw.rect(surface, (100, 100, 100), rect, 2) # Gray outline
            
            # If there is a task in this slot, draw a green progress bar
            if i < len(self.slots):
                task = self.slots[i]
                ratio = task["time"] / task["total"]
                
                # Fill logic (Green bar shrinking)
                fill_width = 70 * (1 - ratio) # Invert so it fills up
                pygame.draw.rect(surface, (0, 255, 0), (rect.x, rect.y, fill_width, 50))
                
                # Optional: Text
                # font = pygame.font.SysFont(None, 20)
                # surface.blit(font.render(task["name"][:3], True, (255,255,255)), (rect.x+5, rect.y+10))