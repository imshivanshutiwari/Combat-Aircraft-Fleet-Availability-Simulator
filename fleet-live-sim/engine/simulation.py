"""
SimPy simulation engine thread for the Fleet Live Simulation.

Runs the discrete event simulation in a background thread and writes
state updates to the SharedState object every simulated hour.
"""

import time
import numpy as np
import simpy

from engine.aircraft import Aircraft
from engine.maintenance import MaintenanceBase, PartsInventory, ShiftScheduler
from engine.distributions import poisson_interval
from assets.colors import (
    EVENT_FAILURE, EVENT_REPAIR, EVENT_PARTS,
    EVENT_SHIFT, EVENT_SORTIE, EVENT_GENERAL,
)

HOURS_PER_DAY = 24
SORTIE_HOURS_MIN = 1.2
SORTIE_HOURS_MAX = 2.8
PEACETIME_INTERVAL = 48.0
SURGE_INTERVAL = 18.0


def run_simulation_thread(shared_state, fleet_size=12, random_seed=42):
    """
    Main simulation thread function.

    Parameters
    ----------
    shared_state : SharedState
        Thread-safe shared state object.
    fleet_size : int
        Number of aircraft.
    random_seed : int
        Seed for reproducibility.
    """
    while shared_state.running:
        # Check for reset
        shared_state.reset_requested = False
        _run_one_session(shared_state, fleet_size, random_seed)
        if not shared_state.reset_requested:
            # Simulation ended naturally (unlikely since it loops)
            break


def _run_one_session(shared_state, fleet_size, random_seed):
    """Run one complete simulation session until reset or exit."""
    rng = np.random.RandomState(random_seed)
    env = simpy.Environment()

    # Create fleet
    fleet = [Aircraft(i, rng) for i in range(fleet_size)]

    # Create facilities
    inventory = PartsInventory(env, rng)
    maintenance = MaintenanceBase(env, rng)
    scheduler = ShiftScheduler(env, maintenance)

    # Track sorties for tempo
    sortie_counter = {'count': 0, 'last_day': 0}

    # Log initial event
    shared_state.add_event(
        shared_state.format_sim_time(0),
        "Simulation initialized — all systems nominal",
        EVENT_GENERAL,
    )

    # Start aircraft lifecycle processes
    for ac in fleet:
        env.process(_aircraft_lifecycle(
            env, ac, maintenance, inventory, rng,
            shared_state, sortie_counter,
        ))

    # Start hourly state updater
    env.process(_hourly_updater(
        env, fleet, maintenance, inventory,
        shared_state, sortie_counter,
    ))

    # Start shift change announcer
    env.process(_shift_announcer(env, shared_state))

    # Run simulation step-by-step with real-time pacing
    while shared_state.running and not shared_state.reset_requested:
        if shared_state.paused:
            time.sleep(0.05)
            continue

        # Advance simulation by 1 hour
        target = env.now + 1.0
        try:
            env.run(until=target)
        except simpy.core.EmptySchedule:
            pass

        # Real-time pacing: 1 sim hour = 1 real second / speed_multiplier * 60
        # At 60x speed: 1 sim hour = 1 second
        sleep_time = 1.0 / shared_state.speed_multiplier
        time.sleep(sleep_time)


def _aircraft_lifecycle(env, aircraft, maintenance, inventory, rng,
                        shared_state, sortie_counter):
    """SimPy generator: lifecycle for one aircraft."""
    while True:
        # Wait for next sortie
        if shared_state.surge_active:
            interval = poisson_interval(SURGE_INTERVAL, rng)
        else:
            interval = poisson_interval(PEACETIME_INTERVAL, rng)

        yield env.timeout(interval)

        if not aircraft.is_available_for_sortie():
            continue

        # --- Sortie ---
        aircraft.status = 'sortie'
        _update_ac_state(shared_state, aircraft, env.now)

        shared_state.add_event(
            shared_state.format_sim_time(env.now),
            f"AC-{aircraft.aircraft_id:02d} cleared for sortie",
            EVENT_SORTIE,
        )

        # Update display position: move to runway
        _set_ac_target(shared_state, aircraft.aircraft_id,
                       shared_state.RUNWAY_X + shared_state.RUNWAY_WIDTH,
                       shared_state.RUNWAY_Y + 10)
        _set_ac_field(shared_state, aircraft.aircraft_id,
                      sortie_phase='taxi_out', on_sortie=True,
                      afterburner_active=False)

        # Taxi out time
        yield env.timeout(0.1)

        # Takeoff
        _set_ac_field(shared_state, aircraft.aircraft_id,
                      sortie_phase='takeoff', afterburner_active=True)
        _set_ac_target(shared_state, aircraft.aircraft_id, -50, shared_state.RUNWAY_Y + 10)

        yield env.timeout(0.05)

        # Airborne (disappear off screen)
        _set_ac_field(shared_state, aircraft.aircraft_id,
                      sortie_phase='airborne', afterburner_active=False)
        _set_ac_target(shared_state, aircraft.aircraft_id, -100, shared_state.RUNWAY_Y + 10)

        sortie_hours = rng.uniform(SORTIE_HOURS_MIN, SORTIE_HOURS_MAX)
        yield env.timeout(sortie_hours)

        # Landing — reappear from right
        _set_ac_field(shared_state, aircraft.aircraft_id,
                      sortie_phase='landing', afterburner_active=False)
        with shared_state.lock:
            ac_state = shared_state.aircraft_states[aircraft.aircraft_id]
            ac_state['x'] = 1450.0
            ac_state['y'] = float(shared_state.RUNWAY_Y + 10)
        _set_ac_target(shared_state, aircraft.aircraft_id,
                       shared_state.RUNWAY_X + shared_state.RUNWAY_WIDTH,
                       shared_state.RUNWAY_Y + 10)

        yield env.timeout(0.1)

        # Taxi back to parking
        home_x, home_y = shared_state.PARKING_POSITIONS[aircraft.aircraft_id]
        _set_ac_field(shared_state, aircraft.aircraft_id,
                      sortie_phase='taxi_in', afterburner_active=False)
        _set_ac_target(shared_state, aircraft.aircraft_id, home_x, home_y)

        yield env.timeout(0.1)

        _set_ac_field(shared_state, aircraft.aircraft_id,
                      sortie_phase=None, on_sortie=False)

        # Accrue flight hours
        aircraft.total_flight_hours += sortie_hours
        aircraft.sorties_completed += 1
        sortie_counter['count'] += 1

        # Check for failures
        failed_list = []
        for sub in aircraft.subsystems.values():
            if sub.accrue_flight_hours(sortie_hours):
                failed_list.append(sub)

        if failed_list:
            aircraft.update_status()
            _update_ac_state(shared_state, aircraft, env.now)

            for failed_sub in failed_list:
                shared_state.add_event(
                    shared_state.format_sim_time(env.now),
                    f"AC-{aircraft.aircraft_id:02d} {failed_sub.name} failure detected",
                    EVENT_FAILURE,
                )
                # Move aircraft to maintenance bay
                tier = failed_sub.maintenance_tier_required
                bay_key = {'O': 'o_level', 'I': 'i_level', 'D': 'depot'}[tier]
                bay_pos = shared_state.BAY_POSITIONS[bay_key]
                _set_ac_target(shared_state, aircraft.aircraft_id,
                               bay_pos[0] + 30, bay_pos[1] + 30)

                env.process(
                    _repair_with_events(env, aircraft, failed_sub,
                                        maintenance, inventory, shared_state)
                )
        else:
            aircraft.update_status()
            _update_ac_state(shared_state, aircraft, env.now)
            # Return to parking
            home_x, home_y = shared_state.PARKING_POSITIONS[aircraft.aircraft_id]
            _set_ac_target(shared_state, aircraft.aircraft_id, home_x, home_y)


def _repair_with_events(env, aircraft, failed_sub, maintenance, inventory, shared_state):
    """Wrapper around repair that emits events and updates shared state."""
    tier = failed_sub.maintenance_tier_required
    resource = {'O': maintenance.o_level, 'I': maintenance.i_level,
                'D': maintenance.d_level}[tier]

    bay_key = {'O': 'o_level', 'I': 'i_level', 'D': 'depot'}[tier]

    # Update bay occupancy
    with shared_state.lock:
        shared_state.bay_states[bay_key]['occupancy'] += 1
        shared_state.bay_states[bay_key]['active_repairs'].append(aircraft.aircraft_id)

    if tier == 'D':
        aircraft.status = 'NMC_depot'
    else:
        aircraft.status = 'NMC_maintenance'
    _update_ac_state(shared_state, aircraft, env.now)

    # Queue
    req = resource.request()
    yield req

    # Check parts
    while not inventory.request_part(failed_sub.name):
        aircraft.status = 'NMC_parts'
        _update_ac_state(shared_state, aircraft, env.now)
        shared_state.add_event(
            shared_state.format_sim_time(env.now),
            f"AC-{aircraft.aircraft_id:02d} awaiting {failed_sub.name} parts",
            EVENT_PARTS,
        )
        # Update inventory display
        _update_inventory_display(shared_state, inventory)
        yield env.timeout(4.0)

    if tier != 'D':
        aircraft.status = 'NMC_maintenance'
    else:
        aircraft.status = 'NMC_depot'
    _update_ac_state(shared_state, aircraft, env.now)

    # Repair
    from engine.maintenance import REPAIR_LOG_PARAMS
    from engine.distributions import lognormal_rvs
    params = REPAIR_LOG_PARAMS[tier]
    repair_time = lognormal_rvs(params['mu'], params['sigma'], maintenance.rng)
    yield env.timeout(repair_time)

    # Complete
    resource.release(req)
    failed_sub.reset_after_repair()
    aircraft.update_status()

    # Return to parking
    home_x, home_y = shared_state.PARKING_POSITIONS[aircraft.aircraft_id]
    _set_ac_target(shared_state, aircraft.aircraft_id, home_x, home_y)
    _update_ac_state(shared_state, aircraft, env.now)

    # Update bay
    with shared_state.lock:
        shared_state.bay_states[bay_key]['occupancy'] = max(
            0, shared_state.bay_states[bay_key]['occupancy'] - 1)
        if aircraft.aircraft_id in shared_state.bay_states[bay_key]['active_repairs']:
            shared_state.bay_states[bay_key]['active_repairs'].remove(aircraft.aircraft_id)

    shared_state.add_event(
        shared_state.format_sim_time(env.now),
        f"AC-{aircraft.aircraft_id:02d} {failed_sub.name} repair complete ({tier}-level)",
        EVENT_REPAIR,
    )

    # Log
    aircraft.log_maintenance_event({
        'subsystem': failed_sub.name, 'tier': tier,
        'start_time': env.now - repair_time, 'end_time': env.now,
    })

    _update_inventory_display(shared_state, inventory)


def _hourly_updater(env, fleet, maintenance, inventory, shared_state, sortie_counter):
    """SimPy process: update KPIs and state every simulated hour."""
    while True:
        # Update sim time
        shared_state.sim_time = env.now

        # Compute KPIs
        fmc = sum(1 for ac in fleet if ac.status == 'FMC')
        mc = sum(1 for ac in fleet if ac.status in ('FMC', 'PMC'))
        pam = sum(1 for ac in fleet if ac.status == 'NMC_parts')
        n = len(fleet)

        current_mcr = mc / n if n > 0 else 0
        current_fmcr = fmc / n if n > 0 else 0

        # Tempo: sorties in last 24 hours
        current_day = int(env.now / HOURS_PER_DAY)
        if current_day > sortie_counter['last_day']:
            shared_state.update_kpi(current_tempo=sortie_counter['count'])
            # Add to MCR history (daily)
            with shared_state.lock:
                history = shared_state.kpi.get('mcr_history', [])
                history.append(current_mcr)
                if len(history) > 30:
                    history = history[-30:]
                shared_state.kpi['mcr_history'] = history
            sortie_counter['count'] = 0
            sortie_counter['last_day'] = current_day

        shared_state.update_kpi(
            current_mcr=current_mcr,
            current_fmcr=current_fmcr,
        )

        # Update all aircraft health displays
        for ac in fleet:
            shared_state.update_aircraft(ac.aircraft_id,
                health_engine=ac.subsystems['engine'].current_health,
                health_avionics=ac.subsystems['avionics'].current_health,
                health_hydraulics=ac.subsystems['hydraulics'].current_health,
                health_airframe=ac.subsystems['airframe'].current_health,
            )

        # Update inventory display
        _update_inventory_display(shared_state, inventory)

        # Update bay technician counts
        hour = env.now % HOURS_PER_DAY
        dow = int((env.now / HOURS_PER_DAY) % 7)
        is_weekend = dow >= 5
        is_day = 6 <= hour < 18

        o_techs = maintenance.o_level._capacity
        i_techs = maintenance.i_level._capacity
        d_techs = maintenance.d_level._capacity if (not is_weekend and 8 <= hour < 17) else 0

        shared_state.update_bay('o_level', technician_count=o_techs)
        shared_state.update_bay('i_level', technician_count=i_techs)
        shared_state.update_bay('depot', technician_count=d_techs)

        yield env.timeout(1.0)


def _shift_announcer(env, shared_state):
    """SimPy process: announce shift changes at 0600 and 1800."""
    while True:
        hour = env.now % HOURS_PER_DAY
        if abs(hour - 6.0) < 0.5:
            shared_state.add_event(
                shared_state.format_sim_time(env.now),
                "Shift change: day crew on duty",
                EVENT_SHIFT,
            )
        elif abs(hour - 18.0) < 0.5:
            shared_state.add_event(
                shared_state.format_sim_time(env.now),
                "Shift change: night crew on duty",
                EVENT_SHIFT,
            )
        yield env.timeout(1.0)


# ---------------------------------------------------------------------------
# Helper functions for updating shared state
# ---------------------------------------------------------------------------
def _update_ac_state(shared_state, aircraft, sim_time):
    """Push aircraft status to shared state."""
    shared_state.update_aircraft(aircraft.aircraft_id,
        status=aircraft.status,
    )


def _set_ac_target(shared_state, ac_id, x, y):
    """Set target position for smooth movement animation."""
    shared_state.update_aircraft(ac_id, target_x=float(x), target_y=float(y))


def _set_ac_field(shared_state, ac_id, **kwargs):
    """Set arbitrary fields on an aircraft state."""
    shared_state.update_aircraft(ac_id, **kwargs)


def _update_inventory_display(shared_state, inventory):
    """Push inventory levels to shared state."""
    from engine.maintenance import INVENTORY_PARAMS
    for name in INVENTORY_PARAMS:
        shared_state.update_inventory(name,
            stock=inventory.stock[name],
            reorder_pending=inventory.reorder_pending[name],
        )
