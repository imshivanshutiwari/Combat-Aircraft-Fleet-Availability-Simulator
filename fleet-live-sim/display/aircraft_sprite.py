"""
Aircraft sprite renderer — draws fighter jet silhouettes using pygame.draw.

All shapes are drawn with polygon calls — no image files required.
"""

import pygame
import math
from assets.colors import STATUS_COLORS, STATUS_GLOW_COLORS, PARTICLE_AFTERBURNER


def _lerp_color(c1, c2, t):
    """Linearly interpolate between two RGB tuples."""
    t = max(0.0, min(1.0, t))
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


class AircraftSprite:
    """
    Draws a top-down fighter jet silhouette using pygame polygons.

    The jet is approximately 40x25 pixels, composed of:
    - Fuselage: pointed elongated hexagon
    - Wings: two swept triangles
    - Tail: small triangle at rear
    - Engine nacelles: two small rectangles under wings
    """

    # Base polygon points (centered at origin, pointing left)
    FUSELAGE = [
        (-20, 0),   # nose tip
        (-12, -4),  # upper nose
        (5, -5),    # upper mid
        (18, -3),   # upper rear
        (18, 3),    # lower rear
        (5, 5),     # lower mid
        (-12, 4),   # lower nose
    ]

    LEFT_WING = [
        (-2, -5),
        (10, -14),
        (14, -12),
        (8, -5),
    ]

    RIGHT_WING = [
        (-2, 5),
        (10, 14),
        (14, 12),
        (8, 5),
    ]

    TAIL = [
        (14, -2),
        (20, -8),
        (22, -6),
        (18, -2),
    ]

    TAIL_LOWER = [
        (14, 2),
        (20, 8),
        (22, 6),
        (18, 2),
    ]

    NACELLE_LEFT = [
        (2, -7), (8, -7), (8, -5), (2, -5),
    ]

    NACELLE_RIGHT = [
        (2, 5), (8, 5), (8, 7), (2, 7),
    ]

    def __init__(self):
        self.flame_frame = 0

    def draw(self, surface, x, y, status, old_status, heading,
             transition_progress, afterburner_active, ac_id):
        """
        Draw the aircraft sprite at position (x, y).

        Parameters
        ----------
        surface : pygame.Surface
            Target surface to draw on.
        x, y : float
            Center position.
        status : str
            Current aircraft status for color.
        old_status : str
            Previous status for color blending.
        heading : float
            Rotation angle in degrees (0 = pointing left).
        transition_progress : float
            0.0 to 1.0 for smooth color transitions.
        afterburner_active : bool
            Whether to draw afterburner flames.
        ac_id : int
            Aircraft ID for labeling.
        """
        # Determine color with smooth transition
        current_color = STATUS_COLORS.get(status, (150, 150, 150))
        old_color = STATUS_COLORS.get(old_status, current_color)
        color = _lerp_color(old_color, current_color, transition_progress)

        glow_color = STATUS_GLOW_COLORS.get(status, (40, 40, 40))

        # Draw soft glow effect (larger dim circle behind)
        glow_surf = pygame.Surface((60, 60), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*glow_color, 60), (30, 30), 28)
        surface.blit(glow_surf, (int(x) - 30, int(y) - 30))

        # Transform and draw all polygons
        cos_a = math.cos(math.radians(heading))
        sin_a = math.sin(math.radians(heading))

        def transform(points):
            result = []
            for px, py in points:
                rx = px * cos_a - py * sin_a + x
                ry = px * sin_a + py * cos_a + y
                result.append((int(rx), int(ry)))
            return result

        # Draw all parts
        # Fuselage
        pygame.draw.polygon(surface, color, transform(self.FUSELAGE))
        pygame.draw.polygon(surface, _darken(color, 0.6), transform(self.FUSELAGE), 1)

        # Wings
        pygame.draw.polygon(surface, _darken(color, 0.85), transform(self.LEFT_WING))
        pygame.draw.polygon(surface, _darken(color, 0.85), transform(self.RIGHT_WING))

        # Tail
        pygame.draw.polygon(surface, _darken(color, 0.7), transform(self.TAIL))
        pygame.draw.polygon(surface, _darken(color, 0.7), transform(self.TAIL_LOWER))

        # Nacelles
        pygame.draw.polygon(surface, _darken(color, 0.5), transform(self.NACELLE_LEFT))
        pygame.draw.polygon(surface, _darken(color, 0.5), transform(self.NACELLE_RIGHT))

        # Afterburner flames
        if afterburner_active:
            self.flame_frame += 1
            for i in range(3):
                flame_len = 8 + (self.flame_frame + i * 7) % 12
                flame_width = 3 + (self.flame_frame + i * 3) % 4
                flame_color = PARTICLE_AFTERBURNER[i % len(PARTICLE_AFTERBURNER)]
                flame_points = [
                    (18, -2 - flame_width // 2 + i * 2),
                    (18 + flame_len, i * 2),
                    (18, 2 + flame_width // 2 + i * 2),
                ]
                pygame.draw.polygon(surface, flame_color, transform(flame_points))

        # PAM blinking effect
        if status == 'NMC_parts':
            if (pygame.time.get_ticks() // 500) % 2 == 0:
                blink_surf = pygame.Surface((50, 30), pygame.SRCALPHA)
                pygame.draw.ellipse(blink_surf, (255, 140, 0, 80), (0, 0, 50, 30))
                surface.blit(blink_surf, (int(x) - 25, int(y) - 15))

        # Aircraft ID label
        font = pygame.font.Font(None, 14)
        label = font.render(f"AC-{ac_id:02d}", True, (180, 200, 220))
        surface.blit(label, (int(x) - 14, int(y) + 16))


def _darken(color, factor):
    """Darken a color by a factor (0.0 = black, 1.0 = unchanged)."""
    return (
        int(color[0] * factor),
        int(color[1] * factor),
        int(color[2] * factor),
    )
