"""
Simulation engine for the Military Streamlit Dashboard.

Complete SimPy-based fleet simulation with cached execution.
"""

import simpy
import numpy as np
import pandas as pd
from simulation.distributions import (
    weibull_rvs, lognormal_rvs, normal_rvs, poisson_interval,
)

HOURS_PER_DAY = 24
WARM_UP_DAYS = 30
SORTIE_HOURS_MIN = 1.2
SORTIE_HOURS_MAX = 2.8
SURGE_INTERVAL = 18.0

# Subsystem Weibull parameters
SUBSYSTEM_PARAMS = {
    'engine':     {'beta': 2.1, 'eta': 800},
    'avionics':   {'beta': 1.4, 'eta': 600},
    'hydraulics': {'beta': 1.8, 'eta': 1200},
    'airframe':   {'beta': 3.0, 'eta': 2000},
}

REPAIR_PARAMS = {
    'O': {'mu': 4.0,   'sigma': 1.2},
    'I': {'mu': 24.0,  'sigma': 1.8},
    'D': {'mu': 480.0, 'sigma': 2.1},
}

INVENTORY_PARAMS = {
    'engine':     {'r': 2, 'Q': 3, 'lead_mean': 14, 'lead_std': 3, 'init': 5},
    'avionics':   {'r': 3, 'Q': 5, 'lead_mean': 7,  'lead_std': 2, 'init': 8},
    'hydraulics': {'r': 4, 'Q': 6, 'lead_mean': 5,  'lead_std': 1, 'init': 10},
    'airframe':   {'r': 1, 'Q': 2, 'lead_mean': 30, 'lead_std': 7, 'init': 3},
}


class Subsystem:
    def __init__(self, name, beta, eta, rng, use_ai_predictions=False, model_type='Elite (LSTM)'):
        self.name, self.beta, self.eta, self.rng = name, beta, eta, rng
        self.use_ai = use_ai_predictions
        self.model_type = model_type.split(' ')[0] # Extract 'Elite' or 'Standard' or 'SOTA'
        self.health = 1.0
        self.hours = 0.0
        self.ttf = weibull_rvs(beta, eta, rng)
        self.failed = False
        self.tier = None
        
        # Level 5: Deep Learning Sensor History Buffer
        from data.ml_model import SEQUENCE_LENGTH, FEATURES_COUNT
        self.sensor_history = []
        self.seq_len = SEQUENCE_LENGTH

    def accrue(self, h):
        self.hours += h
        self.health = max(0.0, 1.0 - self.hours / self.ttf)
        
        if getattr(self, 'use_ai', False):
            from data.ml_model import predict_rul
            # Generate simulated sensor noise based on hidden health 
            deg_signal = 1.0 - self.health
            current_sensors = np.clip(self.rng.normal(deg_signal, 0.05, 14), 0, 1)
            
            # Maintain sliding window for LSTM
            self.sensor_history.append(current_sensors)
            if len(self.sensor_history) > self.seq_len:
                self.sensor_history.pop(0)
            
            # Predict RUL; only if we have enough history for the LSTM/Transformer
            if len(self.sensor_history) == self.seq_len:
                m_type = 'LSTM' if 'Elite' in self.model_type else ('Transformer' if 'SOTA' in self.model_type else 'Standard')
                pred_rul = predict_rul(self.sensor_history, model_type=m_type)[0]
                if pred_rul <= 0:
                    self.failed = True
                    self.tier = 'D' if self.health < 0.4 else ('I' if self.health < 0.7 else 'O')
                    return True
            else:
                # Fallback to statistical TTF until buffer is full
                if self.hours >= self.ttf:
                    self.failed = True
                    self.tier = 'D' if self.health < 0.4 else ('I' if self.health < 0.7 else 'O')
                    return True
        else:
            if self.hours >= self.ttf:
                self.failed = True
                self.tier = 'D' if self.health < 0.4 else ('I' if self.health < 0.7 else 'O')
                return True
        return False

    def reset(self):
        self.health, self.hours = 1.0, 0.0
        self.ttf = weibull_rvs(self.beta, self.eta, self.rng)
        self.failed, self.tier = False, None


class Aircraft:
    def __init__(self, aid, rng, sys_params=None, use_ai_predictions=False, **kwargs):
        self.id, self.rng = aid, rng
        params = sys_params if sys_params else SUBSYSTEM_PARAMS
        self.subs = {n: Subsystem(n, p['beta'], p['eta'], rng, use_ai_predictions, kwargs.get('model_type', 'Elite'))
                     for n, p in params.items()}
        self.status = 'FMC'
        self.hours, self.sorties = 0.0, 0
        self.events = []

    def update_status(self):
        states = [s.health for s in self.subs.values()]
        any_failed = any(s.failed for s in self.subs.values())
        if any_failed:
            if self.status not in ('NMC_maintenance', 'NMC_parts', 'NMC_depot'):
                self.status = 'NMC_maintenance'
        elif min(states) < 0.7:
            self.status = 'PMC'
        else:
            self.status = 'FMC'


class Inventory:
    def __init__(self, env, rng):
        self.env, self.rng = env, rng
        self.stock = {n: p['init'] for n, p in INVENTORY_PARAMS.items()}
        self.pending = {n: False for n in INVENTORY_PARAMS}
        self.history = []

    def request(self, name):
        if self.stock[name] > 0:
            self.stock[name] -= 1
            if self.stock[name] <= INVENTORY_PARAMS[name]['r'] and not self.pending[name]:
                self.env.process(self._reorder(name))
            return True
        if not self.pending[name]:
            self.env.process(self._reorder(name))
        return False

    def _reorder(self, name):
        self.pending[name] = True
        p = INVENTORY_PARAMS[name]
        lead = max(1.0, normal_rvs(p['lead_mean'], p['lead_std'], self.rng))
        
        # Supply Chain Shock: 5% chance of severe delay
        if self.rng.random() < 0.05:
            lead *= self.rng.uniform(2.0, 4.0)
            
        yield self.env.timeout(lead * HOURS_PER_DAY)
        self.stock[name] += p['Q']
        self.pending[name] = False

    def snapshot(self, t):
        self.history.append({'time': t, **{n: self.stock[n] for n in INVENTORY_PARAMS}})


class Maintenance:
    def __init__(self, env, rng, o_cap=8, i_cap=4, d_cap=6, surge_start=None, surge_end=None):
        self.env, self.rng = env, rng
        self.o = simpy.Resource(env, o_cap)
        self.i = simpy.Resource(env, i_cap)
        self.d = simpy.Resource(env, d_cap)
        self.surge_start = surge_start
        self.surge_end = surge_end
        self.log = []
        self.queue_hist = []
        self.fleet = [] # Injected later

    def repair(self, env, ac, sub, inv):
        tier = sub.tier
        res = {'O': self.o, 'I': self.i, 'D': self.d}[tier]
        ac.status = 'NMC_depot' if tier == 'D' else 'NMC_maintenance'
        t0 = env.now
        req = res.request()
        yield req
        while not inv.request(sub.name):
            ac.status = 'NMC_parts'
            
            # Cannibalization logic: Look for Depot aircraft with good part
            cannibalized = False
            if self.fleet:
                for donor in self.fleet:
                    if donor.status == 'NMC_depot' and donor.id != ac.id:
                        donor_sub = donor.subs[sub.name]
                        if not donor_sub.failed and donor_sub.health > 0.6:
                            # Strip part from donor
                            donor_sub.failed = True
                            donor_sub.health = 0.0
                            donor_sub.tier = 'I'
                            cannibalized = True
                            # Start repair process to replace donor's now-broken part
                            env.process(self.repair(env, donor, donor_sub, inv))
                            break
                            
            if cannibalized:
                # 8 hours to swap part mechanically
                yield env.timeout(8.0)
                break
                
            yield env.timeout(4.0)
            
        ac.status = 'NMC_depot' if tier == 'D' else 'NMC_maintenance'
        p = REPAIR_PARAMS[tier]
        base_time = lognormal_rvs(p['mu'], p['sigma'], self.rng)
        
        # Fatigue Modeling
        fatigue = 1.0
        if self.surge_start is not None and self.surge_end is not None:
            if self.surge_start <= env.now < self.surge_end:
                hrs_in_surge = env.now - self.surge_start
                if hrs_in_surge > 48.0:
                    fatigue = min(1.5, 1.0 + (hrs_in_surge - 48.0) / 144.0)
                    
        yield env.timeout(base_time * fatigue)
        res.release(req)
        sub.reset()
        ac.update_status()
        self.log.append({
            'ac': ac.id, 'sub': sub.name, 'tier': tier,
            'start': t0, 'end': env.now, 'down': env.now - t0,
        })

    def queue_snapshot(self, t):
        self.queue_hist.append({
            'time': t,
            'o_queue': len(self.o.queue), 'i_queue': len(self.i.queue),
            'd_queue': len(self.d.queue),
        })


def run_single(fleet_size=12, o_techs=8, i_techs=4, d_techs=6,
               sortie_interval=48.0, sim_days=180,
               surge_start=None, surge_dur=None, seed=42,
               use_real_data=False, use_ai_predictions=False, model_type='Elite (LSTM)'):
    """
    Run one complete simulation.

    Returns
    -------
    dict
        Complete results with KPIs, time series, and fleet state.
    """
    rng = np.random.RandomState(seed)
    env = simpy.Environment()
    
    sys_params = None
    if use_real_data or use_ai_predictions:
        from data.cmapss_loader import fit_subsystem_params
        sys_params = fit_subsystem_params('FD001')
        
    fleet = [Aircraft(i, rng, sys_params=sys_params, use_ai_predictions=use_ai_predictions, model_type=model_type) 
             for i in range(fleet_size)]
    inv = Inventory(env, rng)
    surge_start_h = (surge_start * HOURS_PER_DAY) if surge_start else float('inf')
    surge_end_h = (surge_start_h + surge_dur) if surge_dur else float('inf')

    maint = Maintenance(env, rng, o_techs, i_techs, d_techs, 
                        surge_start_h if surge_start else None, 
                        surge_end_h if surge_dur else None)
    maint.fleet = fleet

    # KPI recording
    kpi_records = []
    warm_up_h = WARM_UP_DAYS * HOURS_PER_DAY

    def kpi_recorder():
        while True:
            n = len(fleet)
            fmc = sum(1 for a in fleet if a.status == 'FMC')
            mc = sum(1 for a in fleet if a.status in ('FMC', 'PMC'))
            pam = sum(1 for a in fleet if a.status == 'NMC_parts')
            depot = sum(1 for a in fleet if a.status == 'NMC_depot')
            nmcm = sum(1 for a in fleet if a.status == 'NMC_maintenance')
            kpi_records.append({
                'time': env.now,
                'mcr': mc / n if n else 0,
                'fmcr': fmc / n if n else 0,
                'pam_fraction': pam / n if n else 0,
                'fmc': fmc, 'pmc': mc - fmc,
                'nmc_m': nmcm, 'nmc_p': pam, 'nmc_d': depot,
            })
            inv.snapshot(env.now)
            maint.queue_snapshot(env.now)
            yield env.timeout(1.0)

    def lifecycle(ac):
        while True:
            intv = poisson_interval(
                SURGE_INTERVAL if surge_start_h <= env.now < surge_end_h else sortie_interval,
                rng)
            yield env.timeout(intv)
            if ac.status not in ('FMC', 'PMC'):
                continue
            ac.status = 'sortie'
            hrs = rng.uniform(SORTIE_HOURS_MIN, SORTIE_HOURS_MAX)
            yield env.timeout(hrs)
            ac.hours += hrs
            ac.sorties += 1
            failed = [s for s in ac.subs.values() if s.accrue(hrs)]
            ac.update_status()
            for s in failed:
                env.process(maint.repair(env, ac, s, inv))

    # Shift scheduler
    def shifts():
        while True:
            h = env.now % HOURS_PER_DAY
            dow = int((env.now / HOURS_PER_DAY) % 7)
            is_wknd = dow >= 5
            is_day = 6 <= h < 18
            maint.o._capacity = max(1, o_techs // 2) if (not is_day or is_wknd) else o_techs
            maint.i._capacity = max(1, i_techs // 2) if (not is_day or is_wknd) else i_techs
            maint.d._capacity = max(1, d_techs if (not is_wknd and 8 <= h < 17) else 1)
            yield env.timeout(1.0)

    env.process(kpi_recorder())
    env.process(shifts())
    for ac in fleet:
        env.process(lifecycle(ac))

    env.run(until=sim_days * HOURS_PER_DAY)

    df = pd.DataFrame(kpi_records)
    post_warmup = df[df['time'] >= warm_up_h]

    return {
        'mcr': post_warmup['mcr'].mean() if len(post_warmup) else 0,
        'fmcr': post_warmup['fmcr'].mean() if len(post_warmup) else 0,
        'pam': post_warmup['pam_fraction'].mean() if len(post_warmup) else 0,
        'total_sorties': sum(a.sorties for a in fleet),
        'total_hours': sum(a.hours for a in fleet),
        'kpi_df': df,
        'stock_df': pd.DataFrame(inv.history),
        'queue_df': pd.DataFrame(maint.queue_hist),
        'maint_log': maint.log,
        'fleet': fleet,
        'fleet_size': fleet_size,
    }


def run_monte_carlo(n_reps=50, show_progress_fn=None, **sim_kwargs):
    """
    Run Monte Carlo replications.

    Returns
    -------
    pd.DataFrame
        One row per replication.
    list
        List of full result dicts.
    """
    results = []
    all_results = []
    base_seed = sim_kwargs.pop('seed', 42)
    for i in range(n_reps):
        if show_progress_fn:
            show_progress_fn(i, n_reps)
        r = run_single(seed=base_seed + i, **sim_kwargs)
        results.append({
            'rep': i, 'seed': base_seed + i,
            'mcr': r['mcr'], 'fmcr': r['fmcr'], 'pam': r['pam'],
            'sorties': r['total_sorties'], 'hours': r['total_hours'],
        })
        all_results.append(r)
    return pd.DataFrame(results), all_results
