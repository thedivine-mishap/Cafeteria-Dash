import pygame
import numpy as np
import random
import random
from settings import RECIPES
from assets import load_image
from settings import PATIENCE_MEAN, PATIENCE_STD

class Customer(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        # Use the same test sprite for now
        self.image = load_image("images/test_sprite.png")
        # Tint it slightly different (Red-ish) so we know it's a customer
        self.image.fill((200, 100, 100), special_flags=pygame.BLEND_RGB_MULT)
        
        self.rect = self.image.get_rect(topleft=pos)

        # Pick a random dish from the keys of the RECIPES dictionary
        self.order = random.choice(list(RECIPES.keys()))
        
        # Stats using Normal Distribution
        self.patience = max(10, np.random.normal(PATIENCE_MEAN, PATIENCE_STD))
        self.max_patience = self.patience

    def update(self, dt):
        # Patience ticks down
        self.patience -= dt
        
        # If patience runs out, the sprite "kills" itself (removes from all groups)
        if self.patience <= 0:
            self.kill()

    def draw_patience_bar(self, surface):
        # Calculate ratio
        ratio = self.patience / self.max_patience
        
        # Color transition: Green -> Yellow -> Red
        if ratio > 0.5:
            color = (0, 255, 0) # Green
        elif ratio > 0.2:
            color = (255, 255, 0) # Yellow
        else:
            color = (255, 0, 0) # Red
            
        # Draw background (gray) and foreground (colored)
        bar_width = self.rect.width
        bar_height = 5
        
        # Background rect
        pygame.draw.rect(surface, (100, 100, 100), (self.rect.x, self.rect.y - 10, bar_width, bar_height))
        # Filling rect
        pygame.draw.rect(surface, color, (self.rect.x, self.rect.y - 10, bar_width * ratio, bar_height))

    def draw_order_text(self, surface, font):
        # Render text (Black color)
        text_surf = font.render(self.order, True, (255, 255, 255))
        # Center it above the sprite
        text_rect = text_surf.get_rect(center=(self.rect.centerx, self.rect.top - 20))
        surface.blit(text_surf, text_rect)