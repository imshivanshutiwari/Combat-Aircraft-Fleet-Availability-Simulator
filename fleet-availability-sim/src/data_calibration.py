"""
Data Calibration module for the Fleet Availability Simulator.

Handles calibration of model parameters against real-world reference data.
Generates synthetic reference data matching published benchmarks when
real DGCA data is unavailable.

References
----------
US GAO Report GAO-21-279: Fighter aircraft reliability and maintainability.
Indian CAG Report 2021 on Air Force readiness.
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import ks_2samp, norm
from scipy.optimize import minimize
from datetime import datetime

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
HOURS_PER_DAY = 24
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

# Published benchmark MCRs (publicly available government reports)
BENCHMARK_MCRS = {
    'F-16': 0.719,       # GAO-21-279
    'F-35A': 0.546,      # GAO-21-279
    'F/A-18': 0.621,     # GAO-21-279
    'IAF_high': 0.80,    # CAG 2021 upper bound
    'IAF_low': 0.75,     # CAG 2021 lower bound
}

# Synthetic data generation parameters
SYNTHETIC_MCR_MEAN = 0.72
AR1_PHI = 0.7                    # Autocorrelation coefficient
MONSOON_MONTHS = [6, 7, 8, 9]   # June-September
MONSOON_MCR_DROP = 0.03          # 3 percentage points
MONDAY_MCR_DROP = 0.02           # 2 percentage points


def load_or_generate_reference_data():
    """
    Load real DGCA data or generate synthetic reference dataset.

    Attempts to load from data/dgca_utilisation_raw.csv. If not found,
    generates a synthetic dataset with 365 daily MCR observations
    statistically matching published benchmarks.

    Returns
    -------
    pandas.DataFrame
        DataFrame with columns: 'day', 'date', 'mcr', 'day_of_week',
        'month', 'is_monsoon', 'is_monday'.

    Notes
    -----
    Synthetic data uses AR(1) process with phi=0.7 for temporal
    autocorrelation, plus seasonal (monsoon) and weekly (Monday)
    effects matching published patterns.
    """
    dgca_path = os.path.join(DATA_DIR, 'dgca_utilisation_raw.csv')

    if os.path.exists(dgca_path):
        try:
            df = pd.read_csv(dgca_path)
            if 'mcr' in df.columns:
                return df
        except Exception:
            pass

    # Generate synthetic reference data
    rng = np.random.RandomState(2024)  # Local RNG — zero global random state
    n_days = 365

    # AR(1) process for base MCR
    innovations = rng.normal(0, 0.03, n_days)  # Innovation variance
    mcr_series = np.zeros(n_days)
    mcr_series[0] = SYNTHETIC_MCR_MEAN + innovations[0]

    for t in range(1, n_days):
        mcr_series[t] = (SYNTHETIC_MCR_MEAN * (1 - AR1_PHI)
                         + AR1_PHI * mcr_series[t - 1]
                         + innovations[t])

    # Start date: 1 January (Monday for weekly alignment)
    dates = pd.date_range('2024-01-01', periods=n_days, freq='D')
    df = pd.DataFrame({
        'day': range(n_days),
        'date': dates,
        'mcr': mcr_series,
        'day_of_week': dates.dayofweek,   # 0=Monday
        'month': dates.month,
    })

    # Apply monsoon effect (June-September)
    df['is_monsoon'] = df['month'].isin(MONSOON_MONTHS)
    df.loc[df['is_monsoon'], 'mcr'] -= MONSOON_MCR_DROP

    # Apply Monday effect
    df['is_monday'] = df['day_of_week'] == 0
    df.loc[df['is_monday'], 'mcr'] -= MONDAY_MCR_DROP

    # Clip to valid range
    df['mcr'] = df['mcr'].clip(0.30, 0.98)

    return df


class DataCalibrator:
    """
    Calibrates simulation parameters against reference data.

    Parameters
    ----------
    sim_class : class
        FleetSimulation class to instantiate during calibration.
    base_config : dict
        Default simulation configuration.
    """

    def __init__(self, sim_class, base_config=None):
        self.sim_class = sim_class
        self.base_config = base_config or {}
        self.calibration_history = []

    def calibrate_weibull_parameters(self, reference_mcr_series,
                                      n_quick_sims=50):
        """
        Find Weibull eta parameters minimising SSE vs reference MCR.

        Parameters
        ----------
        reference_mcr_series : array-like
            Reference daily MCR values.
        n_quick_sims : int
            Number of quick simulations per candidate parameter set.

        Returns
        -------
        dict
            Calibrated parameters: {'engine_eta', 'avionics_eta',
            'hydraulics_eta', 'airframe_eta'}.

        Notes
        -----
        Uses scipy.optimize.minimize with Nelder-Mead method.
        Runs short (90-day) simulations for speed during optimisation.
        """
        reference_mean = np.mean(reference_mcr_series)

        def objective(eta_values):
            """Sum of squared errors between simulated and reference MCR."""
            engine_eta, avionics_eta, hydraulics_eta, airframe_eta = eta_values

            subsystem_params = {
                'engine': {'eta': engine_eta},
                'avionics': {'eta': avionics_eta},
                'hydraulics': {'eta': hydraulics_eta},
                'airframe': {'eta': airframe_eta},
            }

            config = dict(self.base_config)
            config['subsystem_params'] = subsystem_params

            sim = self.sim_class(**config)
            mcrs = []
            for i in range(n_quick_sims):
                result = sim.run(simulation_days=90, random_seed=100 + i)
                mcrs.append(result['mcr'])

            sim_mean = np.mean(mcrs)
            sse = (sim_mean - reference_mean) ** 2

            self.calibration_history.append({
                'etas': list(eta_values),
                'sim_mean_mcr': sim_mean,
                'reference_mean_mcr': reference_mean,
                'sse': sse,
            })

            return sse

        # Initial guesses (defaults)
        x0 = [800, 600, 1200, 2000]
        bounds = [(400, 1600), (300, 1200), (600, 2400), (1000, 4000)]

        result = minimize(objective, x0, method='Nelder-Mead',
                          options={'maxiter': 30, 'xatol': 50, 'fatol': 0.0001})

        calibrated = {
            'engine_eta': result.x[0],
            'avionics_eta': result.x[1],
            'hydraulics_eta': result.x[2],
            'airframe_eta': result.x[3],
        }

        return calibrated

    def goodness_of_fit_test(self, simulated_mcr_series, reference_mcr_series):
        """
        Two-sample Kolmogorov-Smirnov test for model validation.

        Parameters
        ----------
        simulated_mcr_series : array-like
            Simulated MCR values.
        reference_mcr_series : array-like
            Reference MCR values.

        Returns
        -------
        dict
            'ks_statistic', 'p_value', 'interpretation' (plain English).
        """
        ks_stat, p_value = ks_2samp(simulated_mcr_series, reference_mcr_series)

        if p_value >= 0.05:
            interpretation = (
                f"Model fits reference data (p={p_value:.4f}, "
                f"fail to reject H0 at 5% level)"
            )
        else:
            interpretation = (
                f"Model does not fit reference data (p={p_value:.4f})"
            )

        return {
            'ks_statistic': ks_stat,
            'p_value': p_value,
            'interpretation': interpretation,
        }

    def plot_calibration_results(self, simulated_series, reference_series,
                                 save_path=None):
        """
        Produce 4-panel calibration comparison figure.

        Parameters
        ----------
        simulated_series : array-like
            Simulated MCR values.
        reference_series : array-like
            Reference MCR values.
        save_path : str, optional
            Path to save figure.

        Returns
        -------
        matplotlib.figure.Figure
            4-panel figure.

        Notes
        -----
        Panels: (1) Histogram comparison with Normal fits,
        (2) Q-Q plot, (3) Time series overlay (first 90 days),
        (4) Autocorrelation function comparison.
        """
        sim = np.asarray(simulated_series)
        ref = np.asarray(reference_series)

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        # Panel 1: Histogram comparison
        ax1 = axes[0, 0]
        ax1.hist(ref, bins=30, alpha=0.5, density=True, color='#3498db',
                 label='Reference')
        ax1.hist(sim, bins=30, alpha=0.5, density=True, color='#e74c3c',
                 label='Simulated')
        # Overlay Normal fits
        x_range = np.linspace(
            min(ref.min(), sim.min()),
            max(ref.max(), sim.max()), 100
        )
        ax1.plot(x_range, norm.pdf(x_range, ref.mean(), ref.std()),
                 'b--', linewidth=2)
        ax1.plot(x_range, norm.pdf(x_range, sim.mean(), sim.std()),
                 'r--', linewidth=2)
        ax1.set_title('MCR Distribution Comparison', fontweight='bold')
        ax1.set_xlabel('MCR')
        ax1.set_ylabel('Density')
        ax1.legend()

        # Panel 2: Q-Q plot
        ax2 = axes[0, 1]
        sim_sorted = np.sort(sim)
        ref_sorted = np.sort(ref)
        n_points = min(len(sim_sorted), len(ref_sorted))
        sim_quantiles = np.quantile(sim_sorted,
                                     np.linspace(0, 1, n_points))
        ref_quantiles = np.quantile(ref_sorted,
                                     np.linspace(0, 1, n_points))
        ax2.scatter(ref_quantiles, sim_quantiles, alpha=0.5, s=10,
                    color='#2c3e50')
        lims = [min(ref_quantiles.min(), sim_quantiles.min()),
                max(ref_quantiles.max(), sim_quantiles.max())]
        ax2.plot(lims, lims, 'r--', linewidth=1)
        ax2.set_title('Q-Q Plot', fontweight='bold')
        ax2.set_xlabel('Reference Quantiles')
        ax2.set_ylabel('Simulated Quantiles')

        # Panel 3: Time series overlay (first 90 days)
        ax3 = axes[1, 0]
        n_overlay = min(90, len(sim), len(ref))
        ax3.plot(range(n_overlay), ref[:n_overlay], color='#3498db',
                 alpha=0.7, label='Reference', linewidth=1)
        ax3.plot(range(n_overlay), sim[:n_overlay], color='#e74c3c',
                 alpha=0.7, label='Simulated', linewidth=1)
        ax3.set_title('Time Series Overlay (First 90 Days)', fontweight='bold')
        ax3.set_xlabel('Day')
        ax3.set_ylabel('MCR')
        ax3.legend()

        # Panel 4: Autocorrelation comparison
        ax4 = axes[1, 1]
        max_lag = min(30, len(sim) - 1, len(ref) - 1)
        ref_acf = [np.corrcoef(ref[:-lag], ref[lag:])[0, 1]
                    for lag in range(1, max_lag + 1)]
        sim_acf = [np.corrcoef(sim[:-lag], sim[lag:])[0, 1]
                    for lag in range(1, max_lag + 1)]
        lags = range(1, max_lag + 1)
        ax4.plot(lags, ref_acf, 'o-', color='#3498db', label='Reference',
                 markersize=4)
        ax4.plot(lags, sim_acf, 's-', color='#e74c3c', label='Simulated',
                 markersize=4)
        ax4.set_title('Autocorrelation Function', fontweight='bold')
        ax4.set_xlabel('Lag (days)')
        ax4.set_ylabel('ACF')
        ax4.legend()
        ax4.axhline(y=0, color='gray', linestyle='--', alpha=0.5)

        plt.suptitle('Model Calibration Results', fontsize=16,
                     fontweight='bold', y=1.02)
        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight')

        return fig

    def save_calibration_results(self, calibrated_params, fit_stats,
                                  output_path=None):
        """
        Save calibration results to JSON.

        Parameters
        ----------
        calibrated_params : dict
            Calibrated Weibull eta parameters.
        fit_stats : dict
            KS test results from goodness_of_fit_test().
        output_path : str, optional
            Output file path. Defaults to data/calibration_results.json.
        """
        if output_path is None:
            output_path = os.path.join(DATA_DIR, 'calibration_results.json')

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        results = {
            'timestamp': datetime.now().isoformat(),
            'calibrated_parameters': calibrated_params,
            'ks_statistic': fit_stats['ks_statistic'],
            'p_value': fit_stats['p_value'],
            'interpretation': fit_stats['interpretation'],
            'notes': (
                'Calibrated against synthetic reference data based on '
                'US GAO-21-279 and Indian CAG 2021 benchmarks.'
            ),
        }

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"Calibration results saved to {output_path}")
