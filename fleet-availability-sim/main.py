"""
Combat Aircraft Fleet Availability Simulator — Main Entry Point.

Runs a single simulation with default parameters and prints summary KPIs.

Usage
-----
    python main.py

For more detailed analysis, see the Jupyter notebooks in notebooks/ or
the Streamlit dashboard in dashboard/app.py.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.simulation import FleetSimulation
from src.distributions import weibull_mean

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
HOURS_PER_DAY = 24


def print_banner():
    """Print project banner."""
    print("=" * 70)
    print("  COMBAT AIRCRAFT FLEET AVAILABILITY SIMULATOR")
    print("  Interactive Analysis Tool — Defence Operations Research")
    print("=" * 70)
    print()


def print_weibull_summary():
    """Print analytical Weibull MTTF for each subsystem."""
    from src.subsystem import SUBSYSTEM_PARAMS

    print("Subsystem Weibull Parameters & Analytical MTTF:")
    print("-" * 55)
    print(f"{'Subsystem':<14} {'Beta':<8} {'Eta (hrs)':<12} {'MTTF (hrs)':<12}")
    print("-" * 55)
    for name, params in SUBSYSTEM_PARAMS.items():
        mttf = weibull_mean(params['beta'], params['eta'])
        print(f"{name:<14} {params['beta']:<8.1f} {params['eta']:<12.0f} {mttf:<12.1f}")
    print()


def run_single_simulation():
    """Run a single simulation and print results."""
    print("Running simulation: 12 aircraft, 180 days, seed=42...")
    print("(30-day warm-up period excluded from KPIs)")
    print()

    sim = FleetSimulation(
        fleet_size=12,
        o_level_techs_day=8,
        i_level_techs_day=4,
        d_level_techs=6,
        sortie_interval_hours=48,
    )

    result = sim.run(
        simulation_days=180,
        surge_start_day=None,
        surge_duration_hours=None,
        random_seed=42,
    )

    # Print results
    print("=" * 50)
    print("  SIMULATION RESULTS")
    print("=" * 50)
    print(f"  Mission Capable Rate (MCR):  {result['mcr'] * 100:.1f}%")
    print(f"  Full Mission Capable (FMCR): {result['fmcr'] * 100:.1f}%")
    print(f"  PAM Fraction:                {result['pam_fraction'] * 100:.1f}%")
    print(f"  Maintenance Pipeline:        {result['maintenance_pipeline_fraction'] * 100:.1f}%")
    print(f"  Total Sorties:               {result['total_sorties']}")
    print(f"  Total Flight Hours:          {result['total_flight_hours']:.0f}")
    print("=" * 50)
    print()

    # MCR assessment
    mcr_pct = result['mcr'] * 100
    if mcr_pct >= 75:
        print(f"  ✓ MCR {mcr_pct:.1f}% MEETS 75% threshold")
    elif mcr_pct >= 60:
        print(f"  ⚠ MCR {mcr_pct:.1f}% is BELOW 75% threshold (amber)")
    else:
        print(f"  ✗ MCR {mcr_pct:.1f}% is CRITICALLY LOW (red)")

    # Benchmark comparison
    print()
    print("Benchmark Comparison (publicly available data):")
    print(f"  F-16 (GAO-21-279):     71.9%")
    print(f"  F/A-18 (GAO-21-279):   62.1%")
    print(f"  IAF fighters (CAG-21): 75-80%")
    print(f"  This model:            {mcr_pct:.1f}%")
    print()

    return result


def main():
    """Main entry point."""
    print_banner()
    print_weibull_summary()
    result = run_single_simulation()

    # Generate availability timeline plot
    try:
        kpi_tracker = result['kpi_tracker']
        fig = kpi_tracker.plot_availability_timeline(
            title='Fleet Status Over Time (Single Run, Seed=42)',
            save_path=None,
        )
        import matplotlib.pyplot as plt
        plt.show()
    except Exception as e:
        print(f"Note: Could not display plot ({e})")

    print("\nFor full analysis, run:")
    print("  streamlit run dashboard/app.py")
    print("  python generate_report.py")
    print("  jupyter notebook notebooks/01_single_run_walkthrough.ipynb")


if __name__ == '__main__':
    main()
