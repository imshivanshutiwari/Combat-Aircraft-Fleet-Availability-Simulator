"""
Dashboard component — Surge scenario animator.

Provides MCR timeline with surge region highlighting.
"""

import plotly.graph_objects as go
import numpy as np
import streamlit as st

HOURS_PER_DAY = 24


def render_surge_timeline(kpi_df, surge_start_day=None,
                          surge_duration_hours=None):
    """
    Render MCR timeline with highlighted surge region.

    Parameters
    ----------
    kpi_df : pandas.DataFrame
        KPI time series.
    surge_start_day : int, optional
        Day when surge begins.
    surge_duration_hours : float, optional
        Duration of surge in hours.
    """
    if len(kpi_df) == 0:
        st.warning("No data to display.")
        return

    df = kpi_df.copy()
    df['day'] = df['time'] / HOURS_PER_DAY

    # Rolling MCR
    window = min(24, len(df))
    df['mcr_rolling'] = df['mcr'].rolling(window=window, min_periods=1).mean()

    fig = go.Figure()

    # Raw MCR
    fig.add_trace(go.Scatter(
        x=df['day'], y=df['mcr'] * 100,
        name='MCR (hourly)',
        mode='lines',
        line=dict(color='rgba(52, 152, 219, 0.3)', width=0.5),
    ))

    # Rolling average
    fig.add_trace(go.Scatter(
        x=df['day'], y=df['mcr_rolling'] * 100,
        name=f'MCR ({window}-hour avg)',
        mode='lines',
        line=dict(color='#2980b9', width=2),
    ))

    # 75% threshold
    fig.add_hline(y=75, line=dict(color='#e74c3c', dash='dash', width=1),
                  annotation_text='75% threshold')

    # Surge region
    if surge_start_day is not None and surge_duration_hours is not None:
        surge_end_day = surge_start_day + surge_duration_hours / HOURS_PER_DAY
        fig.add_vrect(
            x0=surge_start_day, x1=surge_end_day,
            fillcolor='rgba(231, 76, 60, 0.15)',
            line=dict(color='rgba(231, 76, 60, 0.5)', width=1),
            annotation_text='SURGE',
            annotation_position='top left',
        )

    fig.update_layout(
        title='Mission Capable Rate Over Time',
        xaxis_title='Simulation Day',
        yaxis_title='MCR (%)',
        yaxis=dict(range=[0, 105]),
        template='plotly_dark',
        height=400,
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
        margin=dict(l=50, r=20, t=60, b=40),
    )

    st.plotly_chart(fig, use_container_width=True)


def render_queue_timeline(queue_history, surge_start_day=None,
                          surge_duration_hours=None):
    """
    Render maintenance queue length over time.

    Parameters
    ----------
    queue_history : list of dict
        Maintenance queue snapshots.
    surge_start_day : int, optional
        Day when surge begins.
    surge_duration_hours : float, optional
        Duration of surge.
    """
    if not queue_history:
        st.info("No queue data available.")
        return

    import pandas as pd
    df = pd.DataFrame(queue_history)
    df['day'] = df['time'] / HOURS_PER_DAY

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df['day'], y=df['o_level_queue'],
        name='O-level Queue', mode='lines',
        line=dict(color='#3498db', width=1.5),
    ))
    fig.add_trace(go.Scatter(
        x=df['day'], y=df['i_level_queue'],
        name='I-level Queue', mode='lines',
        line=dict(color='#f39c12', width=1.5),
    ))
    fig.add_trace(go.Scatter(
        x=df['day'], y=df['d_level_queue'],
        name='D-level Queue', mode='lines',
        line=dict(color='#8e44ad', width=1.5),
    ))

    if surge_start_day is not None and surge_duration_hours is not None:
        surge_end_day = surge_start_day + surge_duration_hours / HOURS_PER_DAY
        fig.add_vrect(
            x0=surge_start_day, x1=surge_end_day,
            fillcolor='rgba(231, 76, 60, 0.1)',
            line=dict(color='rgba(231, 76, 60, 0.3)'),
        )

    fig.update_layout(
        title='Maintenance Queue Length Over Time',
        xaxis_title='Simulation Day',
        yaxis_title='Queue Length',
        template='plotly_dark',
        height=350,
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
        margin=dict(l=50, r=20, t=60, b=40),
    )

    st.plotly_chart(fig, use_container_width=True)
