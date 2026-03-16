"""
Thread-safe shared state for communication between SimPy and Pygame threads.

The SimPy simulation thread writes to this state every simulated hour.
The Pygame rendering thread reads from this state every frame (60 FPS).
Neither thread does the other's job — clean producer/consumer separation.
"""

import threading
import collections


class SharedState:
    """
    Thread-safe shared state dictionary for SimPy ↔ Pygame communication.

    Attributes
    ----------
    lock : threading.Lock
        Mutex protecting all state reads/writes.
    aircraft_states : list of dict
        Per-aircraft state for rendering. Each dict has keys:
        id, status, x, y, target_x, target_y,
        health_engine, health_avionics, health_hydraulics, health_airframe,
        color_transition_progress, old_status.
    bay_states : dict
        Maintenance bay occupancy. Keys: 'o_level', 'i_level', 'depot'.
        Each value is a dict with: occupancy, max_capacity,
        technician_count, active_repairs (list of aircraft IDs).
    inventory_levels : dict
        Spare parts stock. Keys: 'engine', 'avionics', 'hydraulics', 'airframe'.
        Each value is a dict with: stock, reorder_point, reorder_pending.
    kpi : dict
        Current KPIs: current_mcr, current_fmcr, current_tempo,
        mcr_history (list of last 30 daily values).
    event_log : collections.deque
        Last 8 events. Each entry: (timestamp_string, message, color_tuple).
    sim_time : float
        Current simulated time in hours.
    surge_active : bool
        Whether surge OPTEMPO is active.
    paused : bool
        Whether simulation is paused.
    speed_multiplier : int
        Simulation speed multiplier (30, 60, 120, or 300).
    reset_requested : bool
        Flag for the render thread to signal a reset.
    running : bool
        Master flag — set to False to stop both threads.
    """

    # Default parking spot positions (2 rows of 6)
    PARKING_POSITIONS = []
    for row in range(2):
        for col in range(6):
            PARKING_POSITIONS.append((
                350 + col * 100,   # x: starting at 350, spaced 100px
                200 + row * 150,   # y: two rows at y=200 and y=350
            ))

    # Maintenance bay positions
    BAY_POSITIONS = {
        'o_level': (950, 180),
        'i_level': (950, 340),
        'depot':   (950, 500),
    }

    # Runway position
    RUNWAY_X = 40
    RUNWAY_Y = 280
    RUNWAY_WIDTH = 250
    RUNWAY_HEIGHT = 40

    # Warehouse position
    WAREHOUSE_X = 1050
    WAREHOUSE_Y = 600

    def __init__(self, fleet_size=12):
        self.lock = threading.Lock()
        self.fleet_size = fleet_size

        # Aircraft states
        self.aircraft_states = []
        for i in range(fleet_size):
            px, py = self.PARKING_POSITIONS[i] if i < len(self.PARKING_POSITIONS) else (400, 400)
            self.aircraft_states.append({
                'id': i,
                'status': 'FMC',
                'old_status': 'FMC',
                'x': float(px),
                'y': float(py),
                'target_x': float(px),
                'target_y': float(py),
                'home_x': float(px),
                'home_y': float(py),
                'health_engine': 1.0,
                'health_avionics': 1.0,
                'health_hydraulics': 1.0,
                'health_airframe': 1.0,
                'color_transition_progress': 1.0,
                'afterburner_active': False,
                'heading': 0.0,
                'on_sortie': False,
                'sortie_phase': None,   # 'taxi_out', 'takeoff', 'airborne', 'landing', 'taxi_in'
            })

        # Maintenance bay states
        self.bay_states = {
            'o_level': {
                'occupancy': 0,
                'max_capacity': 8,
                'technician_count': 8,
                'active_repairs': [],
            },
            'i_level': {
                'occupancy': 0,
                'max_capacity': 4,
                'technician_count': 4,
                'active_repairs': [],
            },
            'depot': {
                'occupancy': 0,
                'max_capacity': 6,
                'technician_count': 6,
                'active_repairs': [],
            },
        }

        # Parts inventory
        self.inventory_levels = {
            'engine':     {'stock': 5,  'reorder_point': 2, 'reorder_pending': False},
            'avionics':   {'stock': 8,  'reorder_point': 3, 'reorder_pending': False},
            'hydraulics': {'stock': 10, 'reorder_point': 4, 'reorder_pending': False},
            'airframe':   {'stock': 3,  'reorder_point': 1, 'reorder_pending': False},
        }

        # KPIs
        self.kpi = {
            'current_mcr': 1.0,
            'current_fmcr': 1.0,
            'current_tempo': 0.0,
            'mcr_history': [],
        }

        # Event log (most recent 8 events)
        self.event_log = collections.deque(maxlen=8)

        # Simulation control
        self.sim_time = 0.0
        self.surge_active = False
        self.paused = False
        self.speed_multiplier = 60
        self.reset_requested = False
        self.running = True

    def update_aircraft(self, aircraft_id, **kwargs):
        """
        Update an aircraft's state (called from SimPy thread).

        Parameters
        ----------
        aircraft_id : int
            Index of the aircraft to update.
        **kwargs : dict
            Key-value pairs to update in the aircraft state dict.
        """
        with self.lock:
            if 0 <= aircraft_id < len(self.aircraft_states):
                ac = self.aircraft_states[aircraft_id]
                # Track status transitions for color blending
                if 'status' in kwargs and kwargs['status'] != ac['status']:
                    ac['old_status'] = ac['status']
                    ac['color_transition_progress'] = 0.0
                ac.update(kwargs)

    def update_bay(self, bay_name, **kwargs):
        """Update a maintenance bay's state."""
        with self.lock:
            if bay_name in self.bay_states:
                self.bay_states[bay_name].update(kwargs)

    def update_inventory(self, subsystem_name, **kwargs):
        """Update inventory levels for a subsystem."""
        with self.lock:
            if subsystem_name in self.inventory_levels:
                self.inventory_levels[subsystem_name].update(kwargs)

    def update_kpi(self, **kwargs):
        """Update KPI values."""
        with self.lock:
            self.kpi.update(kwargs)

    def add_event(self, timestamp_str, message, color):
        """
        Add an event to the log.

        Parameters
        ----------
        timestamp_str : str
            Formatted timestamp, e.g. "DAY 047 — 14:32".
        message : str
            Event description.
        color : tuple
            RGB color tuple for the event text.
        """
        with self.lock:
            self.event_log.appendleft((timestamp_str, message, color))

    def get_snapshot(self):
        """
        Get a thread-safe copy of all state for rendering.

        Returns
        -------
        dict
            Deep-ish copy of all state fields.
        """
        with self.lock:
            return {
                'aircraft': [dict(ac) for ac in self.aircraft_states],
                'bays': {k: dict(v) for k, v in self.bay_states.items()},
                'inventory': {k: dict(v) for k, v in self.inventory_levels.items()},
                'kpi': dict(self.kpi),
                'event_log': list(self.event_log),
                'sim_time': self.sim_time,
                'surge_active': self.surge_active,
                'paused': self.paused,
                'speed_multiplier': self.speed_multiplier,
            }

    def format_sim_time(self, hours=None):
        """
        Format simulation time as military-style string.

        Parameters
        ----------
        hours : float, optional
            Time in hours. If None, uses current sim_time.

        Returns
        -------
        str
            Formatted string like "DAY 047 — 14:32".
        """
        if hours is None:
            hours = self.sim_time
        day = int(hours // 24) + 1
        hour_of_day = int(hours % 24)
        minute = int((hours % 1) * 60)
        return f"DAY {day:03d} — {hour_of_day:02d}:{minute:02d}"
