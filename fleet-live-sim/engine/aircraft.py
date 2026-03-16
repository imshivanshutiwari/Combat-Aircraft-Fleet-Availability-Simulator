"""
Aircraft module for the Fleet Live Simulation engine.

Models a single combat aircraft with four subsystems.
"""

from engine.subsystem import Subsystem, SUBSYSTEM_PARAMS


class Aircraft:
    """
    One combat aircraft in the fleet.

    Parameters
    ----------
    aircraft_id : int
        Unique identifier.
    rng : numpy.random.RandomState
        Seeded random state.
    """

    def __init__(self, aircraft_id, rng):
        self.aircraft_id = aircraft_id
        self.rng = rng
        self.subsystems = {}
        for name, params in SUBSYSTEM_PARAMS.items():
            self.subsystems[name] = Subsystem(
                name=name, beta=params['beta'],
                eta=params['eta'], rng=rng,
            )
        self.status = 'FMC'
        self.total_flight_hours = 0.0
        self.sorties_completed = 0
        self.maintenance_events = []

    def update_status(self):
        """Update aircraft status based on subsystem states."""
        statuses = [s.get_health_status() for s in self.subsystems.values()]
        if 'NMC' in statuses:
            if self.status not in ('NMC_maintenance', 'NMC_parts', 'NMC_depot'):
                self.status = 'NMC_maintenance'
        elif 'PMC' in statuses:
            self.status = 'PMC'
        else:
            self.status = 'FMC'
        return self.status

    def get_failed_subsystems(self):
        """Return list of failed subsystems."""
        return [s for s in self.subsystems.values() if s.is_failed]

    def is_available_for_sortie(self):
        """Check if aircraft can fly."""
        return self.status in ('FMC', 'PMC')

    def log_maintenance_event(self, event_dict):
        """Record a maintenance event."""
        event_dict['aircraft_id'] = self.aircraft_id
        self.maintenance_events.append(event_dict)
