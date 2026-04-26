# ui/button.py
import pygame
from settings import BLACK, RICH_CREAM, GRAY

class Button:
    def __init__(self, x, y, width, height, text, color, hover_color, action_func=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.action_func = action_func # The function to run when clicked
        self.font = pygame.font.SysFont("trebuchetms", 15, bold=True)
        self.is_hovered = False

    def set_position(self, x, y):
        """Dynamically update the button's position."""
        self.rect.x = x
        self.rect.y = y

    def draw(self, surface):
        # Change color if hovered
        current_color = self.hover_color if self.is_hovered else self.color
        
        # Draw shadow
        shadow_rect = self.rect.copy()
        shadow_rect.y += 3
        pygame.draw.rect(surface, GRAY, shadow_rect, border_radius=15)

        # Draw button body
        pygame.draw.rect(surface, current_color, self.rect, border_radius=15)
        pygame.draw.rect(surface, RICH_CREAM, self.rect, 2, border_radius=15)
        
        # Draw text centered
        text_surf = self.font.render(self.text, True, RICH_CREAM)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # Use the event position for hit-testing so clicks work
                # even if hover state wasn't updated this frame.
                pos = getattr(event, 'pos', pygame.mouse.get_pos())
                if self.rect.collidepoint(pos):
                    if self.action_func:
                        self.action_func() # Run the assigned function
                    return True
        return False