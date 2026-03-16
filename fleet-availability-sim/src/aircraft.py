"""
Aircraft module for the Fleet Availability Simulator.

Models a single combat aircraft composed of four independent subsystems
(engine, avionics, hydraulics, airframe). Tracks aircraft status,
flight hours, sorties, and maintenance event history.
"""

from src.subsystem import Subsystem, SUBSYSTEM_PARAMS


class Aircraft:
    """
    Represents one combat aircraft in the fleet.

    Parameters
    ----------
    aircraft_id : int
        Unique identifier for this aircraft.
    rng : numpy.random.RandomState
        Seeded random state for reproducibility.

    Attributes
    ----------
    subsystems : dict
        Dictionary mapping subsystem name to Subsystem instance.
    status : str
        Current aircraft status. One of:
        'FMC'  — Fully Mission Capable (all subsystems healthy)
        'PMC'  — Partially Mission Capable (degraded but flyable)
        'NMC_maintenance' — Not Mission Capable, in maintenance
        'NMC_parts' — Not Mission Capable, awaiting parts (PAM)
        'NMC_depot' — Not Mission Capable, in depot-level maintenance
        'sortie' — Currently flying a sortie
    total_flight_hours : float
        Cumulative flight hours across all sorties.
    sorties_completed : int
        Total number of sorties completed.
    maintenance_events : list of dict
        Log of all maintenance events with timing details.
    """

    def __init__(self, aircraft_id, rng):
        self.aircraft_id = aircraft_id
        self.rng = rng

        # Create four independent subsystems
        self.subsystems = {}
        for name, params in SUBSYSTEM_PARAMS.items():
            self.subsystems[name] = Subsystem(
                name=name,
                beta=params['beta'],
                eta=params['eta'],
                rng=rng,
            )

        self.status = 'FMC'
        self.total_flight_hours = 0.0
        self.sorties_completed = 0
        self.maintenance_events = []

    def update_status(self):
        """
        Update aircraft status based on current subsystem states.

        Returns
        -------
        str
            Updated status string.

        Notes
        -----
        Status is determined hierarchically:
        - If any subsystem is failed → NMC (specific type set externally
          during maintenance/parts flow)
        - If all subsystems FMC → aircraft is FMC
        - If any subsystem PMC but none NMC → aircraft is PMC
        """
        statuses = [s.get_health_status() for s in self.subsystems.values()]

        if 'NMC' in statuses:
            # Keep the specific NMC sub-status if already set
            if self.status not in ('NMC_maintenance', 'NMC_parts', 'NMC_depot'):
                self.status = 'NMC_maintenance'
        elif 'PMC' in statuses:
            self.status = 'PMC'
        else:
            self.status = 'FMC'

        return self.status

    def get_failed_subsystems(self):
        """
        Return list of currently failed subsystems.

        Returns
        -------
        list of Subsystem
            All subsystems in failed state.
        """
        return [s for s in self.subsystems.values() if s.is_failed]

    def get_availability_contribution(self):
        """
        Return this aircraft's contribution to fleet availability metrics.

        Returns
        -------
        dict
            Keys: 'is_fmc' (bool), 'is_mission_capable' (bool),
            'is_pam' (bool), 'status' (str).

        Notes
        -----
        Mission Capable = FMC or PMC.
        FMC = all subsystems fully healthy.
        PAM = awaiting parts specifically.
        """
        return {
            'is_fmc': self.status == 'FMC',
            'is_mission_capable': self.status in ('FMC', 'PMC'),
            'is_pam': self.status == 'NMC_parts',
            'status': self.status,
        }

    def log_maintenance_event(self, event_dict):
        """
        Record a maintenance event.

        Parameters
        ----------
        event_dict : dict
            Must contain keys: 'subsystem', 'tier', 'start_time',
            'end_time', 'queue_wait_hours', 'parts_wait_hours',
            'active_repair_hours', 'aircraft_id'.
        """
        event_dict['aircraft_id'] = self.aircraft_id
        self.maintenance_events.append(event_dict)

    def is_available_for_sortie(self):
        """
        Check if aircraft can fly a sortie.

        Returns
        -------
        bool
            True if status is FMC or PMC.
        """
        return self.status in ('FMC', 'PMC')
