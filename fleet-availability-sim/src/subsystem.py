"""
Subsystem module for the Fleet Availability Simulator.

Models individual aircraft subsystems (engine, avionics, hydraulics, airframe)
with Weibull failure processes and health-based maintenance triage.

Each subsystem independently tracks flight hours and generates failures
according to its own Weibull distribution parameters.
"""

import numpy as np
from src.distributions import weibull_rvs


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
HEALTH_THRESHOLD_DEPOT = 0.40      # Below this → D-level maintenance
HEALTH_THRESHOLD_INTERMEDIATE = 0.70  # Below this → I-level maintenance
# Above 0.70 → O-level maintenance

# Subsystem Weibull parameters (beta=shape, eta=scale in flight hours)
SUBSYSTEM_PARAMS = {
    'engine':     {'beta': 2.1, 'eta': 800},
    'avionics':   {'beta': 1.4, 'eta': 600},
    'hydraulics': {'beta': 1.8, 'eta': 1200},
    'airframe':   {'beta': 3.0, 'eta': 2000},
}


class Subsystem:
    """
    Represents one aircraft subsystem with Weibull failure behaviour.

    Parameters
    ----------
    name : str
        Subsystem name ('engine', 'avionics', 'hydraulics', 'airframe').
    beta : float
        Weibull shape parameter.
    eta : float
        Weibull scale parameter in flight hours.
    rng : numpy.random.RandomState
        Seeded random state for reproducibility.

    Attributes
    ----------
    current_health : float
        Health fraction in [0, 1]. Starts at 1.0 (perfect).
    flight_hours_accumulated : float
        Total flight hours accrued since last repair/reset.
    time_to_next_failure : float
        Remaining flight hours until next failure (Weibull variate).
    is_failed : bool
        Whether subsystem is currently in failed state.
    maintenance_tier_required : str or None
        'O', 'I', or 'D' based on health at failure; None if not failed.
    """

    def __init__(self, name, beta, eta, rng):
        self.name = name
        self.beta = beta
        self.eta = eta
        self.rng = rng

        self.current_health = 1.0
        self.flight_hours_accumulated = 0.0
        self.time_to_next_failure = weibull_rvs(beta, eta, rng)
        self.is_failed = False
        self.maintenance_tier_required = None

    def accrue_flight_hours(self, hours):
        """
        Accrue flight hours and check for failure.

        Parameters
        ----------
        hours : float
            Flight hours to add.

        Returns
        -------
        bool
            True if a failure occurred during this accrual.

        Notes
        -----
        Health degrades linearly as a fraction of hours used vs. TTF.
        When accumulated hours exceed time_to_next_failure, the subsystem
        fails and the required maintenance tier is determined by health level.
        """
        self.flight_hours_accumulated += hours
        # Health degrades as proportion of life used
        life_fraction = self.flight_hours_accumulated / self.time_to_next_failure
        self.current_health = max(0.0, 1.0 - life_fraction)

        if self.flight_hours_accumulated >= self.time_to_next_failure:
            self.is_failed = True
            self._determine_maintenance_tier()
            return True
        return False

    def _determine_maintenance_tier(self):
        """
        Determine required maintenance tier based on health at failure.

        Notes
        -----
        Triage rule from spec:
        - Health < 40%  → D-level (depot overhaul)
        - Health 40-70% → I-level (intermediate)
        - Health > 70%  → O-level (organisational)
        """
        if self.current_health < HEALTH_THRESHOLD_DEPOT:
            self.maintenance_tier_required = 'D'
        elif self.current_health < HEALTH_THRESHOLD_INTERMEDIATE:
            self.maintenance_tier_required = 'I'
        else:
            self.maintenance_tier_required = 'O'

    def reset_after_repair(self):
        """
        Reset subsystem state after successful repair.

        Restores health to 1.0, resets flight hours, generates new TTF,
        and clears failure flags.
        """
        self.current_health = 1.0
        self.flight_hours_accumulated = 0.0
        self.time_to_next_failure = weibull_rvs(self.beta, self.eta, self.rng)
        self.is_failed = False
        self.maintenance_tier_required = None

    def get_health_status(self):
        """
        Return health status category.

        Returns
        -------
        str
            'FMC' (Fully Mission Capable) if health >= 0.70 and not failed,
            'PMC' (Partially Mission Capable) if health >= 0.40 and not failed,
            'NMC' (Not Mission Capable) if health < 0.40 or failed.
        """
        if self.is_failed:
            return 'NMC'
        if self.current_health >= HEALTH_THRESHOLD_INTERMEDIATE:
            return 'FMC'
        if self.current_health >= HEALTH_THRESHOLD_DEPOT:
            return 'PMC'
        return 'NMC'
