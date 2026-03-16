"""
Maintenance module for the Fleet Availability Simulator.

Models three-tier military maintenance system:
- O-level (Organisational): Squadron flight-line maintenance
- I-level (Intermediate): Base workshop maintenance
- D-level (Depot): Centralised major overhaul

Each tier has its own SimPy Resource pool. Repair times follow lognormal
distributions. Parts availability is checked before repair can begin.
"""

import simpy
import numpy as np
from src.distributions import lognormal_rvs

# ---------------------------------------------------------------------------
# Constants — Repair time parameters (lognormal: mu in log-space, sigma in log-space)
# ---------------------------------------------------------------------------
HOURS_PER_DAY = 24

REPAIR_PARAMS = {
    'O': {'mu': 4.0,   'sigma': 1.2},    # O-level: mean ~4h in log-space
    'I': {'mu': 24.0,  'sigma': 1.8},    # I-level: mean ~24h in log-space
    'D': {'mu': 480.0, 'sigma': 2.1},    # D-level: mean ~480h (20 days)
}

# Convert actual-space means to log-space mu for lognormal parameterisation
# lognormal_rvs expects mu in log-space; we use log(mean) as mu
import math
REPAIR_LOG_PARAMS = {
    tier: {'mu': math.log(p['mu']), 'sigma': p['sigma']}
    for tier, p in REPAIR_PARAMS.items()
}


class MaintenanceBase:
    """
    Three-tier maintenance facility with SimPy resource pools.

    Parameters
    ----------
    env : simpy.Environment
        SimPy simulation environment.
    rng : numpy.random.RandomState
        Seeded random state for reproducibility.
    o_level_capacity : int
        Number of O-level technicians (day shift default).
    i_level_capacity : int
        Number of I-level technicians (day shift default).
    d_level_capacity : int
        Number of D-level depot technicians.

    Attributes
    ----------
    o_level : simpy.Resource
        O-level maintenance resource pool.
    i_level : simpy.Resource
        I-level maintenance resource pool.
    d_level : simpy.Resource
        D-level maintenance resource pool.
    maintenance_log : list of dict
        Complete log of all maintenance activities.
    queue_length_history : list of dict
        Time series of queue lengths for analysis.
    """

    def __init__(self, env, rng, o_level_capacity=8, i_level_capacity=4,
                 d_level_capacity=6):
        self.env = env
        self.rng = rng

        # SimPy Resource pools
        self.o_level = simpy.Resource(env, capacity=o_level_capacity)
        self.i_level = simpy.Resource(env, capacity=i_level_capacity)
        self.d_level = simpy.Resource(env, capacity=d_level_capacity)

        # Capacity tracking for dynamic shift changes
        self.o_level_day_capacity = o_level_capacity
        self.i_level_day_capacity = i_level_capacity
        self.d_level_capacity = d_level_capacity

        self.maintenance_log = []
        self.queue_length_history = []

    def _get_resource_for_tier(self, tier):
        """
        Return the SimPy Resource for the given maintenance tier.

        Parameters
        ----------
        tier : str
            'O', 'I', or 'D'.

        Returns
        -------
        simpy.Resource
            The corresponding resource pool.
        """
        if tier == 'O':
            return self.o_level
        elif tier == 'I':
            return self.i_level
        elif tier == 'D':
            return self.d_level
        else:
            raise ValueError(f"Unknown maintenance tier: {tier}")

    def _generate_repair_time(self, tier):
        """
        Generate a repair time from the tier-specific lognormal distribution.

        Parameters
        ----------
        tier : str
            'O', 'I', or 'D'.

        Returns
        -------
        float
            Repair time in hours.
        """
        params = REPAIR_LOG_PARAMS[tier]
        return lognormal_rvs(params['mu'], params['sigma'], self.rng)

    def repair_aircraft(self, env, aircraft, failed_subsystem, inventory):
        """
        SimPy generator process: repair a failed subsystem on an aircraft.

        This process:
        1. Determines the maintenance tier
        2. Waits in queue for available technician
        3. Checks parts availability (waits if stockout)
        4. Performs repair (timed by lognormal distribution)
        5. Resets subsystem and updates aircraft status

        Parameters
        ----------
        env : simpy.Environment
            SimPy simulation environment.
        aircraft : Aircraft
            The aircraft being repaired.
        failed_subsystem : Subsystem
            The failed subsystem to repair.
        inventory : PartsInventory
            Spare parts inventory to draw from.

        Yields
        ------
        simpy.events.Event
            Various SimPy events (resource requests, timeouts).
        """
        tier = failed_subsystem.maintenance_tier_required
        resource = self._get_resource_for_tier(tier)

        # Update aircraft status
        if tier == 'D':
            aircraft.status = 'NMC_depot'
        else:
            aircraft.status = 'NMC_maintenance'

        # --- Phase 1: Queue for technician ---
        queue_start = env.now
        req = resource.request()
        yield req
        queue_wait_hours = env.now - queue_start

        # --- Phase 2: Check parts availability ---
        parts_start = env.now
        part_available = inventory.request_part(failed_subsystem.name)

        while not part_available:
            aircraft.status = 'NMC_parts'
            # Wait and re-check every 4 hours
            yield env.timeout(4.0)
            part_available = inventory.request_part(failed_subsystem.name)

        parts_wait_hours = env.now - parts_start

        # --- Phase 3: Active repair ---
        if tier != 'D':
            aircraft.status = 'NMC_maintenance'
        else:
            aircraft.status = 'NMC_depot'

        repair_time = self._generate_repair_time(tier)
        repair_start = env.now
        yield env.timeout(repair_time)
        active_repair_hours = env.now - repair_start

        # --- Phase 4: Complete repair ---
        resource.release(req)
        failed_subsystem.reset_after_repair()
        aircraft.update_status()

        # Log the event
        event = {
            'aircraft_id': aircraft.aircraft_id,
            'subsystem': failed_subsystem.name,
            'tier': tier,
            'start_time': queue_start,
            'end_time': env.now,
            'queue_wait_hours': queue_wait_hours,
            'parts_wait_hours': parts_wait_hours,
            'active_repair_hours': active_repair_hours,
            'total_downtime_hours': env.now - queue_start,
        }
        aircraft.log_maintenance_event(event)
        self.maintenance_log.append(event)

    def record_queue_snapshot(self, time):
        """
        Record current queue lengths for analysis.

        Parameters
        ----------
        time : float
            Current simulation time in hours.
        """
        snapshot = {
            'time': time,
            'o_level_queue': len(self.o_level.queue),
            'i_level_queue': len(self.i_level.queue),
            'd_level_queue': len(self.d_level.queue),
            'o_level_in_use': self.o_level.count,
            'i_level_in_use': self.i_level.count,
            'd_level_in_use': self.d_level.count,
        }
        self.queue_length_history.append(snapshot)
