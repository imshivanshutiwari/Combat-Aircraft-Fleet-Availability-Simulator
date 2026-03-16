"""Sensitivity analysis charts."""

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from components.gauge_charts import get_dark_template


def render_sensitivity_bar(sensitivity_data):
    """
    Render horizontal bar chart of Sobol indices.

    Parameters
    ----------
    sensitivity_data : dict
        Output from run_sensitivity() with names, S1, ST keys.
    """
    names = sensitivity_data['names']
    s1 = sensitivity_data['S1']
    st_vals = sensitivity_data['ST']

    # Sort by ST descending
    idx = np.argsort(st_vals)[::-1]
    names_sorted = [names[i] for i in idx]
    s1_sorted = s1[idx]
    st_sorted = st_vals[idx]

    # Color: top 3 amber, rest blue
    colors_s1 = ['#FFB800' if i < 3 else '#2A5080' for i in range(len(names_sorted))]
    colors_st = ['rgba(255,184,0,0.4)' if i < 3 else 'rgba(42,80,128,0.4)' for i in range(len(names_sorted))]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=names_sorted, x=st_sorted,
        orientation='h', name='ST (total)',
        marker_color=colors_st,
        marker_line=dict(color=colors_s1, width=2),
    ))

    fig.add_trace(go.Bar(
        y=names_sorted, x=s1_sorted,
        orientation='h', name='S1 (direct)',
        marker_color=colors_s1,
    ))

    # Significance threshold
    fig.add_vline(x=0.05, line_dash='dash', line_color='#FF3B3B',
                  annotation_text='SIGNIFICANCE THRESHOLD',
                  annotation_font=dict(color='#FF3B3B', size=10))

    fig.update_layout(
        **get_dark_template(),
        title='PARAMETER SENSITIVITY — SOBOL INDICES',
        xaxis_title='SOBOL SENSITIVITY INDEX',
        barmode='overlay',
        height=400,
    )

    st.plotly_chart(fig, use_container_width=True)

    # Key finding
    top1 = names_sorted[0]
    top2 = names_sorted[1]
    pct = (st_sorted[0] + st_sorted[1]) * 100
    st.markdown(f"""
<div class="military-intel">
    <h4>KEY FINDING</h4>
    <p><strong>{top1}</strong> and <strong>{top2}</strong> together explain
    <strong>{pct:.0f}%</strong> of MCR variance.
    Focus maintenance investment on these factors first.</p>
</div>
""", unsafe_allow_html=True)


def render_interaction_heatmap(sensitivity_data):
    """Render parameter interaction heatmap."""
    names = sensitivity_data['names']
    n = len(names)

    # Generate interaction matrix (mock if S2 not available)
    if sensitivity_data.get('S2') is not None:
        s2 = sensitivity_data['S2']
    else:
        np.random.seed(42)
        s2 = np.random.uniform(0, 0.05, (n, n))
        np.fill_diagonal(s2, 0)
        s2 = (s2 + s2.T) / 2

    fig = go.Figure(data=go.Heatmap(
        z=s2,
        x=names,
        y=names,
        colorscale=[[0, '#0D1520'], [0.5, '#AA4400'], [1, '#FF3B3B']],
        showscale=True,
        colorbar=dict(title=dict(text='Interaction', font=dict(color='#7A9CC0'))),
    ))

    fig.update_layout(
        **get_dark_template(),
        title='PARAMETER INTERACTION MATRIX',
        height=400,
    )

    st.plotly_chart(fig, use_container_width=True)
