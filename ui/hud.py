# ui/hud.py
import pygame
from settings import RICH_CREAM, BLACK, WARM_TERRACOTTA, VIBRANT_GOLD, CERAMIC, GREEN_ACCENT, RED_ACCENT

class HUD:
    def __init__(self, inventory):
        self.inventory = inventory
        self.font_title = pygame.font.SysFont("trebuchetms", 28, bold=True)
        self.font = pygame.font.SysFont("trebuchetms", 20, bold=True)
        self.font_sm = pygame.font.SysFont("trebuchetms", 15, bold=True)
        self.color = BLACK

    def draw(self, surface, cur_w, cur_h, game_stats=None, game_elapsed=0.0, game_timer_max=0.0):
        # 1. Game Title and Logo (Top Left)
        title_surf = self.font_title.render("Cafeteria Dash", True, RICH_CREAM)
        surface.blit(title_surf, (60, 20))
        # Placeholder Logo
        pygame.draw.circle(surface, VIBRANT_GOLD, (30, 35), 15)
        pygame.draw.circle(surface, RICH_CREAM, (30, 35), 15, 2)

        # 2. Chef Character and Cooked Food (Top Right)
        chef_x = cur_w - 60
        chef_y = 60
        # Draw Placeholder Chef
        pygame.draw.circle(surface, RICH_CREAM, (chef_x, chef_y), 20) # Head
        pygame.draw.rect(surface, RICH_CREAM, (chef_x - 15, chef_y - 40, 30, 25), border_radius=4) # Hat
        pygame.draw.ellipse(surface, (200, 200, 200), (chef_x - 20, chef_y - 45, 40, 10)) # Hat brim
        pygame.draw.circle(surface, BLACK, (chef_x - 7, chef_y - 2), 3) # Eye
        pygame.draw.circle(surface, BLACK, (chef_x + 7, chef_y - 2), 3) # Eye
        
        # Thought Bubbles for Food
        bubble_x = chef_x - 140
        y_offset = 20
        for dish, count in self.inventory.cooked_food.items():
            if count > 0:
                # Draw bubble
                pygame.draw.ellipse(surface, RICH_CREAM, (bubble_x, y_offset, 100, 30))
                # Pointer to chef
                pygame.draw.polygon(surface, RICH_CREAM, [(bubble_x + 90, y_offset + 15), (bubble_x + 100, y_offset + 25), (chef_x - 15, chef_y - 10)])
                
                # Text
                text = self.font_sm.render(f"{dish}: {count}", True, BLACK)
                surface.blit(text, (bubble_x + 10, y_offset + 5))
                y_offset += 40

        # 3. Draw Live Stats Panel (if stats are being tracked)
        if game_stats is not None:
            self._draw_live_stats(surface, game_stats, game_elapsed, game_timer_max, cur_w, cur_h)

    def _draw_live_stats(self, surface, stats, elapsed, timer_max, cur_w, cur_h):
        """Draw a compact live stats panel on the right side."""
        panel_x = cur_w - 200
        panel_y = cur_h // 2 - 100

        # Panel background
        panel_rect = pygame.Rect(panel_x - 5, panel_y - 5, 195, 150)
        pygame.draw.rect(surface, (253, 246, 227, 220), panel_rect, border_radius=15) # RICH_CREAM with alpha
        pygame.draw.rect(surface, VIBRANT_GOLD, panel_rect, 2, border_radius=15) # Gold border

        # Header
        hdr = self.font_sm.render("LIVE STATS", True, WARM_TERRACOTTA)
        surface.blit(hdr, (panel_x, panel_y))
        y = panel_y + 25

        # Timer
        mins = int(elapsed) // 60
        secs = int(elapsed) % 60
        if timer_max > 0:
            remaining = max(0, timer_max - elapsed)
            r_mins = int(remaining) // 60
            r_secs = int(remaining) % 60
            time_color = RED_ACCENT if remaining < 30 else VIBRANT_GOLD if remaining < 60 else BLACK
            time_str = f"Time: {r_mins}:{r_secs:02d} left"
        else:
            time_color = BLACK
            time_str = f"Time: {mins}:{secs:02d}"
        time_surf = self.font_sm.render(time_str, True, time_color)
        surface.blit(time_surf, (panel_x, y))
        y += 25

        # Served
        served_text = self.font_sm.render(f"Served: {stats.total_served}", True, GREEN_ACCENT)
        surface.blit(served_text, (panel_x, y))
        y += 25

        # Lost (Draw Silhouettes)
        lost_text = self.font_sm.render(f"Lost: ", True, RED_ACCENT)
        surface.blit(lost_text, (panel_x, y))
        
        for i in range(stats.total_lost):
            # Draw tiny grey silhouette
            sx = panel_x + 50 + (i * 12)
            sy = y + 7
            pygame.draw.circle(surface, (150, 150, 150), (sx, sy - 5), 4)
            pygame.draw.polygon(surface, (150, 150, 150), [(sx - 5, sy + 5), (sx + 5, sy + 5), (sx, sy - 2)])
        
        y += 25

        # Serve rate
        if stats.total_arrived > 0:
            rate = stats.total_served / stats.total_arrived
            rate_color = GREEN_ACCENT if rate >= 0.7 else VIBRANT_GOLD if rate >= 0.4 else RED_ACCENT
            rate_text = self.font_sm.render(f"Rate: {rate:.0%}", True, rate_color)
        else:
            rate_text = self.font_sm.render("Rate: --", True, BLACK)
        surface.blit(rate_text, (panel_x, y))
