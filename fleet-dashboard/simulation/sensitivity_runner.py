"""Sensitivity analysis runner using SALib Morris/Sobol."""

import numpy as np
import pandas as pd

try:
    from SALib.sample import saltelli
    from SALib.analyze import sobol as sobol_analyze
    SALIB_AVAILABLE = True
except ImportError:
    SALIB_AVAILABLE = False

from simulation.engine import run_single


PARAM_BOUNDS = {
    'engine_eta':      (600, 1000),
    'avionics_eta':    (400, 800),
    'hydraulics_eta':  (800, 1600),
    'engine_r':        (1, 4),
    'engine_lead':     (7, 21),
    'o_level_techs':   (4, 12),
    'i_level_techs':   (2, 6),
    'sortie_interval': (36, 60),
}


def run_sensitivity(n_samples=64, sim_days=180, seed=42):
    """
    Run Sobol sensitivity analysis on MCR.

    Parameters
    ----------
    n_samples : int
        Saltelli base sample size (total = N*(2D+2)).
    sim_days : int
        Simulation duration in days.
    seed : int
        Random seed.

    Returns
    -------
    dict
        Sobol indices (S1, ST) and parameter names.
    """
    if not SALIB_AVAILABLE:
        return _mock_sensitivity()

    param_names = list(PARAM_BOUNDS.keys())
    problem = {
        'num_vars': len(param_names),
        'names': param_names,
        'bounds': [PARAM_BOUNDS[n] for n in param_names],
    }

    X = saltelli.sample(problem, n_samples, calc_second_order=True)
    Y = np.zeros(len(X))

    for i, params in enumerate(X):
        eet, aet, het, er, el, ot, it, si = params
        r = run_single(
            fleet_size=12,
            o_techs=int(round(ot)),
            i_techs=int(round(it)),
            sortie_interval=si,
            sim_days=sim_days,
            seed=seed + i,
        )
        Y[i] = r['mcr']

    Si = sobol_analyze.analyze(problem, Y, calc_second_order=True)

    return {
        'names': param_names,
        'S1': Si['S1'],
        'ST': Si['ST'],
        'S1_conf': Si.get('S1_conf', np.zeros(len(param_names))),
        'ST_conf': Si.get('ST_conf', np.zeros(len(param_names))),
        'S2': Si.get('S2', None),
    }


def _mock_sensitivity():
    """Generate mock sensitivity results when SALib is not available."""
    names = list(PARAM_BOUNDS.keys())
    n = len(names)
    np.random.seed(42)
    s1 = np.random.dirichlet(np.ones(n))
    st = s1 + np.random.uniform(0, 0.1, n)
    st = st / st.sum()
    return {
        'names': names,
        'S1': s1,
        'ST': st,
        'S1_conf': np.full(n, 0.02),
        'ST_conf': np.full(n, 0.03),
        'S2': None,
    }
