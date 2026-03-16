"""
Main renderer — orchestrates all display components each frame.

Owns the pygame window (1400x800) and calls sub-renderers in order:
1. Fill background
2. Draw runway
3. Draw parking spots
4. Draw maintenance bays
5. Draw warehouse
6. Update and draw particles
7. Draw aircraft sprites (with smooth movement)
8. Draw HUD (gauges, time, status)
9. Draw event log
10. Draw control panel
11. Draw surge vignette if active
12. pygame.display.flip()
"""

import pygame
import math
from engine.shared_state import SharedState
from display.aircraft_sprite import AircraftSprite
from display.particles import ParticleSystem
from display.hud import HUD
from display.event_log import EventLog
from display.maintenance_bay import MaintenanceBayRenderer
from display.warehouse_display import WarehouseDisplay
from display.controls import ControlPanel
from assets.colors import (
    BACKGROUND, RUNWAY_COLOR, RUNWAY_LINE,
    PARKING_SPOT, PARKING_OUTLINE,
    SURGE_TINT, HUD_TEXT_DIM,
)

SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 800
FPS = 60

# Movement speed for aircraft (pixels per second)
AIRCRAFT_MOVE_SPEED = 200.0
COLOR_TRANSITION_SPEED = 2.0  # Full transition in 0.5 seconds


class Renderer:
    """
    Main display orchestrator.

    Creates the pygame window and renders all visual components.
    """

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Combat Aircraft Fleet — Live Simulation")
        self.screen = pygame.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            pygame.RESIZABLE,
        )
        self.clock = pygame.time.Clock()
        self.fullscreen = False

        # Sub-renderers
        self.aircraft_sprite = AircraftSprite()
        self.particle_system = ParticleSystem()
        self.hud = HUD(SCREEN_WIDTH)
        self.event_log = EventLog(SCREEN_WIDTH - 340, 110)
        self.bay_renderer = MaintenanceBayRenderer(SharedState.BAY_POSITIONS)
        self.warehouse = WarehouseDisplay(
            SharedState.WAREHOUSE_X, SharedState.WAREHOUSE_Y,
        )
        self.controls = ControlPanel(SCREEN_WIDTH, SCREEN_HEIGHT)

        # Runway dash animation
        self.runway_dash_offset = 0

        # Previous event count for detecting new events
        self.prev_event_count = 0

    def toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode."""
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.screen = pygame.display.set_mode(
                (SCREEN_WIDTH, SCREEN_HEIGHT),
                pygame.FULLSCREEN,
            )
        else:
            self.screen = pygame.display.set_mode(
                (SCREEN_WIDTH, SCREEN_HEIGHT),
                pygame.RESIZABLE,
            )

    def render_frame(self, snapshot):
        """
        Render one complete frame.

        Parameters
        ----------
        snapshot : dict
            State snapshot from SharedState.get_snapshot().

        Returns
        -------
        float
            Frame delta time in seconds.
        """
        dt = self.clock.tick(FPS) / 1000.0

        aircraft_states = snapshot['aircraft']
        bay_states = snapshot['bays']
        inventory = snapshot['inventory']
        kpi = snapshot['kpi']
        event_log_list = snapshot['event_log']
        sim_time = snapshot['sim_time']
        surge_active = snapshot['surge_active']
        paused = snapshot['paused']
        speed = snapshot['speed_multiplier']

        # 1. Fill background
        self.screen.fill(BACKGROUND)

        # 2. Draw runway
        self._draw_runway(dt, any(
            ac.get('sortie_phase') in ('taxi_out', 'takeoff', 'landing')
            for ac in aircraft_states
        ))

        # 3. Draw parking spots
        self._draw_parking_spots()

        # 4. Draw maintenance bays
        self.bay_renderer.update(dt)
        self.bay_renderer.draw(self.screen, bay_states)

        # 5. Draw warehouse
        self.warehouse.update(dt)
        self.warehouse.draw(self.screen, inventory)

        # 6. Update and draw particles
        self.particle_system.update(dt)
        # Emit afterburner particles for aircraft in takeoff
        for ac in aircraft_states:
            if ac.get('afterburner_active'):
                self.particle_system.emit_afterburner(ac['x'] + 18, ac['y'])
        self.particle_system.draw(self.screen)

        # 7. Draw aircraft (with smooth movement)
        for ac in aircraft_states:
            # Smooth position interpolation
            dx = ac['target_x'] - ac['x']
            dy = ac['target_y'] - ac['y']
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 1.0:
                move = min(dist, AIRCRAFT_MOVE_SPEED * dt)
                ac['x'] += (dx / dist) * move
                ac['y'] += (dy / dist) * move

            # Color transition progress
            if ac.get('color_transition_progress', 1.0) < 1.0:
                ac['color_transition_progress'] = min(
                    1.0,
                    ac['color_transition_progress'] + COLOR_TRANSITION_SPEED * dt,
                )

            # Don't draw if off screen (airborne)
            if -100 < ac['x'] < SCREEN_WIDTH + 100:
                self.aircraft_sprite.draw(
                    self.screen,
                    ac['x'], ac['y'],
                    ac.get('status', 'FMC'),
                    ac.get('old_status', 'FMC'),
                    ac.get('heading', 0),
                    ac.get('color_transition_progress', 1.0),
                    ac.get('afterburner_active', False),
                    ac.get('id', 0),
                )

        # 8. Draw HUD
        self.hud.update(dt, kpi)
        self.hud.draw(self.screen, sim_time, speed, surge_active, paused)

        # 9. Draw event log
        # Detect new events
        if len(event_log_list) != self.prev_event_count:
            self.event_log.trigger_scroll()
            self.prev_event_count = len(event_log_list)
        self.event_log.update(dt)
        self.event_log.draw(self.screen, event_log_list)

        # 10. Draw control panel
        self.controls.draw(self.screen, kpi.get('mcr_history', []))

        # 11. Surge vignette effect
        if surge_active:
            self._draw_surge_vignette()

        # 12. Flip display
        pygame.display.flip()

        return dt

    def _draw_runway(self, dt, active):
        """Draw the runway with animated center dashes."""
        rx = SharedState.RUNWAY_X
        ry = SharedState.RUNWAY_Y
        rw = SharedState.RUNWAY_WIDTH
        rh = SharedState.RUNWAY_HEIGHT

        # Runway surface
        pygame.draw.rect(self.screen, RUNWAY_COLOR,
                         (rx, ry, rw, rh))

        # Center line dashes
        if active:
            self.runway_dash_offset = (self.runway_dash_offset + dt * 100) % 30
        else:
            self.runway_dash_offset = 0

        dash_len = 15
        gap = 15
        y_center = ry + rh // 2
        x = rx + 10 - int(self.runway_dash_offset)
        while x < rx + rw - 10:
            x1 = max(rx + 5, x)
            x2 = min(rx + rw - 5, x + dash_len)
            if x2 > x1:
                pygame.draw.line(self.screen, RUNWAY_LINE,
                                 (x1, y_center), (x2, y_center), 2)
            x += dash_len + gap

        # Runway edge lines
        pygame.draw.line(self.screen, RUNWAY_LINE,
                         (rx + 5, ry + 2), (rx + rw - 5, ry + 2), 1)
        pygame.draw.line(self.screen, RUNWAY_LINE,
                         (rx + 5, ry + rh - 2), (rx + rw - 5, ry + rh - 2), 1)

        # Label
        font = pygame.font.Font(None, 14)
        label = font.render("RUNWAY", True, HUD_TEXT_DIM)
        self.screen.blit(label, (rx + rw // 2 - 20, ry + rh + 4))

    def _draw_parking_spots(self):
        """Draw the 12 parking spot rectangles."""
        for i, (px, py) in enumerate(SharedState.PARKING_POSITIONS):
            spot_rect = pygame.Rect(px - 22, py - 14, 44, 28)
            pygame.draw.rect(self.screen, PARKING_SPOT, spot_rect)
            pygame.draw.rect(self.screen, PARKING_OUTLINE, spot_rect, 1)

    def _draw_surge_vignette(self):
        """Draw red vignette at screen edges during surge."""
        vignette = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        # Top edge
        for i in range(30):
            alpha = int(40 * (1.0 - i / 30))
            pygame.draw.line(vignette, (*SURGE_TINT, alpha),
                             (0, i), (SCREEN_WIDTH, i))
        # Bottom edge
        for i in range(30):
            alpha = int(40 * (1.0 - i / 30))
            pygame.draw.line(vignette, (*SURGE_TINT, alpha),
                             (0, SCREEN_HEIGHT - i), (SCREEN_WIDTH, SCREEN_HEIGHT - i))
        # Left edge
        for i in range(20):
            alpha = int(30 * (1.0 - i / 20))
            pygame.draw.line(vignette, (*SURGE_TINT, alpha),
                             (i, 0), (i, SCREEN_HEIGHT))
        # Right edge
        for i in range(20):
            alpha = int(30 * (1.0 - i / 20))
            pygame.draw.line(vignette, (*SURGE_TINT, alpha),
                             (SCREEN_WIDTH - i, 0), (SCREEN_WIDTH - i, SCREEN_HEIGHT))
        self.screen.blit(vignette, (0, 0))
