# ui/hud.py
import pygame

class HUD:
    def __init__(self, inventory):
        self.inventory = inventory
        self.font = pygame.font.SysFont("Arial", 20, bold=True)
        self.color = (255, 255, 255)

    def draw(self, surface):
        # 1. Draw Money (Top Left, Yellow)
        money_text = self.font.render(f"Money: ${self.inventory.money}", True, (255, 215, 0))
        surface.blit(money_text, (20, 20))

        # 2. Draw Inventory List (Below Money)
        y_offset = 60
        for item, count in self.inventory.items.items():
            text = self.font.render(f"{item}: {count}", True, self.color)
            surface.blit(text, (20, y_offset))
            y_offset += 30 # Move down for next line
            
        # 3. Draw Controls Help (Bottom Left)
        help_text = self.font.render("Press 1: Rice($2) | 2: Egg($1) | 3: Veg($2) | 4: Chk($5)", True, (150, 150, 150))
        surface.blit(help_text, (20, 550))

        # 4. Draw Cooked Food (Top Right)
        # We will draw this at x=600
        header_text = self.font.render("READY TO SERVE:", True, (0, 255, 0))
        surface.blit(header_text, (600, 20))
        
        y_offset = 50
        for dish, count in self.inventory.cooked_food.items():
            # Only draw if we have at least 1, or draw all if you prefer
            color = (255, 255, 255) if count > 0 else (100, 100, 100)
            text = self.font.render(f"{dish}: {count}", True, color)
            surface.blit(text, (600, y_offset))
            y_offset += 30