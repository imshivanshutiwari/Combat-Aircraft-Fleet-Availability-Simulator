"""KPI calculator and statistics module."""

import numpy as np
import pandas as pd
from scipy import stats


def compute_confidence_interval(data, confidence=0.95):
    """
    Compute confidence interval for a dataset.

    Returns
    -------
    tuple
        (mean, ci_lower, ci_upper, ci_half_width)
    """
    n = len(data)
    mean = np.mean(data)
    if n < 2:
        return mean, mean, mean, 0.0
    se = stats.sem(data)
    h = se * stats.t.ppf((1 + confidence) / 2, n - 1)
    return mean, mean - h, mean + h, h


def compute_summary_stats(mc_df):
    """
    Compute summary statistics from Monte Carlo results.

    Parameters
    ----------
    mc_df : pd.DataFrame
        Monte Carlo results with 'mcr', 'fmcr', 'pam' columns.

    Returns
    -------
    pd.DataFrame
        Summary table with Mean, Std, 5th/95th percentiles, CIs.
    """
    metrics = {
        'MCR': mc_df['mcr'],
        'FMCR': mc_df['fmcr'],
        'PAM Fraction': mc_df['pam'],
        'Total Sorties': mc_df['sorties'],
        'Total Flight Hours': mc_df['hours'],
    }

    rows = []
    for name, data in metrics.items():
        mean, ci_lo, ci_hi, hw = compute_confidence_interval(data)
        rows.append({
            'Metric': name,
            'Mean': f"{mean:.4f}" if mean < 10 else f"{mean:.1f}",
            'Std Dev': f"{np.std(data):.4f}" if np.std(data) < 10 else f"{np.std(data):.1f}",
            '5th Pct': f"{np.percentile(data, 5):.4f}" if np.percentile(data, 5) < 10 else f"{np.percentile(data, 5):.1f}",
            '95th Pct': f"{np.percentile(data, 95):.4f}" if np.percentile(data, 95) < 10 else f"{np.percentile(data, 95):.1f}",
            '95% CI Lower': f"{ci_lo:.4f}" if ci_lo < 10 else f"{ci_lo:.1f}",
            '95% CI Upper': f"{ci_hi:.4f}" if ci_hi < 10 else f"{ci_hi:.1f}",
        })

    return pd.DataFrame(rows)


def convergence_data(mc_df, metric='mcr'):
    """
    Compute running mean and CI as replications increase.

    Returns
    -------
    pd.DataFrame
        Columns: n_reps, running_mean, ci_lower, ci_upper
    """
    vals = mc_df[metric].values
    records = []
    for n in range(2, len(vals) + 1):
        subset = vals[:n]
        mean, lo, hi, hw = compute_confidence_interval(subset)
        records.append({'n_reps': n, 'running_mean': mean,
                        'ci_lower': lo, 'ci_upper': hi, 'ci_hw': hw})
    return pd.DataFrame(records)


def find_min_reps_for_hw(mc_df, target_hw=0.01, metric='mcr'):
    """Find minimum replications for CI half-width below target."""
    conv = convergence_data(mc_df, metric)
    below = conv[conv['ci_hw'] <= target_hw]
    if len(below) > 0:
        return int(below.iloc[0]['n_reps'])
    return len(mc_df)
