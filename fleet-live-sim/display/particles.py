"""
Particle effects system for the Fleet Live Simulation.

Manages particles for afterburner, failure flashes, parts arrival,
and shift change effects.
"""

import pygame
import random
import math
from assets.colors import PARTICLE_AFTERBURNER, PARTICLE_SMOKE


class Particle:
    """
    A single visual particle.

    Attributes
    ----------
    x, y : float
        Position.
    vx, vy : float
        Velocity (pixels per frame).
    lifetime : float
        Remaining lifetime in seconds.
    max_lifetime : float
        Initial lifetime for alpha calculation.
    color : tuple
        RGB color.
    size : float
        Current radius in pixels.
    """

    def __init__(self, x, y, vx, vy, lifetime, color, size):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.color = color
        self.size = size

    def update(self, dt):
        """Advance particle by dt seconds."""
        self.x += self.vx * dt * 60
        self.y += self.vy * dt * 60
        self.lifetime -= dt
        # Size grows slightly as particle ages
        age_fraction = 1.0 - (self.lifetime / self.max_lifetime)
        self.size = self.size * (1.0 + age_fraction * 0.5)

    def is_alive(self):
        """Check if particle still has lifetime remaining."""
        return self.lifetime > 0

    def get_alpha(self):
        """Get alpha (0-255) based on remaining lifetime."""
        if self.max_lifetime <= 0:
            return 0
        return int(255 * (self.lifetime / self.max_lifetime))


class ParticleSystem:
    """
    Manages all active particles and provides emission methods.
    """

    def __init__(self):
        self.particles = []
        self._rng = random.Random(42)

    def emit_afterburner(self, x, y):
        """
        Emit afterburner particles at position (x, y).

        Creates 5 particles per call with backward velocity spread.
        """
        for _ in range(5):
            angle = math.pi + self._rng.uniform(-0.4, 0.4)
            speed = self._rng.uniform(2.0, 5.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            color = self._rng.choice(PARTICLE_AFTERBURNER)
            size = self._rng.uniform(1.5, 3.5)
            lifetime = self._rng.uniform(0.15, 0.35)
            self.particles.append(Particle(x, y, vx, vy, lifetime, color, size))

    def emit_failure_flash(self, x, y):
        """
        Emit a failure flash effect — red expanding circles and smoke.
        """
        # Red flash particles
        for _ in range(8):
            angle = self._rng.uniform(0, 2 * math.pi)
            speed = self._rng.uniform(1.0, 3.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            self.particles.append(Particle(
                x, y, vx, vy,
                lifetime=0.5,
                color=(255, 60, 60),
                size=self._rng.uniform(2, 5),
            ))
        # Smoke puff
        for _ in range(4):
            angle = self._rng.uniform(0, 2 * math.pi)
            speed = self._rng.uniform(0.5, 1.5)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            color = self._rng.choice(PARTICLE_SMOKE)
            self.particles.append(Particle(
                x, y, vx, vy,
                lifetime=0.8,
                color=color,
                size=self._rng.uniform(3, 7),
            ))

    def emit_parts_arrival(self, x, y):
        """
        Emit green sparkle for parts arrival at warehouse.
        """
        for _ in range(6):
            angle = self._rng.uniform(0, 2 * math.pi)
            speed = self._rng.uniform(1.0, 2.5)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - 1.5  # Upward bias
            self.particles.append(Particle(
                x, y, vx, vy,
                lifetime=0.6,
                color=(80, 255, 120),
                size=self._rng.uniform(1.5, 3),
            ))

    def emit_shift_sweep(self, y_start, y_end, x):
        """
        Emit horizontal sweep particles for shift change.
        """
        for i in range(10):
            py = y_start + (y_end - y_start) * (i / 10)
            self.particles.append(Particle(
                x, py, 3.0, 0,
                lifetime=0.4,
                color=(200, 220, 255),
                size=2,
            ))

    def update(self, dt):
        """Update all particles and remove dead ones."""
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.is_alive()]

    def draw(self, surface):
        """Draw all particles to surface."""
        for p in self.particles:
            alpha = p.get_alpha()
            size = max(1, int(p.size))
            if alpha > 10:
                particle_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(
                    particle_surf,
                    (*p.color, alpha),
                    (size, size),
                    size,
                )
                surface.blit(particle_surf, (int(p.x) - size, int(p.y) - size))
