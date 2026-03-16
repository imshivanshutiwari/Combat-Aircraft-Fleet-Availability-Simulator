"""
Scrolling event log for the HUD.

Shows the last 8 simulation events with slide-in / slide-out animation.
"""

import pygame
from assets.colors import HUD_BG, HUD_BORDER, HUD_TEXT_DIM

LOG_WIDTH = 320
LOG_HEIGHT = 160
LINE_HEIGHT = 18


class EventLog:
    """
    Renders a scrolling event log panel.

    Parameters
    ----------
    x, y : int
        Top-left corner position.
    """

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.scroll_offset = 0  # For slide animation

    def update(self, dt):
        """Smooth scroll animation (decays over time)."""
        if self.scroll_offset > 0:
            self.scroll_offset = max(0, self.scroll_offset - dt * 100)

    def draw(self, surface, event_log_list):
        """
        Draw the event log panel.

        Parameters
        ----------
        surface : pygame.Surface
            Target surface.
        event_log_list : list
            List of (timestamp, message, color) tuples.
        """
        # Background panel
        rect = pygame.Rect(self.x, self.y, LOG_WIDTH, LOG_HEIGHT)
        pygame.draw.rect(surface, HUD_BG, rect)
        pygame.draw.rect(surface, HUD_BORDER, rect, 1)

        # Title
        title_font = pygame.font.Font(None, 14)
        title_surf = title_font.render("EVENT LOG", True, HUD_TEXT_DIM)
        surface.blit(title_surf, (self.x + 5, self.y + 3))

        # Clip to panel
        clip_rect = pygame.Rect(self.x + 2, self.y + 16,
                                LOG_WIDTH - 4, LOG_HEIGHT - 20)
        old_clip = surface.get_clip()
        surface.set_clip(clip_rect)

        # Draw events
        font = pygame.font.Font(None, 13)
        for i, event in enumerate(event_log_list):
            if i >= 8:
                break
            timestamp, message, color = event
            ey = self.y + 18 + i * LINE_HEIGHT - int(self.scroll_offset)

            if ey < self.y + 14 or ey > self.y + LOG_HEIGHT:
                continue

            # Timestamp
            ts_surf = font.render(timestamp[-5:], True, HUD_TEXT_DIM)
            surface.blit(ts_surf, (self.x + 5, ey))

            # Message (truncated to fit)
            msg_text = message[:38]
            msg_surf = font.render(msg_text, True, color)
            surface.blit(msg_surf, (self.x + 48, ey))

        surface.set_clip(old_clip)

    def trigger_scroll(self):
        """Trigger a scroll animation when a new event arrives."""
        self.scroll_offset = LINE_HEIGHT
