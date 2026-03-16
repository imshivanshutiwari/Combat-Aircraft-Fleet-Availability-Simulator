# Combat Aircraft Fleet — Pygame Live Animated Simulation

A real-time, visually stunning 2D animated simulation of a military air base
using Pygame for rendering and SimPy for discrete event simulation.

## What You See

- **Top-down satellite view** of a military air base at night
- **12 fighter jet sprites** drawn with polygon shapes — color-coded by status
- **Animated runway** with scrolling dashes during takeoff/landing
- **Three maintenance bays** (O-level, I-level, Depot) with stick-figure technicians
- **Parts warehouse** with real-time stock level bar graphs
- **Three circular gauges** for MCR, FMCR, and sortie tempo
- **Scrolling event log** with color-coded military events
- **Afterburner particle effects**, failure flashes, and parts arrival sparkles

## Running

```bash
pip install -r requirements.txt
python main.py
```

## Keyboard Shortcuts

| Key     | Action               |
|---------|----------------------|
| SPACE   | Pause / Resume       |
| S       | Toggle Surge Mode    |
| R       | Reset Simulation     |
| 1       | Speed 30x            |
| 2       | Speed 60x (default)  |
| 3       | Speed 120x           |
| 4       | Speed 300x           |
| F       | Toggle Fullscreen    |
| ESC     | Quit                 |

## Architecture

Two threads run concurrently:
- **SimPy thread**: Runs the full discrete event simulation (Weibull failures,
  lognormal repairs, (r,Q) inventory, shift scheduling)
- **Pygame thread** (main): Reads shared state at 60 FPS and renders all visuals

Communication is via a thread-safe `SharedState` object with `threading.Lock()`.

## Aircraft Status Colors

| Color          | Status                        |
|---------------|-------------------------------|
| Bright Green  | FMC (Fully Mission Capable)   |
| Yellow        | PMC (Partially Mission Capable)|
| Red           | NMC (In Maintenance)          |
| Orange Blink  | NMC (Parts Awaiting - PAM)    |
| White         | On Sortie                     |
| Blue          | Being Towed to Maintenance    |
| Grey          | In Depot (Off-Base)           |
