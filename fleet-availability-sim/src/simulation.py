"""
Fleet Simulation orchestration module.

Ties together all components: aircraft, subsystems, maintenance,
inventory, shift scheduling, and KPI tracking into a single
runnable discrete event simulation using SimPy.

Supports both peacetime and surge OPTEMPO scenarios.
"""

import simpy
import numpy as np
import pandas as pd
from tqdm import tqdm

from src.aircraft import Aircraft
from src.inventory import PartsInventory
from src.maintenance import MaintenanceBase
from src.scheduler import ShiftScheduler
from src.kpi_tracker import KPITracker
from src.distributions import poisson_interval

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
HOURS_PER_DAY = 24
WARM_UP_DAYS = 30                       # 30-day warm-up excluded from KPIs
DEFAULT_FLEET_SIZE = 12
DEFAULT_SIM_DAYS = 180
DEFAULT_SORTIE_INTERVAL_HOURS = 48      # Peacetime OPTEMPO
SURGE_SORTIE_INTERVAL_HOURS = 18        # Surge OPTEMPO
SORTIE_HOURS_MIN = 1.2                  # Uniform sortie duration bounds
SORTIE_HOURS_MAX = 2.8


class FleetSimulation:
    """
    Complete fleet availability simulation.

    Parameters
    ----------
    fleet_size : int
        Number of aircraft. Default 12.
    o_level_techs_day : int
        Day-shift O-level technicians. Default 8.
    i_level_techs_day : int
        Day-shift I-level technicians. Default 4.
    d_level_techs : int
        Depot technicians. Default 6.
    sortie_interval_hours : float
        Mean inter-sortie time in hours (peacetime). Default 48.
    inventory_params : dict, optional
        Override default inventory parameters.
    subsystem_params : dict, optional
        Override default Weibull parameters per subsystem.
        Format: {'engine': {'beta': X, 'eta': Y}, ...}
    """

    def __init__(self, fleet_size=DEFAULT_FLEET_SIZE,
                 o_level_techs_day=8, i_level_techs_day=4,
                 d_level_techs=6,
                 sortie_interval_hours=DEFAULT_SORTIE_INTERVAL_HOURS,
                 inventory_params=None,
                 subsystem_params=None):
        self.fleet_size = fleet_size
        self.o_level_techs_day = o_level_techs_day
        self.i_level_techs_day = i_level_techs_day
        self.d_level_techs = d_level_techs
        self.sortie_interval_hours = sortie_interval_hours
        self.inventory_params = inventory_params
        self.subsystem_params = subsystem_params

    def _apply_subsystem_overrides(self, aircraft, rng):
        """
        Apply custom Weibull parameters to aircraft subsystems.

        Parameters
        ----------
        aircraft : Aircraft
            Aircraft whose subsystems to override.
        rng : numpy.random.RandomState
            Random state for re-generating TTF.
        """
        if self.subsystem_params is None:
            return
        for name, params in self.subsystem_params.items():
            if name in aircraft.subsystems:
                sub = aircraft.subsystems[name]
                if 'beta' in params:
                    sub.beta = params['beta']
                if 'eta' in params:
                    sub.eta = params['eta']
                # Regenerate TTF with new params
                from src.distributions import weibull_rvs
                sub.time_to_next_failure = weibull_rvs(sub.beta, sub.eta, rng)

    def _aircraft_lifecycle(self, env, aircraft, maintenance, inventory, rng,
                            sortie_interval_hours, surge_start_hour,
                            surge_end_hour):
        """
        SimPy generator: lifecycle process for one aircraft.

        Generates sorties, accrues flight hours, triggers failures and
        maintenance. Adjusts OPTEMPO during surge periods.

        Parameters
        ----------
        env : simpy.Environment
            SimPy environment.
        aircraft : Aircraft
            The aircraft to manage.
        maintenance : MaintenanceBase
            Maintenance facility.
        inventory : PartsInventory
            Spare parts inventory.
        rng : numpy.random.RandomState
            Random state.
        sortie_interval_hours : float
            Peacetime mean inter-sortie time.
        surge_start_hour : float
            Simulation hour when surge begins (inf if no surge).
        surge_end_hour : float
            Simulation hour when surge ends.

        Yields
        ------
        simpy.events.Event
            Timeouts and process joins.
        """
        while True:
            # Wait for next sortie
            if surge_start_hour <= env.now < surge_end_hour:
                interval = poisson_interval(SURGE_SORTIE_INTERVAL_HOURS, rng)
            else:
                interval = poisson_interval(sortie_interval_hours, rng)

            yield env.timeout(interval)

            # Check if aircraft is available
            if not aircraft.is_available_for_sortie():
                continue

            # Fly sortie
            sortie_hours = rng.uniform(SORTIE_HOURS_MIN, SORTIE_HOURS_MAX)
            aircraft.status = 'sortie'

            yield env.timeout(sortie_hours)

            aircraft.total_flight_hours += sortie_hours
            aircraft.sorties_completed += 1

            # Accrue flight hours on all subsystems
            failed_list = []
            for sub in aircraft.subsystems.values():
                failure_occurred = sub.accrue_flight_hours(sortie_hours)
                if failure_occurred:
                    failed_list.append(sub)

            # Process failures
            if failed_list:
                aircraft.update_status()
                for failed_sub in failed_list:
                    env.process(
                        maintenance.repair_aircraft(
                            env, aircraft, failed_sub, inventory
                        )
                    )
            else:
                aircraft.update_status()

    def _kpi_recorder(self, env, fleet, kpi_tracker, inventory, maintenance):
        """
        SimPy generator: records KPI snapshots every simulated hour.

        Parameters
        ----------
        env : simpy.Environment
            SimPy environment.
        fleet : list of Aircraft
            All aircraft.
        kpi_tracker : KPITracker
            KPI tracker instance.
        inventory : PartsInventory
            For stock level recording.
        maintenance : MaintenanceBase
            For queue length recording.

        Yields
        ------
        simpy.events.Timeout
            1-hour intervals.
        """
        while True:
            kpi_tracker.record_snapshot(env, fleet)
            inventory.record_stock_snapshot(env.now)
            maintenance.record_queue_snapshot(env.now)
            yield env.timeout(1.0)

    def run(self, simulation_days=DEFAULT_SIM_DAYS,
            surge_start_day=None, surge_duration_hours=None,
            random_seed=42):
        """
        Run a complete fleet simulation.

        Parameters
        ----------
        simulation_days : int
            Total simulation duration in days.
        surge_start_day : int or None
            Day on which surge begins (None = no surge).
        surge_duration_hours : float or None
            Duration of surge in hours.
        random_seed : int
            Random seed for reproducibility.

        Returns
        -------
        dict
            Complete results including:
            - 'mcr': time-averaged MCR
            - 'fmcr': time-averaged FMCR
            - 'pam_fraction': time-averaged PAM fraction
            - 'maintenance_pipeline_fraction': mean pipeline fraction
            - 'total_sorties': total sorties across fleet
            - 'total_flight_hours': total flight hours
            - 'kpi_dataframe': full KPI time series
            - 'stock_history': inventory time series
            - 'queue_history': maintenance queue time series
            - 'maintenance_log': all maintenance events
        """
        rng = np.random.RandomState(random_seed)
        env = simpy.Environment()

        # Surge timing
        if surge_start_day is not None and surge_duration_hours is not None:
            surge_start_hour = surge_start_day * HOURS_PER_DAY
            surge_end_hour = surge_start_hour + surge_duration_hours
        else:
            surge_start_hour = float('inf')
            surge_end_hour = float('inf')

        # Create fleet
        fleet = [Aircraft(i, rng) for i in range(self.fleet_size)]

        # Apply subsystem parameter overrides
        for ac in fleet:
            self._apply_subsystem_overrides(ac, rng)

        # Create facilities
        inventory = PartsInventory(env, rng, self.inventory_params)
        maintenance = MaintenanceBase(
            env, rng,
            o_level_capacity=self.o_level_techs_day,
            i_level_capacity=self.i_level_techs_day,
            d_level_capacity=self.d_level_techs,
        )

        # Start shift scheduler
        scheduler = ShiftScheduler(env, maintenance)

        # KPI tracker with warm-up
        warm_up_hours = WARM_UP_DAYS * HOURS_PER_DAY
        kpi_tracker = KPITracker(self.fleet_size, warm_up_hours)

        # Start KPI recorder
        env.process(self._kpi_recorder(env, fleet, kpi_tracker,
                                        inventory, maintenance))

        # Start aircraft lifecycle processes
        for ac in fleet:
            env.process(self._aircraft_lifecycle(
                env, ac, maintenance, inventory, rng,
                self.sortie_interval_hours,
                surge_start_hour, surge_end_hour,
            ))

        # Run simulation
        sim_hours = simulation_days * HOURS_PER_DAY
        env.run(until=sim_hours)

        # Compile results
        total_sorties = sum(ac.sorties_completed for ac in fleet)
        total_hours = sum(ac.total_flight_hours for ac in fleet)

        results = {
            'mcr': kpi_tracker.compute_time_averaged_MCR(),
            'fmcr': kpi_tracker.compute_time_averaged_FMCR(),
            'pam_fraction': kpi_tracker.compute_PAM_fraction(),
            'maintenance_pipeline_fraction':
                kpi_tracker.compute_maintenance_pipeline_fraction(),
            'total_sorties': total_sorties,
            'total_flight_hours': total_hours,
            'kpi_dataframe': kpi_tracker.get_full_dataframe(),
            'kpi_tracker': kpi_tracker,
            'stock_history': inventory.stock_history,
            'queue_history': maintenance.queue_length_history,
            'maintenance_log': maintenance.maintenance_log,
            'fleet': fleet,
            'inventory': inventory,
        }

        return results


def run_monte_carlo(sim_config, n_replications=50, show_progress=True,
                    **run_kwargs):
    """
    Run multiple replications of the simulation for Monte Carlo analysis.

    Parameters
    ----------
    sim_config : dict
        FleetSimulation constructor arguments.
    n_replications : int
        Number of replications.
    show_progress : bool
        Show tqdm progress bar.
    **run_kwargs : dict
        Additional arguments to FleetSimulation.run() (e.g., surge params).

    Returns
    -------
    pandas.DataFrame
        One row per replication with columns: mcr, fmcr, pam_fraction,
        total_sorties, total_flight_hours, seed.
    """
    sim = FleetSimulation(**sim_config)
    results_list = []

    iterator = range(n_replications)
    if show_progress:
        iterator = tqdm(iterator, desc='Monte Carlo replications')

    for i in iterator:
        seed = run_kwargs.get('random_seed', 42) + i
        kwargs = dict(run_kwargs)
        kwargs['random_seed'] = seed
        result = sim.run(**kwargs)

        results_list.append({
            'replication': i,
            'seed': seed,
            'mcr': result['mcr'],
            'fmcr': result['fmcr'],
            'pam_fraction': result['pam_fraction'],
            'total_sorties': result['total_sorties'],
            'total_flight_hours': result['total_flight_hours'],
        })

    return pd.DataFrame(results_list)
