"""
Maintenance module for the Fleet Live Simulation engine.

Models three-tier maintenance with SimPy resources and spare parts.
"""

import simpy
from engine.distributions import lognormal_rvs, normal_rvs

HOURS_PER_DAY = 24

# Lognormal repair time parameters (mu, sigma in log-space)
REPAIR_LOG_PARAMS = {
    'O': {'mu': 4.0,   'sigma': 1.2},
    'I': {'mu': 24.0,  'sigma': 1.8},
    'D': {'mu': 480.0, 'sigma': 2.1},
}

# Inventory parameters
INVENTORY_PARAMS = {
    'engine':     {'reorder_point': 2, 'order_qty': 3,
                   'lead_mean': 14, 'lead_std': 3, 'init_stock': 5},
    'avionics':   {'reorder_point': 3, 'order_qty': 5,
                   'lead_mean': 7,  'lead_std': 2, 'init_stock': 8},
    'hydraulics': {'reorder_point': 4, 'order_qty': 6,
                   'lead_mean': 5,  'lead_std': 1, 'init_stock': 10},
    'airframe':   {'reorder_point': 1, 'order_qty': 2,
                   'lead_mean': 30, 'lead_std': 7, 'init_stock': 3},
}


class PartsInventory:
    """Spare parts inventory with (r, Q) continuous review policy."""

    def __init__(self, env, rng):
        self.env = env
        self.rng = rng
        self.stock = {k: v['init_stock'] for k, v in INVENTORY_PARAMS.items()}
        self.reorder_pending = {k: False for k in INVENTORY_PARAMS}

    def request_part(self, subsystem_name):
        """Request a part. Returns True if available, False if stockout."""
        if self.stock[subsystem_name] > 0:
            self.stock[subsystem_name] -= 1
            r = INVENTORY_PARAMS[subsystem_name]['reorder_point']
            if self.stock[subsystem_name] <= r and not self.reorder_pending[subsystem_name]:
                self.env.process(self._reorder(subsystem_name))
            return True
        else:
            if not self.reorder_pending[subsystem_name]:
                self.env.process(self._reorder(subsystem_name))
            return False

    def _reorder(self, subsystem_name):
        """SimPy process: reorder parts with stochastic lead time."""
        self.reorder_pending[subsystem_name] = True
        p = INVENTORY_PARAMS[subsystem_name]
        lead_days = max(1.0, normal_rvs(p['lead_mean'], p['lead_std'], self.rng))
        yield self.env.timeout(lead_days * HOURS_PER_DAY)
        self.stock[subsystem_name] += p['order_qty']
        self.reorder_pending[subsystem_name] = False


class MaintenanceBase:
    """Three-tier maintenance facility with SimPy resources."""

    def __init__(self, env, rng, o_capacity=8, i_capacity=4, d_capacity=6):
        self.env = env
        self.rng = rng
        self.o_level = simpy.Resource(env, capacity=o_capacity)
        self.i_level = simpy.Resource(env, capacity=i_capacity)
        self.d_level = simpy.Resource(env, capacity=d_capacity)
        self.o_level_day_capacity = o_capacity
        self.i_level_day_capacity = i_capacity
        self.d_level_capacity = d_capacity
        self.maintenance_log = []

    def repair_aircraft(self, env, aircraft, failed_sub, inventory):
        """
        SimPy generator: full repair pipeline.

        1. Queue for technician
        2. Check/wait for parts
        3. Active repair
        4. Release and reset
        """
        tier = failed_sub.maintenance_tier_required
        resource = {'O': self.o_level, 'I': self.i_level, 'D': self.d_level}[tier]

        if tier == 'D':
            aircraft.status = 'NMC_depot'
        else:
            aircraft.status = 'NMC_maintenance'

        # Phase 1: queue
        queue_start = env.now
        req = resource.request()
        yield req
        queue_wait = env.now - queue_start

        # Phase 2: parts
        parts_start = env.now
        while not inventory.request_part(failed_sub.name):
            aircraft.status = 'NMC_parts'
            yield env.timeout(4.0)
        parts_wait = env.now - parts_start

        if tier != 'D':
            aircraft.status = 'NMC_maintenance'
        else:
            aircraft.status = 'NMC_depot'

        # Phase 3: repair
        params = REPAIR_LOG_PARAMS[tier]
        repair_time = lognormal_rvs(params['mu'], params['sigma'], self.rng)
        repair_start = env.now
        yield env.timeout(repair_time)

        # Phase 4: complete
        resource.release(req)
        failed_sub.reset_after_repair()
        aircraft.update_status()

        event = {
            'aircraft_id': aircraft.aircraft_id,
            'subsystem': failed_sub.name,
            'tier': tier,
            'start_time': queue_start,
            'end_time': env.now,
            'queue_wait_hours': queue_wait,
            'parts_wait_hours': parts_wait,
            'active_repair_hours': env.now - repair_start,
        }
        aircraft.log_maintenance_event(event)
        self.maintenance_log.append(event)


class ShiftScheduler:
    """Manages shift-based resource capacity changes."""

    def __init__(self, env, maint):
        self.env = env
        self.maint = maint
        self.action = env.process(self.run())

    def run(self):
        """SimPy process: update capacities every hour."""
        while True:
            hour = self.env.now % HOURS_PER_DAY
            dow = int((self.env.now / HOURS_PER_DAY) % 7)
            is_weekend = dow >= 5
            is_day = 6 <= hour < 18

            # O-level
            base_o = self.maint.o_level_day_capacity
            if is_weekend:
                o_cap = max(1, base_o // 2)
            elif is_day:
                o_cap = base_o
            else:
                o_cap = max(1, base_o // 2)
            self.maint.o_level._capacity = o_cap

            # I-level
            base_i = self.maint.i_level_day_capacity
            if is_weekend:
                i_cap = max(1, base_i // 2)
            elif is_day:
                i_cap = base_i
            else:
                i_cap = max(1, base_i // 2)
            self.maint.i_level._capacity = i_cap

            # D-level — weekday 0800-1700 only
            if not is_weekend and 8 <= hour < 17:
                d_cap = self.maint.d_level_capacity
            else:
                d_cap = max(1, self.maint.d_level.count)
            self.maint.d_level._capacity = max(1, d_cap)

            yield self.env.timeout(1.0)
