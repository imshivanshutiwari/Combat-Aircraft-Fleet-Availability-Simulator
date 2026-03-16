"""
Generate Research Report — Standalone Script.

Runs the full technician sweep experiment and generates the publishable
PDF research report at docs/research_report.pdf.

Usage
-----
    python generate_report.py

This may take several minutes depending on the number of replications.
For a quick test, reduce replications with --quick flag.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import argparse
from src.research_question import ResearchAnalysis


def main():
    """Generate research report."""
    parser = argparse.ArgumentParser(
        description='Generate Combat Aircraft Fleet Availability Research Report'
    )
    parser.add_argument(
        '--quick', action='store_true',
        help='Quick mode: 5 replications per config (for testing)'
    )
    parser.add_argument(
        '--replications', type=int, default=50,
        help='Number of replications per configuration (default: 50)'
    )
    args = parser.parse_args()

    reps = 5 if args.quick else args.replications

    print("=" * 60)
    print("  RESEARCH REPORT GENERATOR")
    print("  Combat Aircraft Fleet Availability Simulator")
    print("=" * 60)
    print()
    print(f"  Replications per config: {reps}")
    print(f"  Fleet sizes: [8, 10, 12, 16, 20]")
    print(f"  Tech ratios: [0.4, 0.6, 0.8, 1.0, 1.2, 1.5]")
    print(f"  Total configs: 30")
    print(f"  Total simulation runs: {30 * reps}")
    print()

    # Run analysis
    analysis = ResearchAnalysis(replications_per_config=reps)

    print("Phase 1: Running technician sweep experiment...")
    results_df = analysis.run_technician_sweep()
    print(f"  ✓ Sweep complete: {len(results_df)} configurations evaluated")
    print()

    print("Phase 2: Finding minimum viable ratios...")
    min_ratios = analysis.find_minimum_viable_ratio()
    for fs, ratio in sorted(min_ratios.items()):
        status = f"{ratio:.1f}" if ratio is not None else "None achieves 75%"
        print(f"  Fleet size {fs}: min ratio = {status}")
    print()

    print("Phase 3: Generating PDF report...")
    report_path = analysis.generate_research_report()
    print(f"  ✓ Report generated: {report_path}")
    print()
    print("Done!")


if __name__ == '__main__':
    main()
