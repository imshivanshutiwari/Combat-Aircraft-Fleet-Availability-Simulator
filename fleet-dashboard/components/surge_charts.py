"""Surge analysis charts."""

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from components.gauge_charts import get_dark_template


def render_surge_analysis(mc_results, surge_start, surge_dur):
    """
    Render surge impact assessment tab.

    Parameters
    ----------
    mc_results : list
        List of result dicts from Monte Carlo runs.
    surge_start : int
        Surge start day.
    surge_dur : float
        Surge duration hours.
    """
    if not mc_results:
        st.info("Run simulation with surge enabled.")
        return

    surge_start_h = surge_start * 24
    surge_end_h = surge_start_h + surge_dur
    surge_end_day = surge_start + surge_dur / 24

    # Compute mean MCR across replications per hour
    all_dfs = [r['kpi_df'] for r in mc_results if 'kpi_df' in r]
    if not all_dfs:
        st.info("No KPI data available.")
        return

    # Align on common time axis
    min_len = min(len(df) for df in all_dfs)
    mcr_matrix = np.array([df['mcr'].values[:min_len] for df in all_dfs])
    times = all_dfs[0]['time'].values[:min_len]
    days = times / 24.0

    mean_mcr = np.mean(mcr_matrix, axis=0)
    ci_lo = np.percentile(mcr_matrix, 2.5, axis=0)
    ci_hi = np.percentile(mcr_matrix, 97.5, axis=0)

    # MCR during surge
    surge_mask = (times >= surge_start_h) & (times <= surge_end_h)
    mcr_during = mean_mcr[surge_mask].mean() if surge_mask.any() else 0

    # MCR 7 days post-surge
    post_start = surge_end_h
    post_end = post_start + 7 * 24
    post_mask = (times >= post_start) & (times <= post_end)
    mcr_post = mean_mcr[post_mask].mean() if post_mask.any() else 0

    # Recovery time (when MCR returns to pre-surge baseline)
    pre_surge_mask = times < surge_start_h
    baseline = mean_mcr[pre_surge_mask].mean() if pre_surge_mask.any() else 0.75
    recovery_day = None
    for i in range(len(times)):
        if times[i] > surge_end_h and mean_mcr[i] >= baseline * 0.98:
            recovery_day = days[i] - surge_end_day
            break

    # Top metric cards
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
<div class="military-card" style="border-left:4px solid #FF3B3B;">
    <div style="color:#7A9CC0;font-size:0.7rem;">MCR DURING SURGE</div>
    <div style="font-family:monospace;font-size:2rem;color:#FF3B3B;
                text-shadow:0 0 10px rgba(255,59,59,0.5);">
        {mcr_during*100:.1f}%
    </div>
</div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
<div class="military-card" style="border-left:4px solid #FFB800;">
    <div style="color:#7A9CC0;font-size:0.7rem;">MCR 7-DAY POST-SURGE</div>
    <div style="font-family:monospace;font-size:2rem;color:#FFB800;
                text-shadow:0 0 10px rgba(255,184,0,0.5);">
        {mcr_post*100:.1f}%
    </div>
</div>""", unsafe_allow_html=True)
    with c3:
        rec_text = f"{recovery_day:.1f} DAYS" if recovery_day else "N/A"
        st.markdown(f"""
<div class="military-card" style="border-left:4px solid #00FF88;">
    <div style="color:#7A9CC0;font-size:0.7rem;">RECOVERY TIME</div>
    <div style="font-family:monospace;font-size:2rem;color:#00FF88;
                text-shadow:0 0 10px rgba(0,255,136,0.5);">
        {rec_text}
    </div>
</div>""", unsafe_allow_html=True)

    # Time series plot
    # Downsample
    step = max(1, len(days) // 500)
    d_ds = days[::step]
    m_ds = mean_mcr[::step]
    lo_ds = ci_lo[::step]
    hi_ds = ci_hi[::step]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=d_ds, y=hi_ds * 100,
        mode='lines', line=dict(width=0), showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=d_ds, y=lo_ds * 100,
        mode='lines', line=dict(width=0), fill='tonexty',
        fillcolor='rgba(0,255,136,0.15)', name='95% CI',
    ))
    fig.add_trace(go.Scatter(
        x=d_ds, y=m_ds * 100,
        mode='lines', line=dict(color='#00FF88', width=2),
        name='Mean MCR',
    ))

    # Surge region
    fig.add_vrect(x0=surge_start, x1=surge_end_day,
                  fillcolor='rgba(255,0,0,0.15)', line_width=0)
    fig.add_hline(y=75, line_dash='dash', line_color='#00FF88',
                  annotation_text='OPERATIONAL THRESHOLD',
                  annotation_font=dict(color='#00FF88', size=10))

    fig.update_layout(
        **get_dark_template(),
        title='SURGE OPERATIONS IMPACT — MCR WITH 95% CI',
        xaxis_title='SIMULATED DAY',
        yaxis_title='MCR (%)',
        yaxis_range=[0, 105],
        height=400,
    )

    st.plotly_chart(fig, use_container_width=True)

    # Assessment box
    rec_str = f"{recovery_day:.1f}" if recovery_day else 'N/A'
    st.markdown(f"""
<div class="military-intel">
    <h4>ASSESSMENT</h4>
    <p>Under current maintenance establishment, fleet MCR drops from
    <strong>{baseline*100:.1f}%</strong> to <strong>{mcr_during*100:.1f}%</strong>
    during {int(surge_dur)}-hour surge. Recovery to baseline requires
    <strong>{rec_str} days</strong>.</p>
</div>
""", unsafe_allow_html=True)
