"""
HUD overlay for the Fleet Live Simulation.

Renders the top-bar with simulated time, gauges, and informational text.
"""

import pygame
from assets.colors import HUD_BG, HUD_TEXT, HUD_TEXT_DIM, HUD_BORDER, SURGE_TEXT
from display.gauges import CircularGauge


class HUD:
    """
    Head-Up Display overlay.

    Shows simulated time, MCR/FMCR/Tempo gauges, and status indicators.

    Parameters
    ----------
    screen_width : int
        Screen width for layout calculations.
    """

    def __init__(self, screen_width):
        self.screen_width = screen_width
        self.bar_height = 100

        # Create three gauges
        gauge_y = 52
        gauge_r = 38
        spacing = screen_width // 4

        self.mcr_gauge = CircularGauge(
            spacing, gauge_y, gauge_r,
            'MCR', '%', 0, 100, 75, 60,
        )
        self.fmcr_gauge = CircularGauge(
            spacing * 2, gauge_y, gauge_r,
            'FMCR', '%', 0, 100, 75, 60,
        )
        self.tempo_gauge = CircularGauge(
            spacing * 3, gauge_y, gauge_r,
            'TEMPO', '/d', 0, 30, 15, 8,
        )

    def update(self, dt, kpi_data):
        """
        Update gauge values and animations.

        Parameters
        ----------
        dt : float
            Frame delta time in seconds.
        kpi_data : dict
            KPI values from SharedState.
        """
        self.mcr_gauge.set_value(kpi_data.get('current_mcr', 0) * 100)
        self.fmcr_gauge.set_value(kpi_data.get('current_fmcr', 0) * 100)
        self.tempo_gauge.set_value(kpi_data.get('current_tempo', 0))

        self.mcr_gauge.update(dt)
        self.fmcr_gauge.update(dt)
        self.tempo_gauge.update(dt)

    def draw(self, surface, sim_time, speed_multiplier, surge_active, paused):
        """
        Draw the complete HUD.

        Parameters
        ----------
        surface : pygame.Surface
            Target surface.
        sim_time : float
            Current simulated time in hours.
        speed_multiplier : int
            Current simulation speed.
        surge_active : bool
            Whether surge is active.
        paused : bool
            Whether simulation is paused.
        """
        # Top bar background
        bar_rect = pygame.Rect(0, 0, self.screen_width, self.bar_height)
        pygame.draw.rect(surface, HUD_BG, bar_rect)
        pygame.draw.line(surface, HUD_BORDER,
                         (0, self.bar_height), (self.screen_width, self.bar_height), 1)

        # Simulated time display (top left)
        day = int(sim_time // 24) + 1
        hour = int(sim_time % 24)
        minute = int((sim_time % 1) * 60)

        time_font = pygame.font.Font(None, 22)
        time_text = f"DAY {day:03d} — {hour:02d}:{minute:02d}"
        time_surf = time_font.render(time_text, True, HUD_TEXT)
        surface.blit(time_surf, (10, 8))

        # Speed indicator
        speed_font = pygame.font.Font(None, 16)
        speed_text = f"SPEED: {speed_multiplier}x"
        speed_surf = speed_font.render(speed_text, True, HUD_TEXT_DIM)
        surface.blit(speed_surf, (10, 28))

        # Draw gauges
        self.mcr_gauge.draw(surface)
        self.fmcr_gauge.draw(surface)
        self.tempo_gauge.draw(surface)

        # Surge indicator
        if surge_active:
            surge_font = pygame.font.Font(None, 24)
            # Pulsing effect
            ticks = pygame.time.get_ticks()
            if (ticks // 300) % 2 == 0:
                surge_surf = surge_font.render("⚡ SURGE ACTIVE ⚡", True, SURGE_TEXT)
                sw = surge_surf.get_width()
                surface.blit(surge_surf, (self.screen_width // 2 - sw // 2, 8))

        # Pause indicator
        if paused:
            pause_font = pygame.font.Font(None, 36)
            pause_surf = pause_font.render("SIMULATION PAUSED", True, HUD_TEXT)
            pw = pause_surf.get_width()
            ph = pause_surf.get_height()
            # Semi-transparent overlay
            overlay = pygame.Surface((pw + 20, ph + 10), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            cx = self.screen_width // 2 - pw // 2 - 10
            cy = self.bar_height + 20
            surface.blit(overlay, (cx, cy))
            surface.blit(pause_surf, (cx + 10, cy + 5))
