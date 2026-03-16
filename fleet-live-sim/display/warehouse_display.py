"""
Warehouse display renderer.

Shows four bar graphs for spare parts stock levels with color coding
and reorder indicators.
"""

import pygame
from assets.colors import (
    WAREHOUSE_BG, WAREHOUSE_BORDER,
    STOCK_GREEN, STOCK_AMBER, STOCK_RED, STOCK_EMPTY_PULSE,
    HUD_TEXT, HUD_TEXT_DIM,
)

BAR_WIDTH = 30
BAR_MAX_HEIGHT = 80
PART_NAMES = ['engine', 'avionics', 'hydraulics', 'airframe']
PART_LABELS = ['ENG', 'AVI', 'HYD', 'AFR']
MAX_STOCK = 15  # Visual max for bar scaling


class WarehouseDisplay:
    """Draws the spare parts warehouse with stock level bars."""

    def __init__(self, x, y):
        """
        Parameters
        ----------
        x, y : int
            Top-left corner of the warehouse panel.
        """
        self.x = x
        self.y = y
        self.width = 200
        self.height = 140
        self.pulse_phase = 0

    def update(self, dt):
        """Update pulse animation for empty stock."""
        self.pulse_phase += dt * 4  # Pulse frequency

    def draw(self, surface, inventory_levels):
        """
        Draw the warehouse panel with stock bars.

        Parameters
        ----------
        surface : pygame.Surface
            Target surface.
        inventory_levels : dict
            Stock data from SharedState.
        """
        # Background panel
        rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, WAREHOUSE_BG, rect)
        pygame.draw.rect(surface, WAREHOUSE_BORDER, rect, 2)

        # Title
        font = pygame.font.Font(None, 16)
        title = font.render("PARTS WAREHOUSE", True, HUD_TEXT)
        surface.blit(title, (self.x + 10, self.y + 5))

        # Draw bars
        bar_start_x = self.x + 25
        bar_y_bottom = self.y + self.height - 20
        spacing = 45

        for i, (part_name, label) in enumerate(zip(PART_NAMES, PART_LABELS)):
            data = inventory_levels.get(part_name, {})
            stock = data.get('stock', 0)
            reorder_point = data.get('reorder_point', 2)
            reorder_pending = data.get('reorder_pending', False)

            bx = bar_start_x + i * spacing
            stock_fraction = min(1.0, stock / MAX_STOCK)
            bar_height = int(stock_fraction * BAR_MAX_HEIGHT)

            # Determine bar color
            if stock == 0:
                # Pulsing red
                import math
                pulse = abs(math.sin(self.pulse_phase))
                bar_color = (
                    int(STOCK_RED[0] + (STOCK_EMPTY_PULSE[0] - STOCK_RED[0]) * pulse),
                    int(STOCK_RED[1] + (STOCK_EMPTY_PULSE[1] - STOCK_RED[1]) * pulse),
                    int(STOCK_RED[2] + (STOCK_EMPTY_PULSE[2] - STOCK_RED[2]) * pulse),
                )
            elif stock <= reorder_point:
                bar_color = STOCK_AMBER
            else:
                bar_color = STOCK_GREEN

            # Draw bar background (empty)
            bg_rect = pygame.Rect(bx, bar_y_bottom - BAR_MAX_HEIGHT,
                                  BAR_WIDTH, BAR_MAX_HEIGHT)
            pygame.draw.rect(surface, (20, 25, 35), bg_rect)

            # Draw filled bar
            if bar_height > 0:
                fill_rect = pygame.Rect(bx, bar_y_bottom - bar_height,
                                        BAR_WIDTH, bar_height)
                pygame.draw.rect(surface, bar_color, fill_rect)

            # Reorder point line
            rp_fraction = min(1.0, reorder_point / MAX_STOCK)
            rp_y = bar_y_bottom - int(rp_fraction * BAR_MAX_HEIGHT)
            pygame.draw.line(surface, STOCK_AMBER,
                             (bx - 2, rp_y), (bx + BAR_WIDTH + 2, rp_y), 1)

            # Stock number
            small_font = pygame.font.Font(None, 14)
            stock_surf = small_font.render(str(stock), True, HUD_TEXT)
            stock_rect = stock_surf.get_rect(
                center=(bx + BAR_WIDTH // 2, bar_y_bottom - bar_height - 8))
            surface.blit(stock_surf, stock_rect)

            # Label
            label_surf = small_font.render(label, True, HUD_TEXT_DIM)
            label_rect = label_surf.get_rect(
                center=(bx + BAR_WIDTH // 2, bar_y_bottom + 10))
            surface.blit(label_surf, label_rect)

            # Reorder pending indicator
            if reorder_pending:
                tiny_font = pygame.font.Font(None, 10)
                ro_surf = tiny_font.render("REORDER", True, STOCK_AMBER)
                surface.blit(ro_surf, (bx, bar_y_bottom - BAR_MAX_HEIGHT - 12))
