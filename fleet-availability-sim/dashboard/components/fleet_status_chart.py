"""
Dashboard component — Fleet status chart.

Provides stacked area chart and per-aircraft heatmap visualisations.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import streamlit as st

HOURS_PER_DAY = 24


def render_fleet_status_chart(kpi_df):
    """
    Render stacked area chart of fleet status over time using Plotly.

    Parameters
    ----------
    kpi_df : pandas.DataFrame
        KPI time series with columns: time, fmc, sortie,
        nmc_maintenance, pam, nmc_depot.
    """
    if len(kpi_df) == 0:
        st.warning("No data to display.")
        return

    df = kpi_df.copy()
    df['day'] = df['time'] / HOURS_PER_DAY

    fig = go.Figure()

    categories = [
        ('fmc', 'FMC', '#2ecc71'),
        ('sortie', 'On Sortie', '#3498db'),
        ('nmc_maintenance', 'In Maintenance', '#f39c12'),
        ('pam', 'Awaiting Parts', '#e74c3c'),
        ('nmc_depot', 'In Depot', '#8e44ad'),
    ]

    for col, name, color in categories:
        if col in df.columns:
            fig.add_trace(go.Scatter(
                x=df['day'], y=df[col],
                name=name,
                mode='lines',
                stackgroup='one',
                line=dict(width=0.5, color=color),
                fillcolor=color,
            ))

    fig.update_layout(
        title='Fleet Status Over Time',
        xaxis_title='Simulation Day',
        yaxis_title='Number of Aircraft',
        template='plotly_dark',
        height=450,
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
        margin=dict(l=50, r=20, t=60, b=40),
    )

    st.plotly_chart(fig, use_container_width=True)


def render_aircraft_heatmap(kpi_df, maintenance_events_dict, fleet_size):
    """
    Render per-aircraft availability heatmap.

    If maintenance events exist, shows repair periods as red blocks.
    Otherwise, shows a weekly MCR trend heatmap derived from the KPI
    time series, which is always populated and always useful.

    Parameters
    ----------
    kpi_df : pandas.DataFrame
        KPI time series with 'time' and 'mcr' columns.
    maintenance_events_dict : dict
        Mapping of aircraft_id to list of maintenance events.
    fleet_size : int
        Number of aircraft in fleet.
    """
    if len(kpi_df) == 0 or fleet_size == 0:
        st.info("No fleet data available for heatmap.")
        return

    total_events = sum(len(v) for v in maintenance_events_dict.values()) if maintenance_events_dict else 0

    if total_events > 0 and maintenance_events_dict:
        # Use maintenance events if available
        max_time = kpi_df['time'].max()
        n_weeks = max(1, int(max_time / (HOURS_PER_DAY * 7)))

        heatmap_data = np.ones((fleet_size, n_weeks))

        for ac_id in range(fleet_size):
            events = maintenance_events_dict.get(ac_id, [])
            for event in events:
                start_week = int(event['start_time'] / (HOURS_PER_DAY * 7))
                end_week = int(event['end_time'] / (HOURS_PER_DAY * 7))
                for w in range(max(0, start_week), min(n_weeks, end_week + 1)):
                    heatmap_data[ac_id, w] = 0

        y_labels = [f'AC-{i:02d}' for i in range(fleet_size)]
        x_labels = [f'W{w+1}' for w in range(n_weeks)]
        title = 'Per-Aircraft Availability (Green=Available, Red=In Maintenance)'
        colorscale = [[0, '#e74c3c'], [1, '#2ecc71']]
    else:
        # Fallback: weekly MCR trend heatmap from KPI data
        df = kpi_df.copy()
        df['day'] = df['time'] / HOURS_PER_DAY
        df['week'] = (df['day'] / 7).astype(int)
        n_weeks = df['week'].max() + 1

        # Create per-status weekly summary
        status_cols = ['fmc', 'pam', 'nmc_maintenance', 'nmc_depot']
        available_cols = [c for c in status_cols if c in df.columns]

        weekly = df.groupby('week').agg(
            mcr=('mcr', 'mean'),
            fmcr=('fmcr', 'mean'),
        ).reset_index()

        # Build a multi-row heatmap: MCR, FMCR, PAM
        metrics = ['mcr', 'fmcr']
        metric_labels = ['MCR', 'FMCR']
        if 'pam_fraction' in df.columns:
            weekly_pam = df.groupby('week')['pam_fraction'].mean().reset_index()
            weekly = weekly.merge(weekly_pam, on='week', how='left')
            metrics.append('pam_fraction')
            metric_labels.append('PAM')

        heatmap_data = np.zeros((len(metrics), int(n_weeks)))
        for i, metric in enumerate(metrics):
            if metric in weekly.columns:
                vals = weekly[metric].values
                heatmap_data[i, :len(vals)] = vals

        y_labels = metric_labels
        x_labels = [f'W{w+1}' for w in range(int(n_weeks))]
        title = 'Weekly Fleet Performance (MCR/FMCR/PAM trends)'
        colorscale = [[0, '#e74c3c'], [0.5, '#f39c12'], [0.75, '#2ecc71'], [1, '#27ae60']]

    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data,
        x=x_labels,
        y=y_labels,
        colorscale=colorscale,
        zmin=0,
        zmax=1,
        showscale=True,
        colorbar=dict(title='Value'),
    ))

    fig.update_layout(
        title=title,
        xaxis_title='Week',
        yaxis_title='Metric' if total_events == 0 else 'Aircraft',
        template='plotly_dark',
        height=max(300, len(y_labels) * 40 + 100),
        margin=dict(l=70, r=20, t=60, b=40),
    )

    st.plotly_chart(fig, use_container_width=True)

