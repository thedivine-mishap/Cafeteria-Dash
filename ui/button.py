# ui/button.py
import pygame

class Button:
    def __init__(self, x, y, width, height, text, color, hover_color, action_func=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.action_func = action_func # The function to run when clicked
        self.font = pygame.font.SysFont("Arial", 14, bold=True)
        self.is_hovered = False

    def draw(self, surface):
        # Change color if hovered
        current_color = self.hover_color if self.is_hovered else self.color
        
        # Draw button body
        pygame.draw.rect(surface, current_color, self.rect, border_radius=5)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, 2, border_radius=5) # White border
        
        # Draw text centered
        text_surf = self.font.render(self.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.is_hovered: # Left click
                if self.action_func:
                    self.action_func() # Run the assigned function
                    return True
        return False