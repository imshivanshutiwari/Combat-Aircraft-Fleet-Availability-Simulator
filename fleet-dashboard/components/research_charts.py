"""Research findings charts — heatmap, threshold curve, key finding."""

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from components.gauge_charts import get_dark_template


def render_research_heatmap(results_df):
    """
    Render the technician ratio vs fleet size heatmap.

    Parameters
    ----------
    results_df : pd.DataFrame
        Output from run_technician_sweep().
    """
    fleet_sizes = sorted(results_df['fleet_size'].unique())
    tech_ratios = sorted(results_df['tech_ratio'].unique())

    z_matrix = np.zeros((len(tech_ratios), len(fleet_sizes)))
    for i, tr in enumerate(tech_ratios):
        for j, fs in enumerate(fleet_sizes):
            row = results_df[(results_df['fleet_size'] == fs) &
                             (results_df['tech_ratio'] == tr)]
            if len(row) > 0:
                z_matrix[i, j] = row.iloc[0]['mean_surge_mcr'] * 100

    fig = go.Figure(data=go.Heatmap(
        z=z_matrix,
        x=[str(fs) for fs in fleet_sizes],
        y=[f"{tr:.1f}" for tr in tech_ratios],
        colorscale=[
            [0, '#660022'], [0.4, '#FF3B3B'],
            [0.6, '#FFB800'], [0.75, '#88CC44'],
            [1, '#00FF88'],
        ],
        zmin=40, zmax=100,
        showscale=True,
        colorbar={'title': {'text': 'MCR%', 'font': {'color': '#7A9CC0'}}},
    ))

    # Add 75% contour line annotation
    fig.add_annotation(
        text="── 75% OPERATIONAL THRESHOLD ──",
        xref='paper', yref='paper',
        x=0.5, y=1.05,
        showarrow=False,
        font={'color': '#FFB800', 'size': 14, 'family': 'JetBrains Mono', 'weight': 'bold'},
    )

    fig.update_layout(
        **get_dark_template(),
        title='SURGE MCR — FLEET SIZE × TECHNICIAN RATIO',
        xaxis_title='FLEET SIZE (AIRCRAFT)',
        yaxis_title='TECH:AIRCRAFT RATIO',
        height=450,
    )

    st.plotly_chart(fig, use_container_width=True)


def render_threshold_curve(min_ratios):
    """
    Plot minimum viable ratio vs fleet size.

    Parameters
    ----------
    min_ratios : dict
        fleet_size → minimum viable ratio.
    """
    sizes = sorted(min_ratios.keys())
    ratios = [min_ratios[s] for s in sizes]

    # Fit polynomial
    if len(sizes) >= 2:
        coeffs = np.polyfit(sizes, ratios, 2)
        fit_x = np.linspace(min(sizes), max(sizes), 50)
        fit_y = np.polyval(coeffs, fit_x)
        eq = f"y = {coeffs[0]:.4f}x² + {coeffs[1]:.3f}x + {coeffs[2]:.2f}"
    else:
        fit_x, fit_y, eq = [], [], "Insufficient data"

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=list(sizes), y=ratios,
        mode='markers+lines',
        marker={'size': 12, 'color': '#FFB800',
                    'line': {'width': 2, 'color': '#E0E8FF'}},
        line={'color': '#FFB800', 'width': 2},
        name='Observed',
    ))

    if len(fit_x) > 0:
        fig.add_trace(go.Scatter(
            x=list(fit_x), y=list(fit_y),
            mode='lines',
            line={'color': '#FF3B3B', 'width': 1, 'dash': 'dash'},
            name='Fitted Curve',
        ))

    fig.add_annotation(
        text=f"SUPERLINEAR SCALING: {eq}",
        xref='paper', yref='paper',
        x=0.5, y=-0.22,
        showarrow=False,
        font={'color': '#00FF88', 'size': 13, 'family': 'JetBrains Mono', 'weight': 'bold'},
    )

    fig.update_layout(
        **get_dark_template(),
        title='MINIMUM VIABLE TECHNICIAN RATIO vs FLEET SIZE',
        xaxis_title='FLEET SIZE',
        yaxis_title='MIN TECH:AIRCRAFT RATIO',
        height=350,
    )

    st.plotly_chart(fig, use_container_width=True)


def render_key_finding(finding):
    """Render the key finding highlight box."""
    st.markdown(f"""
    <div class="key-finding" style="padding: 32px;">
        <div style="color:#A0C0E0;font-size:1rem;letter-spacing:3px;margin-bottom:16px;font-weight:700;">
            KEY RESEARCH FINDING
        </div>
        <div class="number" style="font-size:4rem; margin: 12px 0;">{finding['ratio']:.1f}</div>
        <div style="color:#A0C0E0;font-size:1.1rem;margin-top:12px;font-weight:700;">
            MINIMUM TECH:AIRCRAFT RATIO FOR {finding['fleet_size']}-AIRCRAFT FLEET
        </div>
        <div style="color:#FFFFFF;font-size:1.05rem;margin-top:16px;
                    padding:16px;background:rgba(26,58,92,0.4);border:1px solid #1A3A5C;border-radius:6px;line-height:1.6;">
            {finding['text']}
        </div>
    </div>
    """, unsafe_allow_html=True)
