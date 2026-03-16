"""
Maintenance bay renderer.

Draws the three maintenance bays (O-level, I-level, Depot) with
technician figures, capacity indicators, and active repair info.
"""

import pygame
import math
from assets.colors import (
    BAY_O_LEVEL, BAY_I_LEVEL, BAY_DEPOT, BAY_BORDER,
    TECHNICIAN_COLOR, WRENCH_COLOR, QUESTION_MARK_COLOR,
    HUD_TEXT, HUD_TEXT_DIM,
)

BAY_WIDTH = 160
BAY_HEIGHT = 120

BAY_CONFIGS = {
    'o_level': {'color': BAY_O_LEVEL, 'label': 'O-LEVEL'},
    'i_level': {'color': BAY_I_LEVEL, 'label': 'I-LEVEL'},
    'depot':   {'color': BAY_DEPOT,   'label': 'DEPOT'},
}


class MaintenanceBayRenderer:
    """Draws maintenance bays with technicians and status indicators."""

    def __init__(self, positions):
        """
        Parameters
        ----------
        positions : dict
            Mapping bay_name → (x, y) top-left corner.
        """
        self.positions = positions
        self.wrench_angle = 0  # Rotating wrench animation

    def update(self, dt):
        """Update animations."""
        self.wrench_angle += dt * 180  # degrees per second

    def draw(self, surface, bay_states):
        """
        Draw all three maintenance bays.

        Parameters
        ----------
        surface : pygame.Surface
            Target surface.
        bay_states : dict
            Bay state data from SharedState.
        """
        for bay_name, config in BAY_CONFIGS.items():
            if bay_name not in self.positions:
                continue
            x, y = self.positions[bay_name]
            state = bay_states.get(bay_name, {})
            self._draw_one_bay(surface, x, y, config, state)

    def _draw_one_bay(self, surface, x, y, config, state):
        """Draw a single maintenance bay."""
        color = config['color']
        label = config['label']
        occupancy = state.get('occupancy', 0)
        max_cap = state.get('max_capacity', 8)
        tech_count = state.get('technician_count', 0)
        active_repairs = state.get('active_repairs', [])

        # Bay rectangle with border
        rect = pygame.Rect(x, y, BAY_WIDTH, BAY_HEIGHT)
        pygame.draw.rect(surface, color, rect)
        pygame.draw.rect(surface, BAY_BORDER, rect, 2)

        # Label
        font = pygame.font.Font(None, 16)
        label_surf = font.render(label, True, HUD_TEXT)
        surface.blit(label_surf, (x + 5, y + 3))

        # Capacity indicator
        cap_text = f"{occupancy}/{max_cap}"
        cap_surf = font.render(cap_text, True, HUD_TEXT_DIM)
        surface.blit(cap_surf, (x + BAY_WIDTH - 35, y + 3))

        # Draw technician stick figures
        tech_y = y + 25
        for i in range(min(tech_count, 12)):
            tx = x + 10 + (i % 6) * 24
            ty = tech_y + (i // 6) * 30
            self._draw_technician(surface, tx, ty, working=(i < occupancy))

        # Active repairs list
        if active_repairs:
            small_font = pygame.font.Font(None, 12)
            repair_text = ", ".join(f"AC-{rid:02d}" for rid in active_repairs[:3])
            repair_surf = small_font.render(repair_text, True, HUD_TEXT_DIM)
            surface.blit(repair_surf, (x + 5, y + BAY_HEIGHT - 14))

    def _draw_technician(self, surface, x, y, working=False):
        """Draw a small stick figure technician."""
        # Head
        pygame.draw.circle(surface, TECHNICIAN_COLOR, (x, y), 3)
        # Body
        pygame.draw.line(surface, TECHNICIAN_COLOR, (x, y + 3), (x, y + 10), 1)
        # Legs
        pygame.draw.line(surface, TECHNICIAN_COLOR, (x, y + 10), (x - 3, y + 15), 1)
        pygame.draw.line(surface, TECHNICIAN_COLOR, (x, y + 10), (x + 3, y + 15), 1)
        # Arms
        pygame.draw.line(surface, TECHNICIAN_COLOR, (x, y + 5), (x - 4, y + 8), 1)
        pygame.draw.line(surface, TECHNICIAN_COLOR, (x, y + 5), (x + 4, y + 8), 1)

        if working:
            # Animated wrench
            wrench_len = 5
            angle_rad = math.radians(self.wrench_angle)
            wx = x + 6 + int(wrench_len * math.cos(angle_rad))
            wy = y + 5 + int(wrench_len * math.sin(angle_rad))
            pygame.draw.line(surface, WRENCH_COLOR, (x + 6, y + 5), (wx, wy), 1)
        else:
            # Question mark above head
            small_font = pygame.font.Font(None, 12)
            q_surf = small_font.render("?", True, QUESTION_MARK_COLOR)
            surface.blit(q_surf, (x - 2, y - 12))
