"""
Report generator — creates formatted Streamlit markdown report.
"""

import streamlit as st
import numpy as np


def render_executive_summary(result, mc_df=None, fleet_size=12):
    """
    Render a formatted executive summary report.

    Parameters
    ----------
    result : dict
        Single simulation results.
    mc_df : pd.DataFrame or None
        Monte Carlo summary results.
    fleet_size : int
        Fleet size for the report.
    """
    mcr = result.get('mcr', 0) * 100
    fmcr = result.get('fmcr', 0) * 100
    pam = result.get('pam', 0) * 100
    sorties = result.get('total_sorties', 0)
    hours = result.get('total_hours', 0)

    status = 'OPERATIONAL' if mcr >= 75 else ('DEGRADED' if mcr >= 60 else 'CRITICAL')
    status_color = '#00FF88' if mcr >= 75 else ('#FFB800' if mcr >= 60 else '#FF3B3B')

    st.markdown(f"""
<div class="military-card" style="text-align:center;padding:24px;">
    <div style="color:#7A9CC0;font-size:0.8rem;letter-spacing:3px;">
        EXECUTIVE SUMMARY — FLEET READINESS ASSESSMENT
    </div>
    <div style="margin:16px 0;">
        <span style="font-family:monospace;font-size:3rem;font-weight:bold;
                     color:{status_color};text-shadow:0 0 20px {status_color};">
            {status}
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns(5)
    metrics = [
        (c1, 'MCR', f'{mcr:.1f}%'),
        (c2, 'FMCR', f'{fmcr:.1f}%'),
        (c3, 'PAM', f'{pam:.1f}%'),
        (c4, 'SORTIES', f'{sorties}'),
        (c5, 'FLT HOURS', f'{hours:.0f}'),
    ]
    for col, label, value in metrics:
        with col:
            st.markdown(f"""
<div class="military-card" style="text-align:center;">
    <div style="color:#7A9CC0;font-size:0.65rem;letter-spacing:1px;">{label}</div>
    <div style="font-family:monospace;font-size:1.3rem;color:#E0E8FF;">{value}</div>
</div>
""", unsafe_allow_html=True)

    # Monte Carlo section
    if mc_df is not None and len(mc_df) > 0:
        st.markdown("#### MONTE CARLO STATISTICAL SUMMARY")
        from simulation.kpi_calculator import compute_summary_stats
        summary = compute_summary_stats(mc_df)
        st.dataframe(summary, use_container_width=True, hide_index=True)

    # Recommendations
    recommendations = []
    if mcr < 75:
        recommendations.append("CRITICAL: MCR below 75% operational threshold. "
                               "Increase O-level technician allocation.")
    if pam > 5:
        recommendations.append("WARNING: Parts availability impacting >5% of fleet. "
                               "Review inventory reorder policies.")
    if fmcr < 60:
        recommendations.append("ALERT: Low FMCR indicates widespread subsystem degradation. "
                               "Consider preemptive maintenance schedule.")
    if not recommendations:
        recommendations.append("Fleet readiness within acceptable parameters. "
                               "Continue current maintenance posture.")

    rec_html = "".join(f"<li>{r}</li>" for r in recommendations)
    st.markdown(f"""
<div class="military-intel">
    <h4>RECOMMENDATIONS</h4>
    <ul style="color:#E0E8FF;margin:0;">{rec_html}</ul>
</div>
""", unsafe_allow_html=True)
