"""
KPI Tracker module for the Fleet Availability Simulator.

Records hourly snapshots of fleet status and computes key performance
indicators: Mission Capable Rate (MCR), Full Mission Capable Rate (FMCR),
PAM fraction, and maintenance pipeline metrics.

These are the exact metrics that air force commanders report to government.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
HOURS_PER_DAY = 24


class KPITracker:
    """
    Records and analyses fleet availability KPIs.

    Parameters
    ----------
    fleet_size : int
        Number of aircraft in the fleet.
    warm_up_hours : float
        Hours to exclude from KPI calculation (warm-up period).

    Attributes
    ----------
    snapshots : list of dict
        Hourly fleet status snapshots.
    fleet_size : int
        Fleet size for rate calculations.
    warm_up_hours : float
        Warm-up period in hours.
    """

    def __init__(self, fleet_size, warm_up_hours=0.0):
        self.fleet_size = fleet_size
        self.warm_up_hours = warm_up_hours
        self.snapshots = []

    def record_snapshot(self, env, fleet):
        """
        Record a snapshot of fleet status at current simulation time.

        Parameters
        ----------
        env : simpy.Environment
            SimPy simulation environment (for current time).
        fleet : list of Aircraft
            All aircraft in the fleet.
        """
        fmc_count = 0
        mc_count = 0
        pam_count = 0
        nmc_maint_count = 0
        nmc_depot_count = 0
        sortie_count = 0

        for ac in fleet:
            contrib = ac.get_availability_contribution()
            if contrib['is_fmc']:
                fmc_count += 1
            if contrib['is_mission_capable']:
                mc_count += 1
            if contrib['is_pam']:
                pam_count += 1
            if ac.status == 'NMC_maintenance':
                nmc_maint_count += 1
            if ac.status == 'NMC_depot':
                nmc_depot_count += 1
            if ac.status == 'sortie':
                sortie_count += 1

        snapshot = {
            'time': env.now,
            'fmc': fmc_count,
            'mc': mc_count,
            'pam': pam_count,
            'nmc_maintenance': nmc_maint_count,
            'nmc_depot': nmc_depot_count,
            'sortie': sortie_count,
            'mcr': mc_count / self.fleet_size,
            'fmcr': fmc_count / self.fleet_size,
            'pam_fraction': pam_count / self.fleet_size,
        }
        self.snapshots.append(snapshot)

    def _get_post_warmup_df(self):
        """
        Return DataFrame of snapshots after warm-up period.

        Returns
        -------
        pandas.DataFrame
            Filtered snapshots.
        """
        df = pd.DataFrame(self.snapshots)
        if len(df) == 0:
            return df
        return df[df['time'] >= self.warm_up_hours].reset_index(drop=True)

    def compute_time_averaged_MCR(self):
        """
        Compute time-averaged Mission Capable Rate (post warm-up).

        Returns
        -------
        float
            Mean MCR across all post-warmup snapshots.
        """
        df = self._get_post_warmup_df()
        if len(df) == 0:
            return 0.0
        return df['mcr'].mean()

    def compute_time_averaged_FMCR(self):
        """
        Compute time-averaged Full Mission Capable Rate (post warm-up).

        Returns
        -------
        float
            Mean FMCR across all post-warmup snapshots.
        """
        df = self._get_post_warmup_df()
        if len(df) == 0:
            return 0.0
        return df['fmcr'].mean()

    def compute_PAM_fraction(self):
        """
        Compute time-averaged PAM (Parts Awaiting Maintenance) fraction.

        Returns
        -------
        float
            Mean PAM fraction across all post-warmup snapshots.
        """
        df = self._get_post_warmup_df()
        if len(df) == 0:
            return 0.0
        return df['pam_fraction'].mean()

    def compute_maintenance_pipeline_fraction(self):
        """
        Compute fraction of fleet in maintenance pipeline (NMC_maint + NMC_depot).

        Returns
        -------
        float
            Mean maintenance pipeline fraction.
        """
        df = self._get_post_warmup_df()
        if len(df) == 0:
            return 0.0
        maint_frac = (df['nmc_maintenance'] + df['nmc_depot']) / self.fleet_size
        return maint_frac.mean()

    def get_full_dataframe(self):
        """
        Return complete DataFrame of all snapshots (including warm-up).

        Returns
        -------
        pandas.DataFrame
            All recorded snapshots.
        """
        return pd.DataFrame(self.snapshots)

    def get_results_summary(self):
        """
        Return summary dictionary of all KPIs.

        Returns
        -------
        dict
            Keys: 'mcr', 'fmcr', 'pam_fraction', 'maintenance_pipeline_fraction'.
        """
        return {
            'mcr': self.compute_time_averaged_MCR(),
            'fmcr': self.compute_time_averaged_FMCR(),
            'pam_fraction': self.compute_PAM_fraction(),
            'maintenance_pipeline_fraction': self.compute_maintenance_pipeline_fraction(),
        }

    def plot_availability_timeline(self, title='Fleet Status Over Time',
                                   save_path=None):
        """
        Produce a stacked area chart of fleet status over time.

        Parameters
        ----------
        title : str
            Plot title.
        save_path : str, optional
            Path to save figure. If None, displays interactively.

        Returns
        -------
        matplotlib.figure.Figure
            The generated figure.
        """
        df = pd.DataFrame(self.snapshots)
        if len(df) == 0:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, 'No data', ha='center', va='center')
            return fig

        time_days = df['time'] / HOURS_PER_DAY

        fig, ax = plt.subplots(figsize=(14, 6))

        # Stacked area chart
        categories = ['fmc', 'sortie', 'nmc_maintenance', 'pam', 'nmc_depot']
        labels = ['FMC', 'On Sortie', 'In Maintenance', 'Awaiting Parts', 'In Depot']
        colors = ['#2ecc71', '#3498db', '#f39c12', '#e74c3c', '#8e44ad']

        # Build stacked data
        y_stack = np.zeros((len(df), len(categories)))
        for i, cat in enumerate(categories):
            if cat in df.columns:
                y_stack[:, i] = df[cat].values

        ax.stackplot(time_days, y_stack.T, labels=labels, colors=colors,
                     alpha=0.85)

        # Warm-up boundary
        if self.warm_up_hours > 0:
            ax.axvline(x=self.warm_up_hours / HOURS_PER_DAY,
                       color='red', linestyle='--', alpha=0.7,
                       label='Warm-up boundary')

        ax.set_xlabel('Simulation Day', fontsize=12)
        ax.set_ylabel('Number of Aircraft', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend(loc='upper right', fontsize=10)
        ax.set_ylim(0, self.fleet_size)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight')
        return fig

    def plot_mcr_timeline(self, title='Mission Capable Rate Over Time',
                          save_path=None):
        """
        Plot MCR over time with warm-up boundary.

        Parameters
        ----------
        title : str
            Plot title.
        save_path : str, optional
            Path to save figure.

        Returns
        -------
        matplotlib.figure.Figure
            The generated figure.
        """
        df = pd.DataFrame(self.snapshots)
        if len(df) == 0:
            fig, ax = plt.subplots()
            return fig

        time_days = df['time'] / HOURS_PER_DAY

        fig, ax = plt.subplots(figsize=(14, 4))
        ax.plot(time_days, df['mcr'] * 100, color='#2980b9', alpha=0.7,
                linewidth=0.5)

        # Rolling average
        window = min(24, len(df))
        rolling_mcr = df['mcr'].rolling(window=window, min_periods=1).mean()
        ax.plot(time_days, rolling_mcr * 100, color='#2c3e50', linewidth=2,
                label=f'{window}-hour rolling average')

        # 75% threshold
        ax.axhline(y=75, color='#e74c3c', linestyle='--', alpha=0.7,
                   label='75% threshold')

        if self.warm_up_hours > 0:
            ax.axvline(x=self.warm_up_hours / HOURS_PER_DAY,
                       color='red', linestyle='--', alpha=0.5)

        ax.set_xlabel('Simulation Day', fontsize=12)
        ax.set_ylabel('MCR (%)', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend(fontsize=10)
        ax.set_ylim(0, 105)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight')
        return fig
