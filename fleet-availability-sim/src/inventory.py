"""
Spare Parts Inventory module for the Fleet Availability Simulator.

Implements (r, Q) continuous review inventory policy for four subsystem
part classes. When stock drops to reorder point r, order quantity Q
with stochastic lead time. Stockouts cause PAM (Parts Awaiting Maintenance).
"""

import simpy
import numpy as np
from src.distributions import normal_rvs

# ---------------------------------------------------------------------------
# Constants — Inventory parameters per subsystem
# ---------------------------------------------------------------------------
HOURS_PER_DAY = 24

INVENTORY_PARAMS = {
    'engine': {
        'reorder_point': 2,
        'order_quantity': 3,
        'lead_time_mean_days': 14,
        'lead_time_std_days': 3,
        'initial_stock': 5,
    },
    'avionics': {
        'reorder_point': 3,
        'order_quantity': 5,
        'lead_time_mean_days': 7,
        'lead_time_std_days': 2,
        'initial_stock': 8,
    },
    'hydraulics': {
        'reorder_point': 4,
        'order_quantity': 6,
        'lead_time_mean_days': 5,
        'lead_time_std_days': 1,
        'initial_stock': 10,
    },
    'airframe': {
        'reorder_point': 1,
        'order_quantity': 2,
        'lead_time_mean_days': 30,
        'lead_time_std_days': 7,
        'initial_stock': 3,
    },
}

# Cost parameters (all in rupees)
HOLDING_COST_PER_PART_PER_DAY = 100       # Rupees
STOCKOUT_COST_PER_AIRCRAFT_PER_PAM_DAY = 50000  # Rupees
LABOUR_COST_PER_TECHNICIAN_PER_SHIFT = 2000     # Rupees


class PartsInventory:
    """
    Spare parts inventory with (r, Q) continuous review policy.

    Parameters
    ----------
    env : simpy.Environment
        SimPy simulation environment.
    rng : numpy.random.RandomState
        Seeded random state for reproducibility.
    params_override : dict, optional
        Override default inventory parameters. Keys are subsystem names,
        values are dicts with 'reorder_point', 'order_quantity', etc.

    Attributes
    ----------
    stock : dict
        Current stock level for each subsystem part class.
    reorder_pending : dict
        Whether a reorder is in progress for each subsystem.
    total_orders : dict
        Total number of reorders placed per subsystem.
    stockout_events : list
        Log of all stockout events.
    stock_history : list of dict
        Time series of stock levels for analysis.
    """

    def __init__(self, env, rng, params_override=None):
        self.env = env
        self.rng = rng

        # Merge default params with any overrides
        self.params = {}
        for name, defaults in INVENTORY_PARAMS.items():
            self.params[name] = dict(defaults)
            if params_override and name in params_override:
                self.params[name].update(params_override[name])

        # Initialise stock levels
        self.stock = {
            name: p['initial_stock'] for name, p in self.params.items()
        }
        self.reorder_pending = {name: False for name in self.params}
        self.total_orders = {name: 0 for name in self.params}
        self.stockout_events = []
        self.stock_history = []

    def request_part(self, subsystem_name):
        """
        Request a spare part for a subsystem repair.

        Parameters
        ----------
        subsystem_name : str
            Name of the subsystem ('engine', 'avionics', etc.).

        Returns
        -------
        bool
            True if part is available (stock > 0), False if stockout.

        Notes
        -----
        Decrements stock and triggers reorder if stock <= reorder point.
        """
        if self.stock[subsystem_name] > 0:
            self.stock[subsystem_name] -= 1
            # Check reorder point
            r = self.params[subsystem_name]['reorder_point']
            if (self.stock[subsystem_name] <= r
                    and not self.reorder_pending[subsystem_name]):
                self.env.process(self.trigger_reorder(subsystem_name))
            return True
        else:
            self.stockout_events.append({
                'time': self.env.now,
                'subsystem': subsystem_name,
            })
            # Trigger reorder if not already pending
            if not self.reorder_pending[subsystem_name]:
                self.env.process(self.trigger_reorder(subsystem_name))
            return False

    def trigger_reorder(self, subsystem_name):
        """
        SimPy generator process for reordering parts.

        Parameters
        ----------
        subsystem_name : str
            Name of the subsystem part class to reorder.

        Yields
        ------
        simpy.events.Timeout
            Lead time delay before parts arrive.

        Notes
        -----
        Lead time drawn from Normal distribution with subsystem-specific
        parameters. Negative lead times are clipped to 1 day minimum.
        """
        self.reorder_pending[subsystem_name] = True
        self.total_orders[subsystem_name] += 1

        p = self.params[subsystem_name]
        lead_time_days = normal_rvs(
            p['lead_time_mean_days'],
            p['lead_time_std_days'],
            self.rng,
        )
        lead_time_hours = max(HOURS_PER_DAY, lead_time_days * HOURS_PER_DAY)

        yield self.env.timeout(lead_time_hours)

        # Parts arrive
        self.stock[subsystem_name] += p['order_quantity']
        self.reorder_pending[subsystem_name] = False

    def get_stock_status(self):
        """
        Return current stock levels and pending orders.

        Returns
        -------
        dict
            Keys: subsystem names. Values: dict with 'stock', 'reorder_pending'.
        """
        return {
            name: {
                'stock': self.stock[name],
                'reorder_pending': self.reorder_pending[name],
            }
            for name in self.params
        }

    def record_stock_snapshot(self, time):
        """
        Record a snapshot of stock levels for time-series analysis.

        Parameters
        ----------
        time : float
            Current simulation time in hours.
        """
        snapshot = {'time': time}
        for name in self.params:
            snapshot[f'{name}_stock'] = self.stock[name]
        self.stock_history.append(snapshot)

    def compute_holding_cost(self, duration_days):
        """
        Compute total holding cost over a given duration.

        Parameters
        ----------
        duration_days : float
            Duration in days.

        Returns
        -------
        float
            Total holding cost in rupees.
        """
        total_parts = sum(self.stock.values())
        return total_parts * HOLDING_COST_PER_PART_PER_DAY * duration_days
