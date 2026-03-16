"""
C-MAPSS Data Loader — NASA Turbofan Engine Degradation Dataset.

Parses FD001–FD004 datasets, computes Health Index from sensor data,
and fits Weibull degradation parameters for the fleet simulation.
"""

import os
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import gamma as gamma_func

# Path to C-MAPSS data relative to project root
_DATA_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', 'pdf', 'CMAPSSData',
)

# Column names for the C-MAPSS dataset
_COLS = (
    ['unit', 'cycle']
    + [f'op{i}' for i in range(1, 4)]
    + [f's{i}' for i in range(1, 22)]
)

# Sensors that show meaningful degradation trends in C-MAPSS
# (identified through correlation analysis in literature)
DEGRADING_SENSORS = ['s2', 's3', 's4', 's7', 's8', 's9',
                     's11', 's12', 's13', 's14', 's15',
                     's17', 's20', 's21']

# Mapping: C-MAPSS sensor groups → fleet simulation subsystems
SENSOR_SUBSYSTEM_MAP = {
    'engine':     ['s2', 's3', 's4', 's7', 's11', 's12'],
    'avionics':   ['s8', 's13'],
    'hydraulics': ['s9', 's14', 's15'],
    'airframe':   ['s17', 's20', 's21'],
}


def load_dataset(dataset='FD001'):
    """
    Load a C-MAPSS dataset.

    Parameters
    ----------
    dataset : str
        Dataset ID: 'FD001', 'FD002', 'FD003', or 'FD004'.

    Returns
    -------
    train_df : pd.DataFrame
        Training data (run-to-failure).
    test_df : pd.DataFrame
        Test data (cut-off before failure).
    rul : np.ndarray
        True RUL values for test data.
    """
    train_path = os.path.join(_DATA_DIR, f'train_{dataset}.txt')
    test_path = os.path.join(_DATA_DIR, f'test_{dataset}.txt')
    rul_path = os.path.join(_DATA_DIR, f'RUL_{dataset}.txt')

    train_df = pd.read_csv(train_path, sep=r'\s+', header=None, names=_COLS)
    test_df = pd.read_csv(test_path, sep=r'\s+', header=None, names=_COLS)
    rul = pd.read_csv(rul_path, sep=r'\s+', header=None).values.flatten()

    return train_df, test_df, rul


def compute_health_index(df, sensors=None):
    """
    Compute a normalized Health Index (HI) per unit per cycle.

    Uses min-max normalization of degrading sensors, then averages
    to produce a 1→0 health trajectory.

    Parameters
    ----------
    df : pd.DataFrame
        Training data with run-to-failure trajectories.
    sensors : list or None
        Sensor columns to use. Defaults to DEGRADING_SENSORS.

    Returns
    -------
    pd.DataFrame
        Original df with added 'health_index' column (1.0 = healthy, 0.0 = failed).
    """
    if sensors is None:
        sensors = DEGRADING_SENSORS

    result = df.copy()
    available = [s for s in sensors if s in result.columns]

    # Normalize each sensor per unit (min-max)
    normalized = pd.DataFrame(index=result.index)
    for s in available:
        grp = result.groupby('unit')[s]
        s_min = grp.transform('min')
        s_max = grp.transform('max')
        rng = s_max - s_min
        rng = rng.replace(0, 1)  # avoid div-by-zero
        normalized[s] = (result[s] - s_min) / rng

    # Average normalized sensors → raw degradation signal (0→1)
    deg_signal = normalized[available].mean(axis=1)

    # Invert: health = 1 - degradation
    result['health_index'] = 1.0 - deg_signal

    return result


def get_failure_times(df):
    """
    Extract time-to-failure (max cycle) for each engine unit.

    Parameters
    ----------
    df : pd.DataFrame
        Training data (run-to-failure).

    Returns
    -------
    np.ndarray
        Array of failure times (in cycles) for each unit.
    """
    return df.groupby('unit')['cycle'].max().values.astype(float)


def _weibull_nll(params, data):
    """Negative log-likelihood for Weibull distribution."""
    beta, eta = params
    if beta <= 0 or eta <= 0:
        return 1e12
    n = len(data)
    ll = (n * np.log(beta / eta)
          + (beta - 1) * np.sum(np.log(data / eta))
          - np.sum((data / eta) ** beta))
    return -ll


def fit_weibull(failure_times):
    """
    Fit Weibull parameters (beta, eta) via MLE.

    Parameters
    ----------
    failure_times : array-like
        Observed time-to-failure values.

    Returns
    -------
    dict
        {'beta': float, 'eta': float, 'mean_ttf': float}
    """
    data = np.array(failure_times, dtype=float)
    data = data[data > 0]

    # Initial guess
    mean_t = np.mean(data)
    beta0, eta0 = 2.0, mean_t

    res = minimize(_weibull_nll, [beta0, eta0], args=(data,),
                   method='Nelder-Mead',
                   options={'maxiter': 5000, 'xatol': 1e-6})

    beta, eta = abs(res.x[0]), abs(res.x[1])
    mean_ttf = eta * gamma_func(1.0 + 1.0 / beta)

    return {'beta': round(beta, 3), 'eta': round(eta, 1),
            'mean_ttf': round(mean_ttf, 1)}


import functools

@functools.lru_cache(maxsize=4)
def fit_subsystem_params(dataset='FD001'):
    """
    Fit Weibull parameters for each subsystem using C-MAPSS sensor groups.

    Maps sensor degradation rates to subsystem failure times by computing
    per-subsystem health indices and finding when each drops below threshold.

    Parameters
    ----------
    dataset : str
        Dataset ID.

    Returns
    -------
    dict
        Subsystem name → {'beta': float, 'eta': float, 'mean_ttf': float}
    """
    train_df, _, _ = load_dataset(dataset)
    overall_ttf = get_failure_times(train_df)

    # Fit overall engine failure distribution
    overall_fit = fit_weibull(overall_ttf)

    # Scale subsystem parameters relative to overall failure pattern
    # Engine subsystem fails at ~1x the overall rate
    # Avionics fails earlier (electronics), hydraulics later (mechanical)
    subsystem_scales = {
        'engine':     1.0,
        'avionics':   0.75,
        'hydraulics': 1.5,
        'airframe':   2.5,
    }

    params = {}
    for subsys, scale in subsystem_scales.items():
        sensors = SENSOR_SUBSYSTEM_MAP.get(subsys, [])
        available = [s for s in sensors if s in train_df.columns]

        if available:
            # Compute subsystem-specific health and fit
            hi_df = compute_health_index(train_df, available)
            # Find per-unit cycle where subsystem health drops below 0.3
            sub_ttf = []
            for uid in hi_df['unit'].unique():
                unit_data = hi_df[hi_df['unit'] == uid]
                failed = unit_data[unit_data['health_index'] <= 0.3]
                if len(failed) > 0:
                    sub_ttf.append(float(failed['cycle'].iloc[0]))
                else:
                    sub_ttf.append(float(unit_data['cycle'].max()))

            sub_fit = fit_weibull(np.array(sub_ttf))
            # Scale eta by the subsystem scale factor
            sub_fit['eta'] = round(sub_fit['eta'] * scale, 1)
            sub_fit['mean_ttf'] = round(
                sub_fit['eta'] * gamma_func(1.0 + 1.0 / sub_fit['beta']), 1)
            params[subsys] = sub_fit
        else:
            # Fallback: scale from overall
            params[subsys] = {
                'beta': overall_fit['beta'],
                'eta': round(overall_fit['eta'] * scale, 1),
                'mean_ttf': round(
                    overall_fit['eta'] * scale
                    * gamma_func(1.0 + 1.0 / overall_fit['beta']), 1),
            }

    return params


def get_degradation_profiles(dataset='FD001', n_units=5):
    """
    Get health index trajectories for sample engine units.

    Parameters
    ----------
    dataset : str
        Dataset ID.
    n_units : int
        Number of sample units to return.

    Returns
    -------
    dict
        unit_id → pd.DataFrame with 'cycle' and 'health_index' columns.
    """
    train_df, _, _ = load_dataset(dataset)
    hi_df = compute_health_index(train_df)

    units = sorted(hi_df['unit'].unique())[:n_units]
    profiles = {}
    for uid in units:
        unit_data = hi_df[hi_df['unit'] == uid][['cycle', 'health_index']].copy()
        profiles[int(uid)] = unit_data.reset_index(drop=True)

    return profiles


def get_sensor_data(dataset='FD001', unit_id=1):
    """
    Get raw sensor readings for a specific engine unit.

    Parameters
    ----------
    dataset : str
        Dataset ID.
    unit_id : int
        Engine unit number.

    Returns
    -------
    pd.DataFrame
        Sensor readings over cycles for the specified unit.
    """
    train_df, _, _ = load_dataset(dataset)
    unit_data = train_df[train_df['unit'] == unit_id].copy()
    return unit_data.reset_index(drop=True)


def get_summary_stats(dataset='FD001'):
    """
    Get summary statistics for the dataset.

    Returns
    -------
    dict
        Summary with n_units, sensor_count, cycle_stats, fitted_params.
    """
    train_df, test_df, rul = load_dataset(dataset)
    ttf = get_failure_times(train_df)
    params = fit_subsystem_params(dataset)

    return {
        'dataset': dataset,
        'n_train_units': train_df['unit'].nunique(),
        'n_test_units': test_df['unit'].nunique(),
        'n_sensors': 21,
        'cycle_stats': {
            'min': int(ttf.min()),
            'max': int(ttf.max()),
            'mean': round(float(ttf.mean()), 1),
            'std': round(float(ttf.std()), 1),
        },
        'fitted_params': params,
    }
