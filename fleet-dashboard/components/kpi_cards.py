"""KPI cards with military styling and glow effects."""

import streamlit as st


def render_kpi_strip(mcr, fmcr, mcr_ci_hw, fmcr_ci_hw, fleet_summary):
    """
    Render the top KPI strip with three glowing metric cards.

    Parameters
    ----------
    mcr : float
        Mission Capable Rate (0-1).
    fmcr : float
        Full Mission Capable Rate (0-1).
    mcr_ci_hw : float
        MCR confidence interval half-width.
    fmcr_ci_hw : float
        FMCR confidence interval half-width.
    fleet_summary : dict
        Fleet status counts: fmc, pmc, nmc_m, nmc_p, nmc_d.
    """
    c1, c2, c3 = st.columns(3)

    with c1:
        mcr_pct = mcr * 100
        color = '#00FF88' if mcr_pct >= 75 else ('#FFB800' if mcr_pct >= 60 else '#FF3B3B')
        status = 'OPERATIONAL' if mcr_pct >= 75 else ('DEGRADED' if mcr_pct >= 60 else 'CRITICAL')
        badge_class = 'badge-fmc' if mcr_pct >= 75 else ('badge-pmc' if mcr_pct >= 60 else 'badge-nmc')

        st.markdown(f"""
<div class="military-card" style="padding: 20px;">
    <div style="color:#A0C0E0;font-size:0.95rem;letter-spacing:2px;font-weight:700;margin-bottom:8px;">
        MISSION CAPABLE RATE
    </div>
    <div style="font-family:\'JetBrains Mono\',monospace;font-size:3.2rem;font-weight:bold;
                color:{color};text-shadow:0 0 20px {color};">
        {mcr_pct:.1f}%
    </div>
    <div style="color:#A0C0E0;font-size:0.9rem;font-weight:700;margin-top:4px;">
        ± {mcr_ci_hw*100:.1f}% (95% CI)
    </div>
    <div style="margin-top:12px;">
        <span class="status-badge {badge_class}" style="font-size:1rem; padding:6px 16px;">{status}</span>
    </div>
</div>
""", unsafe_allow_html=True)

    with c2:
        fmcr_pct = fmcr * 100
        fcolor = '#00FF88' if fmcr_pct >= 75 else ('#FFB800' if fmcr_pct >= 60 else '#FF3B3B')

        st.markdown(f"""
<div class="military-card" style="padding: 20px;">
    <div style="color:#A0C0E0;font-size:0.95rem;letter-spacing:2px;font-weight:700;margin-bottom:8px;">
        FULL MISSION CAPABLE RATE
    </div>
    <div style="font-family:\'JetBrains Mono\',monospace;font-size:3.2rem;font-weight:bold;
                color:{fcolor};text-shadow:0 0 20px {fcolor};">
        {fmcr_pct:.1f}%
    </div>
    <div style="color:#A0C0E0;font-size:0.9rem;font-weight:700;margin-top:4px;">
        ± {fmcr_ci_hw*100:.1f}% (95% CI)
    </div>
</div>
""", unsafe_allow_html=True)

    with c3:
        fmc = fleet_summary.get('fmc', 0)
        pmc = fleet_summary.get('pmc', 0)
        nmc_m = fleet_summary.get('nmc_m', 0)
        nmc_p = fleet_summary.get('nmc_p', 0)
        nmc_d = fleet_summary.get('nmc_d', 0)
        total = fmc + pmc + nmc_m + nmc_p + nmc_d
        if total == 0:
            total = 1

        bar_html = ""
        segments = [
            (fmc, '#00FF88', 'FMC'),
            (pmc, '#FFB800', 'PMC'),
            (nmc_m, '#FF3B3B', 'NMC-M'),
            (nmc_p, '#FF6600', 'NMC-P'),
            (nmc_d, '#444466', 'NMC-D'),
        ]
        for count, color, label in segments:
            if count > 0:
                pct = count / total * 100
                bar_html += f'<div style="width:{pct}%;background:{color};height:24px;display:inline-block;text-align:center;font-size:0.65rem;line-height:24px;color:#0A0F1A;font-weight:bold;">{label}:{count}</div>'

        st.markdown(f"""
<div class="military-card" style="padding: 20px;">
    <div style="color:#A0C0E0;font-size:0.95rem;letter-spacing:2px;font-weight:700;margin-bottom:8px;">
        FLEET STATUS BREAKDOWN
    </div>
    <div style="margin-top:16px;display:flex;border-radius:6px;overflow:hidden;border:1px solid #1A3A5C;">
        {bar_html}
    </div>
    <div style="color:#A0C0E0;font-size:0.85rem;margin-top:12px;font-weight:700;">
        {total} AIRCRAFT | {fmc} READY FOR TASKING
    </div>
</div>
""", unsafe_allow_html=True)
