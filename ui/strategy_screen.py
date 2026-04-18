# ui/strategy_screen.py
"""
Strategy Summary Screen — rendered at the end of a game session.

Displays performance metrics, a rating, strategy feedback messages,
and the identified primary bottleneck. All data comes from GameStats.
"""

import pygame
import math


class StrategyScreen:
    """Renders the end-of-game strategy summary overlay."""

    # ── Colors (Cozy Palette) ─────────────────────────────────────────
    BG = (169, 194, 168)            # Soft Sage Green
    PANEL_BG = (250, 243, 224)      # Warm Cream (Clipboard Paper)
    BORDER = (212, 197, 185)        # Latte / Cream Brown
    GOLD = (205, 126, 93)           # Terracotta Clay
    WHITE = (74, 59, 50)            # Espresso Brown (Main Text)
    DIM = (140, 120, 110)           # Dim text
    GREEN = (143, 169, 120)         # Matcha Green
    RED = (232, 165, 152)           # Soft Coral
    YELLOW = (205, 126, 93)         # Terracotta Clay
    CYAN = (74, 59, 50)             # Espresso Brown
    HEADER_BG = (235, 225, 210)     # Slightly darker cream

    def __init__(self, width, height):
        self.width = width
        self.height = height

        # Fonts
        self.font_title = pygame.font.SysFont("trebuchetms", 30, bold=True)
        self.font_header = pygame.font.SysFont("trebuchetms", 18, bold=True)
        self.font_body = pygame.font.SysFont("trebuchetms", 15)
        self.font_small = pygame.font.SysFont("trebuchetms", 13)
        self.font_rating = pygame.font.SysFont("trebuchetms", 24, bold=True)
        self.font_btn = pygame.font.SysFont("trebuchetms", 16, bold=True)

        # Animation
        self._alpha = 0
        self._fade_speed = 400  # alpha per second

        # Scroll for feedback
        self._scroll_y = 0

        # Continue button rect
        btn_w, btn_h = 200, 45
        self.btn_rect = pygame.Rect(
            width // 2 - btn_w // 2,
            height - 65,
            btn_w, btn_h
        )
        self.btn_hovered = False

    def reset(self):
        """Reset animation state for a new display."""
        self._alpha = 0
        self._scroll_y = 0

    def update(self, dt):
        """Advance fade-in animation."""
        if self._alpha < 255:
            self._alpha = min(255, self._alpha + self._fade_speed * dt)

    def handle_event(self, event):
        """Handle input events. Returns True if 'Continue' was clicked."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_hovered:
                return True
        return False

    def check_hover(self, mouse_pos):
        """Update hover state for the continue button."""
        self.btn_hovered = self.btn_rect.collidepoint(mouse_pos)

    def draw(self, surface, game_stats, cur_w, cur_h):
        """Render the full strategy summary screen.

        Args:
            surface: pygame display surface
            game_stats: finalized GameStats instance
            cur_w: current window width
            cur_h: current window height
        """
        self.width = cur_w
        self.height = cur_h

        # Create overlay surface for fade-in
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        alpha = int(self._alpha)

        # Background
        overlay.fill((*self.BG, min(alpha, 240)))
        surface.blit(overlay, (0, 0))

        if alpha < 50:
            return  # still fading in, don't draw content yet

        # ── Title ─────────────────────────────────────────────────────
        stars, label = game_stats.get_rating()
        title_text = f"{stars}  STRATEGY SUMMARY  {stars}"
        title_surf = self.font_title.render(title_text, True, self.GOLD)
        title_rect = title_surf.get_rect(center=(self.width // 2, 35))
        surface.blit(title_surf, title_rect)

        # ── Single Clipboard Background ───────────────────────────────
        clipboard_x = 15
        clipboard_y = 65
        clipboard_w = self.width - 30
        clipboard_h = self.height - 150
        
        # Clipboard Shadow
        shadow_rect = pygame.Rect(clipboard_x + 5, clipboard_y + 5, clipboard_w, clipboard_h)
        pygame.draw.rect(surface, (140, 160, 140), shadow_rect, border_radius=15)

        # Clipboard Body
        clipboard_rect = pygame.Rect(clipboard_x, clipboard_y, clipboard_w, clipboard_h)
        pygame.draw.rect(surface, self.PANEL_BG, clipboard_rect, border_radius=15)
        pygame.draw.rect(surface, self.BORDER, clipboard_rect, 2, border_radius=15)
        
        # Clip at the top
        clip_w, clip_h = 100, 20
        clip_rect = pygame.Rect((self.width - clip_w) // 2, clipboard_y - 10, clip_w, clip_h)
        pygame.draw.rect(surface, (180, 180, 180), clip_rect, border_radius=8)
        pygame.draw.rect(surface, (150, 150, 150), clip_rect, 2, border_radius=8)

        # ── Left panel: Performance Metrics ───────────────────────────
        panel_x = 25
        panel_y = 75
        panel_w = self.width // 2 - 35
        panel_h = clipboard_h - 20

        # Section header
        hdr_surf = self.font_header.render("PERFORMANCE METRICS", True, self.CYAN)
        surface.blit(hdr_surf, (panel_x + 10, panel_y + 5))

        y = panel_y + 40

        # Format duration
        mins = int(game_stats.game_duration) // 60
        secs = int(game_stats.game_duration) % 60
        duration_str = f"{mins}:{secs:02d}"

        # Metrics list
        metrics = [
            ("Game Duration", duration_str, self.WHITE),
            ("", "", self.WHITE),  # spacer
            ("Customers Arrived", str(game_stats.total_arrived), self.WHITE),
            ("Customers Served", str(game_stats.total_served), self.GREEN),
            ("Customers Lost", str(game_stats.total_lost),
             self.RED if game_stats.total_lost > 0 else self.DIM),
            ("Serve Rate", f"{game_stats.serve_rate:.0%}",
             self.GREEN if game_stats.serve_rate >= 0.7 else self.YELLOW),
            ("", "", self.WHITE),  # spacer
            ("Avg Wait Time", f"{game_stats.avg_wait_time:.1f}s",
             self.GREEN if game_stats.avg_wait_time < 10 else self.YELLOW),
            ("Peak Queue", str(game_stats.peak_queue_length), self.WHITE),
            ("", "", self.WHITE),  # spacer
            ("Total Revenue", f"${game_stats.total_revenue:.0f}", self.GREEN),
            ("Ingredient Cost", f"${game_stats.total_spent_on_ingredients:.0f}", self.RED),
            ("Stove Cost", f"${game_stats.total_spent_on_stoves:.0f}",
             self.RED if game_stats.total_spent_on_stoves > 0 else self.DIM),
            ("Net Profit", f"${game_stats.profit:.0f}",
             self.GREEN if game_stats.profit >= 0 else self.RED),
            ("", "", self.WHITE),  # spacer
            ("Stove Utilization", f"{game_stats.stove_utilization:.0%}",
             self.GREEN if 0.4 <= game_stats.stove_utilization <= 0.85 else self.YELLOW),
            ("Actions/min", f"{game_stats.actions_per_minute:.1f}", self.WHITE),
        ]

        for label_text, value_text, color in metrics:
            if label_text == "":
                y += 8  # spacer
                continue
            lbl = self.font_body.render(label_text, True, self.DIM)
            val = self.font_body.render(value_text, True, color)
            surface.blit(lbl, (panel_x + 15, y))
            surface.blit(val, (panel_x + panel_w - val.get_width() - 15, y))
            y += 22

        # ── Serve rate bar ────────────────────────────────────────────
        y += 5
        bar_x = panel_x + 15
        bar_w = panel_w - 30
        bar_h = 12
        # Background
        pygame.draw.rect(surface, (230, 215, 200), (bar_x, y, bar_w, bar_h), border_radius=6)
        # Fill
        fill_w = int(bar_w * min(1.0, game_stats.serve_rate))
        bar_color = self.GREEN if game_stats.serve_rate >= 0.7 else (
            self.YELLOW if game_stats.serve_rate >= 0.4 else self.RED
        )
        if fill_w > 0:
            pygame.draw.rect(surface, bar_color, (bar_x, y, fill_w, bar_h), border_radius=6)
        lbl = self.font_small.render(f"Serve Rate: {game_stats.serve_rate:.0%}", True, self.WHITE)
        surface.blit(lbl, (bar_x, y + bar_h + 3))

        # ── Right panel: Rating + Feedback + Bottleneck ───────────────
        rpanel_x = self.width // 2 + 10
        rpanel_y = panel_y
        rpanel_w = self.width // 2 - 35
        rpanel_h = panel_h

        # Rating header
        rhdr_surf = self.font_header.render("RATING & FEEDBACK", True, self.CYAN)
        surface.blit(rhdr_surf, (rpanel_x + 10, rpanel_y + 5))

        ry = rpanel_y + 45

        # Rating display
        stars_str, rating_label = game_stats.get_rating()
        rating_color = (
            self.GREEN if "Efficient" in rating_label
            else self.YELLOW if "Average" in rating_label
            else self.RED
        )
        rating_surf = self.font_rating.render(
            f"{stars_str}  {rating_label}", True, rating_color
        )
        surface.blit(rating_surf, (rpanel_x + 15, ry))
        ry += 30

        score_surf = self.font_body.render(
            f"Efficiency Score: {game_stats.efficiency_score:.2f} / 1.00",
            True, self.DIM
        )
        surface.blit(score_surf, (rpanel_x + 15, ry))
        ry += 30

        # Divider
        pygame.draw.line(surface, self.BORDER,
                         (rpanel_x + 10, ry), (rpanel_x + rpanel_w - 10, ry))
        ry += 10

        # Feedback header
        fb_hdr = self.font_header.render("Strategy Feedback", True, self.WHITE)
        surface.blit(fb_hdr, (rpanel_x + 15, ry))
        ry += 25

        # Feedback messages
        feedback = game_stats.generate_feedback()
        for icon, message, color in feedback:
            # Icon
            icon_surf = self.font_body.render(icon, True, color)
            surface.blit(icon_surf, (rpanel_x + 15, ry))

            # Wrap message text
            words = message.split()
            lines = []
            current_line = ""
            for word in words:
                test = current_line + (" " if current_line else "") + word
                if self.font_small.size(test)[0] > rpanel_w - 55:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
                else:
                    current_line = test
            if current_line:
                lines.append(current_line)

            for i, line in enumerate(lines):
                line_surf = self.font_small.render(line, True, color)
                surface.blit(line_surf, (rpanel_x + 35, ry + i * 16))
            ry += max(1, len(lines)) * 16 + 8

            if ry > rpanel_y + rpanel_h - 80:
                break  # prevent overflow

        # ── Bottleneck section ────────────────────────────────────────
        ry = max(ry, rpanel_y + rpanel_h - 70)
        pygame.draw.line(surface, self.BORDER,
                         (rpanel_x + 10, ry), (rpanel_x + rpanel_w - 10, ry))
        ry += 8

        bn_name, bn_desc = game_stats.get_bottleneck()
        bn_hdr = self.font_header.render(f"Bottleneck: {bn_name}", True,
                                         self.RED if bn_name != "None" else self.GREEN)
        surface.blit(bn_hdr, (rpanel_x + 15, ry))
        ry += 22

        bn_desc_surf = self.font_small.render(bn_desc, True, self.DIM)
        surface.blit(bn_desc_surf, (rpanel_x + 15, ry))

        # ── Continue button ───────────────────────────────────────────
        btn_w, btn_h = 200, 45
        self.btn_rect = pygame.Rect(
            cur_w // 2 - btn_w // 2,
            cur_h - 65,
            btn_w, btn_h
        )
        
        btn_color = self.GOLD if not self.btn_hovered else (225, 146, 113)
        pygame.draw.rect(surface, btn_color, self.btn_rect, border_radius=15)
        pygame.draw.rect(surface, self.PANEL_BG, self.btn_rect, 2, border_radius=15)
        btn_text = self.font_btn.render("Continue", True, self.PANEL_BG)
        btn_text_rect = btn_text.get_rect(center=self.btn_rect.center)
        surface.blit(btn_text, btn_text_rect)
