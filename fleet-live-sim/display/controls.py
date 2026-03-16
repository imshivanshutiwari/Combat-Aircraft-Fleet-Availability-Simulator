"""
Control panel for the bottom of the screen.

Renders buttons (SPEED, SURGE, PAUSE, RESET) and MCR sparklines.
"""

import pygame
from assets.colors import (
    CONTROL_BG, CONTROL_BORDER,
    BUTTON_NORMAL, BUTTON_HOVER, BUTTON_ACTIVE,
    BUTTON_SURGE, BUTTON_SURGE_ACTIVE,
    BUTTON_TEXT, HUD_TEXT, HUD_TEXT_DIM,
    GAUGE_GREEN, GAUGE_AMBER, GAUGE_RED,
)

PANEL_HEIGHT = 60


class Button:
    """
    A clickable button.

    Parameters
    ----------
    x, y : int
        Top-left position.
    width, height : int
        Button dimensions.
    label : str
        Button text.
    action : str
        Action identifier for click handling.
    toggle : bool
        Whether this is a toggle button.
    active_color : tuple
        Color when active (for toggle buttons).
    """

    def __init__(self, x, y, width, height, label, action,
                 toggle=False, active_color=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.action = action
        self.toggle = toggle
        self.active = False
        self.hovered = False
        self.active_color = active_color or BUTTON_ACTIVE

    def handle_mouse(self, mouse_pos, clicked):
        """
        Handle mouse interaction.

        Returns
        -------
        str or None
            Action string if clicked, None otherwise.
        """
        self.hovered = self.rect.collidepoint(mouse_pos)
        if clicked and self.hovered:
            if self.toggle:
                self.active = not self.active
            return self.action
        return None

    def draw(self, surface):
        """Draw the button."""
        if self.active and self.toggle:
            color = self.active_color
        elif self.hovered:
            color = BUTTON_HOVER
        else:
            color = BUTTON_NORMAL

        pygame.draw.rect(surface, color, self.rect, border_radius=4)
        pygame.draw.rect(surface, CONTROL_BORDER, self.rect, 1, border_radius=4)

        font = pygame.font.Font(None, 16)
        text_surf = font.render(self.label, True, BUTTON_TEXT)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)


class ControlPanel:
    """
    Bottom control strip with buttons and sparklines.

    Parameters
    ----------
    screen_width : int
        Screen width.
    screen_height : int
        Screen height.
    """

    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.panel_y = screen_height - PANEL_HEIGHT
        self.panel_rect = pygame.Rect(0, self.panel_y, screen_width, PANEL_HEIGHT)

        # Create buttons
        btn_y = self.panel_y + 10
        btn_h = 30
        self.buttons = [
            Button(20, btn_y, 80, btn_h, "SPEED", "speed"),
            Button(110, btn_y, 80, btn_h, "SURGE", "surge",
                   toggle=True, active_color=BUTTON_SURGE_ACTIVE),
            Button(200, btn_y, 80, btn_h, "PAUSE", "pause",
                   toggle=True),
            Button(290, btn_y, 80, btn_h, "RESET", "reset"),
        ]

        # Speed cycle
        self.speed_options = [30, 60, 120, 300]
        self.speed_index = 1  # Default 60x

    def handle_event(self, mouse_pos, clicked):
        """
        Handle mouse events and return list of actions triggered.

        Returns
        -------
        list of str
            List of action strings.
        """
        actions = []
        for button in self.buttons:
            action = button.handle_mouse(mouse_pos, clicked)
            if action:
                actions.append(action)
        return actions

    def get_current_speed(self):
        """Return current speed multiplier."""
        return self.speed_options[self.speed_index]

    def cycle_speed(self):
        """Cycle to next speed option."""
        self.speed_index = (self.speed_index + 1) % len(self.speed_options)
        self.buttons[0].label = f"{self.speed_options[self.speed_index]}x"
        return self.speed_options[self.speed_index]

    def draw(self, surface, mcr_history):
        """
        Draw the control panel.

        Parameters
        ----------
        surface : pygame.Surface
            Target surface.
        mcr_history : list
            List of daily MCR values for sparklines.
        """
        # Panel background
        pygame.draw.rect(surface, CONTROL_BG, self.panel_rect)
        pygame.draw.line(surface, CONTROL_BORDER,
                         (0, self.panel_y), (self.screen_width, self.panel_y), 1)

        # Draw buttons
        for button in self.buttons:
            button.draw(surface)

        # Draw MCR sparklines
        self._draw_sparkline(surface, 420, self.panel_y + 10, 80, 30,
                             mcr_history, "MCR 30d")

    def _draw_sparkline(self, surface, x, y, width, height, data, label):
        """Draw a small sparkline chart."""
        if not data or len(data) < 2:
            return

        # Background
        rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, (20, 25, 35), rect)
        pygame.draw.rect(surface, CONTROL_BORDER, rect, 1)

        # Label
        font = pygame.font.Font(None, 10)
        label_surf = font.render(label, True, HUD_TEXT_DIM)
        surface.blit(label_surf, (x + 2, y + 2))

        # Data points
        points = data[-30:]  # Last 30 values
        if len(points) < 2:
            return

        min_val = max(0, min(points) - 0.05)
        max_val = min(1, max(points) + 0.05)
        val_range = max_val - min_val if max_val > min_val else 1.0

        line_points = []
        for i, val in enumerate(points):
            px = x + 3 + int((i / (len(points) - 1)) * (width - 6))
            py = y + height - 3 - int(((val - min_val) / val_range) * (height - 10))
            line_points.append((px, py))

        if len(line_points) >= 2:
            # Determine color by last value
            last_val = points[-1]
            if last_val >= 0.75:
                line_color = GAUGE_GREEN
            elif last_val >= 0.60:
                line_color = GAUGE_AMBER
            else:
                line_color = GAUGE_RED
            pygame.draw.lines(surface, line_color, False, line_points, 1)
