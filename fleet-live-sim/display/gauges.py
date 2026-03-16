"""
Circular gauge widgets for the HUD display.

Draws arc-based gauges with animated needles for MCR, FMCR, and tempo.
"""

import pygame
import math
from assets.colors import (
    GAUGE_GREEN, GAUGE_AMBER, GAUGE_RED,
    GAUGE_BG, GAUGE_RING, GAUGE_TICK, GAUGE_NEEDLE, HUD_TEXT,
)


class CircularGauge:
    """
    Draws one circular instrument gauge with arc, ticks, needle, and label.

    Parameters
    ----------
    center_x, center_y : int
        Center position on screen.
    radius : int
        Gauge radius in pixels.
    label : str
        Text label below gauge.
    unit : str
        Unit string (e.g., '%').
    min_val, max_val : float
        Value range.
    green_threshold : float
        Value above which gauge is green.
    amber_threshold : float
        Value above which gauge is amber (below green).
    """

    # Arc spans from 225 degrees (lower-left) to -45 degrees (lower-right)
    ARC_START_DEG = 225
    ARC_END_DEG = -45
    ARC_SPAN_DEG = 270

    def __init__(self, center_x, center_y, radius, label, unit='%',
                 min_val=0, max_val=100,
                 green_threshold=75, amber_threshold=60):
        self.cx = center_x
        self.cy = center_y
        self.radius = radius
        self.label = label
        self.unit = unit
        self.min_val = min_val
        self.max_val = max_val
        self.green_threshold = green_threshold
        self.amber_threshold = amber_threshold
        self.current_display_value = min_val  # For smooth animation
        self.target_value = min_val

    def set_value(self, value):
        """Set target value (needle will animate toward it)."""
        self.target_value = max(self.min_val, min(self.max_val, value))

    def update(self, dt):
        """Smoothly animate needle toward target."""
        diff = self.target_value - self.current_display_value
        self.current_display_value += diff * min(1.0, dt * 5.0)

    def draw(self, surface):
        """Draw the complete gauge on the surface."""
        # Background circle
        pygame.draw.circle(surface, GAUGE_BG, (self.cx, self.cy), self.radius)
        pygame.draw.circle(surface, GAUGE_RING, (self.cx, self.cy), self.radius, 2)

        # Draw colored arc
        value_fraction = (self.current_display_value - self.min_val) / (self.max_val - self.min_val)
        value_fraction = max(0.0, min(1.0, value_fraction))

        # Determine color
        if self.current_display_value >= self.green_threshold:
            arc_color = GAUGE_GREEN
        elif self.current_display_value >= self.amber_threshold:
            arc_color = GAUGE_AMBER
        else:
            arc_color = GAUGE_RED

        # Draw arc segments
        arc_extent = value_fraction * self.ARC_SPAN_DEG
        self._draw_arc(surface, arc_color, arc_extent)

        # Draw tick marks at 0%, 25%, 50%, 75%, 100%
        for pct in [0.0, 0.25, 0.5, 0.75, 1.0]:
            angle_deg = self.ARC_START_DEG - pct * self.ARC_SPAN_DEG
            angle_rad = math.radians(angle_deg)
            inner_r = self.radius - 8
            outer_r = self.radius - 2
            x1 = self.cx + int(inner_r * math.cos(angle_rad))
            y1 = self.cy - int(inner_r * math.sin(angle_rad))
            x2 = self.cx + int(outer_r * math.cos(angle_rad))
            y2 = self.cy - int(outer_r * math.sin(angle_rad))
            pygame.draw.line(surface, GAUGE_TICK, (x1, y1), (x2, y2), 2)

        # Draw needle
        needle_angle_deg = self.ARC_START_DEG - value_fraction * self.ARC_SPAN_DEG
        needle_angle_rad = math.radians(needle_angle_deg)
        needle_len = self.radius - 14
        nx = self.cx + int(needle_len * math.cos(needle_angle_rad))
        ny = self.cy - int(needle_len * math.sin(needle_angle_rad))
        pygame.draw.line(surface, GAUGE_NEEDLE, (self.cx, self.cy), (nx, ny), 2)

        # Center dot
        pygame.draw.circle(surface, GAUGE_NEEDLE, (self.cx, self.cy), 4)

        # Value text in center
        font = pygame.font.Font(None, 20)
        val_text = f"{self.current_display_value:.1f}{self.unit}"
        text_surf = font.render(val_text, True, arc_color)
        text_rect = text_surf.get_rect(center=(self.cx, self.cy + 16))
        surface.blit(text_surf, text_rect)

        # Label below gauge
        label_font = pygame.font.Font(None, 16)
        label_surf = label_font.render(self.label, True, HUD_TEXT)
        label_rect = label_surf.get_rect(center=(self.cx, self.cy + self.radius + 12))
        surface.blit(label_surf, label_rect)

    def _draw_arc(self, surface, color, extent_deg):
        """Draw a colored arc using line segments."""
        if extent_deg <= 0:
            return
        n_segments = max(2, int(extent_deg / 3))
        points = []
        for i in range(n_segments + 1):
            frac = i / n_segments
            angle_deg = self.ARC_START_DEG - frac * extent_deg
            angle_rad = math.radians(angle_deg)
            r = self.radius - 5
            px = self.cx + int(r * math.cos(angle_rad))
            py = self.cy - int(r * math.sin(angle_rad))
            points.append((px, py))
        if len(points) >= 2:
            pygame.draw.lines(surface, color, False, points, 3)
