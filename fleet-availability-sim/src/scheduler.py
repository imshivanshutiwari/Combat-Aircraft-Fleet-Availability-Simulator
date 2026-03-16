"""
Shift Scheduler module for the Fleet Availability Simulator.

Models realistic military maintenance staffing schedules:
- Day shift (0600-1800): Full staffing
- Night shift (1800-0600): Reduced staffing
- Weekend: O/I-level at 50%, D-level closed
- D-level depot: Monday-Friday 0800-1700 only

Implemented as a SimPy process that fires at shift boundaries and
dynamically adjusts resource capacities.
"""

import simpy

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
HOURS_PER_DAY = 24
DAY_SHIFT_START = 6      # 0600
DAY_SHIFT_END = 18       # 1800
DEPOT_START = 8           # 0800
DEPOT_END = 17            # 1700

# Staffing multipliers
NIGHT_SHIFT_O_MULTIPLIER = 0.5    # 50% of day shift O-level
NIGHT_SHIFT_I_MULTIPLIER = 0.5    # 50% of day shift I-level
WEEKEND_MULTIPLIER = 0.5          # 50% staffing on weekends


class ShiftScheduler:
    """
    Manages shift-based resource capacity changes.

    Parameters
    ----------
    env : simpy.Environment
        SimPy simulation environment.
    maintenance_base : MaintenanceBase
        The maintenance facility whose capacities to adjust.

    Notes
    -----
    This runs as a continuous SimPy process, checking every hour
    and adjusting resource capacities at shift boundaries.
    The simulation starts on a Monday at 0000.
    """

    def __init__(self, env, maintenance_base):
        self.env = env
        self.maint = maintenance_base
        self.current_shift = None
        self.action = env.process(self.run())

    def _get_day_of_week(self):
        """
        Get current day of week (0=Monday, 6=Sunday).

        Returns
        -------
        int
            Day of week.
        """
        return int((self.env.now / HOURS_PER_DAY) % 7)

    def _get_hour_of_day(self):
        """
        Get current hour of day (0-23).

        Returns
        -------
        float
            Hour of day.
        """
        return self.env.now % HOURS_PER_DAY

    def _is_weekend(self):
        """
        Check if current time is a weekend (Saturday or Sunday).

        Returns
        -------
        bool
            True if Saturday (5) or Sunday (6).
        """
        dow = self._get_day_of_week()
        return dow >= 5

    def _is_day_shift(self):
        """
        Check if current time is within day shift hours.

        Returns
        -------
        bool
            True if between 0600 and 1800.
        """
        hour = self._get_hour_of_day()
        return DAY_SHIFT_START <= hour < DAY_SHIFT_END

    def _is_depot_hours(self):
        """
        Check if current time is within depot operating hours.

        Returns
        -------
        bool
            True if weekday between 0800 and 1700.
        """
        if self._is_weekend():
            return False
        hour = self._get_hour_of_day()
        return DEPOT_START <= hour < DEPOT_END

    def _update_capacities(self):
        """
        Update resource capacities based on current shift and day.

        Notes
        -----
        SimPy Resource capacity is adjusted by replacing the resource's
        internal _capacity attribute. This is a pragmatic approach since
        SimPy doesn't natively support dynamic capacity changes.
        """
        is_weekend = self._is_weekend()
        is_day = self._is_day_shift()
        is_depot = self._is_depot_hours()

        # O-level capacity
        base_o = self.maint.o_level_day_capacity
        if is_weekend:
            o_cap = max(1, int(base_o * WEEKEND_MULTIPLIER))
        elif is_day:
            o_cap = base_o
        else:
            o_cap = max(1, int(base_o * NIGHT_SHIFT_O_MULTIPLIER))
        self.maint.o_level._capacity = o_cap

        # I-level capacity
        base_i = self.maint.i_level_day_capacity
        if is_weekend:
            i_cap = max(1, int(base_i * WEEKEND_MULTIPLIER))
        elif is_day:
            i_cap = base_i
        else:
            i_cap = max(1, int(base_i * NIGHT_SHIFT_I_MULTIPLIER))
        self.maint.i_level._capacity = i_cap

        # D-level capacity — only during depot hours on weekdays
        if is_depot:
            d_cap = self.maint.d_level_capacity
        else:
            d_cap = 0
        # D-level: set to at least 0 (no technicians outside hours)
        # But if anyone is currently being served, don't drop below count
        d_cap = max(d_cap, self.maint.d_level.count)
        self.maint.d_level._capacity = max(1, d_cap) if d_cap > 0 else 1

    def run(self):
        """
        SimPy generator process — runs continuously, updating capacities.

        Yields
        ------
        simpy.events.Timeout
            1-hour intervals between capacity checks.
        """
        while True:
            self._update_capacities()
            yield self.env.timeout(1.0)  # Check every hour
