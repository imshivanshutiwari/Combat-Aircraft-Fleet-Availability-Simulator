"""
Dashboard component — KPI metric cards.

Displays MCR, FMCR, and PAM fraction as large styled metric cards
with colour coding: green (≥75%), amber (60-75%), red (<60%).
"""

import streamlit as st


def get_color_class(value):
    """
    Return colour class based on MCR thresholds.

    Parameters
    ----------
    value : float
        Metric value as fraction (0-1).

    Returns
    -------
    tuple
        (colour_hex, status_label).
    """
    pct = value * 100
    if pct >= 75:
        return '#2ecc71', 'GREEN'
    elif pct >= 60:
        return '#f39c12', 'AMBER'
    else:
        return '#e74c3c', 'RED'


def render_kpi_cards(mcr, fmcr, pam_fraction, mcr_ci=None, fmcr_ci=None):
    """
    Render three KPI metric cards.

    Parameters
    ----------
    mcr : float
        Mission Capable Rate (0-1).
    fmcr : float
        Full Mission Capable Rate (0-1).
    pam_fraction : float
        Parts Awaiting Maintenance fraction (0-1).
    mcr_ci : tuple, optional
        (lower, upper) 95% CI for MCR.
    fmcr_ci : tuple, optional
        (lower, upper) 95% CI for FMCR.
    """
    col1, col2, col3 = st.columns(3)

    with col1:
        color, status = get_color_class(mcr)
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e, #16213e);
                    border-radius: 12px; padding: 1.5rem; text-align: center;
                    border: 1px solid rgba(255,255,255,0.1);
                    box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
            <p style="font-size: 2.5rem; font-weight: bold; color: {color};
                      margin: 0;">{mcr*100:.1f}%</p>
            <p style="font-size: 0.9rem; color: #a0a0a0; margin-top: 0.3rem;">
                Mission Capable Rate</p>
            {f'<p style="font-size: 0.75rem; color: #888;">95% CI: [{mcr_ci[0]*100:.1f}%, {mcr_ci[1]*100:.1f}%]</p>' if mcr_ci else ''}
        </div>
        """, unsafe_allow_html=True)

    with col2:
        color, status = get_color_class(fmcr)
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e, #16213e);
                    border-radius: 12px; padding: 1.5rem; text-align: center;
                    border: 1px solid rgba(255,255,255,0.1);
                    box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
            <p style="font-size: 2.5rem; font-weight: bold; color: {color};
                      margin: 0;">{fmcr*100:.1f}%</p>
            <p style="font-size: 0.9rem; color: #a0a0a0; margin-top: 0.3rem;">
                Full Mission Capable Rate</p>
            {f'<p style="font-size: 0.75rem; color: #888;">95% CI: [{fmcr_ci[0]*100:.1f}%, {fmcr_ci[1]*100:.1f}%]</p>' if fmcr_ci else ''}
        </div>
        """, unsafe_allow_html=True)

    with col3:
        pam_color = '#e74c3c' if pam_fraction > 0.10 else '#f39c12' if pam_fraction > 0.05 else '#2ecc71'
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e, #16213e);
                    border-radius: 12px; padding: 1.5rem; text-align: center;
                    border: 1px solid rgba(255,255,255,0.1);
                    box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
            <p style="font-size: 2.5rem; font-weight: bold; color: {pam_color};
                      margin: 0;">{pam_fraction*100:.1f}%</p>
            <p style="font-size: 0.9rem; color: #a0a0a0; margin-top: 0.3rem;">
                PAM Fraction</p>
        </div>
        """, unsafe_allow_html=True)
