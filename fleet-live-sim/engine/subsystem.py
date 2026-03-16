"""
Subsystem module for the Fleet Live Simulation engine.

Models aircraft subsystems with Weibull failure behaviour.
"""

from engine.distributions import weibull_rvs

# Weibull parameters per subsystem (beta=shape, eta=scale in flight hours)
SUBSYSTEM_PARAMS = {
    'engine':     {'beta': 2.1, 'eta': 800},
    'avionics':   {'beta': 1.4, 'eta': 600},
    'hydraulics': {'beta': 1.8, 'eta': 1200},
    'airframe':   {'beta': 3.0, 'eta': 2000},
}

HEALTH_THRESHOLD_DEPOT = 0.40
HEALTH_THRESHOLD_INTERMEDIATE = 0.70


class Subsystem:
    """
    One aircraft subsystem with Weibull failure clock.

    Parameters
    ----------
    name : str
        Subsystem name.
    beta : float
        Weibull shape parameter.
    eta : float
        Weibull scale parameter (flight hours).
    rng : numpy.random.RandomState
        Random state for variate generation.
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

        Returns
        -------
        bool
            True if failure occurred.
        """
        self.flight_hours_accumulated += hours
        life_fraction = self.flight_hours_accumulated / self.time_to_next_failure
        self.current_health = max(0.0, 1.0 - life_fraction)

        if self.flight_hours_accumulated >= self.time_to_next_failure:
            self.is_failed = True
            if self.current_health < HEALTH_THRESHOLD_DEPOT:
                self.maintenance_tier_required = 'D'
            elif self.current_health < HEALTH_THRESHOLD_INTERMEDIATE:
                self.maintenance_tier_required = 'I'
            else:
                self.maintenance_tier_required = 'O'
            return True
        return False

    def reset_after_repair(self):
        """Reset subsystem state after successful repair."""
        self.current_health = 1.0
        self.flight_hours_accumulated = 0.0
        self.time_to_next_failure = weibull_rvs(self.beta, self.eta, self.rng)
        self.is_failed = False
        self.maintenance_tier_required = None

    def get_health_status(self):
        """Return 'FMC', 'PMC', or 'NMC'."""
        if self.is_failed:
            return 'NMC'
        if self.current_health >= HEALTH_THRESHOLD_INTERMEDIATE:
            return 'FMC'
        if self.current_health >= HEALTH_THRESHOLD_DEPOT:
            return 'PMC'
        return 'NMC'
