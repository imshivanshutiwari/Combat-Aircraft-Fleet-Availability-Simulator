"""
Fleet Live Simulation — Entry Point.

Starts two threads:
1. SimPy simulation thread — runs the discrete event engine
2. Pygame render thread — runs in the main thread (required by pygame)

Keyboard shortcuts:
    SPACE — pause/resume
    S     — toggle surge mode
    R     — reset simulation
    1     — 30x speed
    2     — 60x speed (default)
    3     — 120x speed
    4     — 300x speed
    ESC   — quit
    F     — toggle fullscreen
"""

import sys
import os
import time
import json
import threading
import pygame

from engine.shared_state import SharedState
from engine.simulation import run_simulation_thread
from display.renderer import Renderer


FLEET_SIZE = 12
RANDOM_SEED = 42


def main():
    """Main entry point — starts simulation and render loop."""

    # Create shared state
    state = SharedState(fleet_size=FLEET_SIZE)

    # Start simulation thread
    sim_thread = threading.Thread(
        target=run_simulation_thread,
        args=(state, FLEET_SIZE, RANDOM_SEED),
        daemon=True,
    )
    sim_thread.start()

    # Create renderer (initialises pygame in main thread)
    renderer = Renderer()
    
    from engine.zmq_bridge import CommandSubscriber
    bridge_sub = CommandSubscriber()

    # Main event loop
    running = True
    while running:
        # Handle pygame events
        mouse_pos = pygame.mouse.get_pos()
        clicked = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                elif event.key == pygame.K_SPACE:
                    state.paused = not state.paused

                elif event.key == pygame.K_s:
                    state.surge_active = not state.surge_active
                    if state.surge_active:
                        from assets.colors import EVENT_FAILURE
                        state.add_event(
                            state.format_sim_time(),
                            "SURGE MODE ACTIVATED — Sortie tempo doubled",
                            EVENT_FAILURE,
                        )
                    else:
                        from assets.colors import EVENT_GENERAL
                        state.add_event(
                            state.format_sim_time(),
                            "SURGE MODE DEACTIVATED — Returning to peacetime tempo",
                            EVENT_GENERAL,
                        )

                elif event.key == pygame.K_r:
                    state.reset_requested = True

                elif event.key == pygame.K_1:
                    state.speed_multiplier = 30
                elif event.key == pygame.K_2:
                    state.speed_multiplier = 60
                elif event.key == pygame.K_3:
                    state.speed_multiplier = 120
                elif event.key == pygame.K_4:
                    state.speed_multiplier = 300

                elif event.key == pygame.K_f:
                    renderer.toggle_fullscreen()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    clicked = True

        # Handle control panel button clicks
        if clicked:
            actions = renderer.controls.handle_event(mouse_pos, True)
            for action in actions:
                if action == 'speed':
                    new_speed = renderer.controls.cycle_speed()
                    state.speed_multiplier = new_speed
                elif action == 'surge':
                    state.surge_active = not state.surge_active
                elif action == 'pause':
                    state.paused = not state.paused
                elif action == 'reset':
                    state.reset_requested = True
        else:
            renderer.controls.handle_event(mouse_pos, False)

        # ── BRIDGE POLLING (ZMQ) ──────────────────────────────────────────
        cmd, cmd_time = bridge_sub.check_for_command()
        if cmd:
            if cmd == 'SURGE':
                state.surge_active = not state.surge_active
                from assets.colors import EVENT_FAILURE, EVENT_GENERAL
                if state.surge_active:
                    state.add_event(state.format_sim_time(), "ZMQ BRIDGE: SURGE ACTIVATED", EVENT_FAILURE)
                else:
                    state.add_event(state.format_sim_time(), "ZMQ BRIDGE: SURGE DEACTIVATED", EVENT_GENERAL)
            elif cmd == 'PAUSE':
                state.paused = not state.paused
                from assets.colors import EVENT_GENERAL
                state.add_event(state.format_sim_time(), f"ZMQ BRIDGE: {'PAUSED' if state.paused else 'RESUMED'}", EVENT_GENERAL)

        # Get state snapshot and render
        snapshot = state.get_snapshot()
        renderer.render_frame(snapshot)

    # Cleanup
    state.running = False
    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()
