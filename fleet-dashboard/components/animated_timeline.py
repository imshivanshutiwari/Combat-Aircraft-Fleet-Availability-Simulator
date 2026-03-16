"""Animated fleet timeline chart."""

import plotly.graph_objects as go
from components.gauge_charts import get_dark_template


def render_fleet_timeline(kpi_df, surge_start=None, surge_dur=None):
    """
    Render stacked area chart of fleet status over time.

    Parameters
    ----------
    kpi_df : pd.DataFrame
        KPI time series with fmc, pmc, nmc_m, nmc_p, nmc_d columns.
    surge_start : int or None
        Surge start day.
    surge_dur : float or None
        Surge duration hours.
    """
    import streamlit as st

    if kpi_df is None or len(kpi_df) == 0:
        st.info("No data available for timeline.")
        return

    # Downsample for performance (every 6 hours)
    df = kpi_df.iloc[::6].copy()
    df['day'] = df['time'] / 24.0

    fig = go.Figure()

    # Stacked areas (order reversed for correct stacking)
    categories = [
        ('nmc_d', 'NMC-Depot', '#660022'),
        ('nmc_p', 'NMC-Parts', '#FF3B3B'),
        ('nmc_m', 'NMC-Maint', '#FF6600'),
        ('pmc', 'PMC', '#FFB800'),
        ('fmc', 'FMC', '#00FF88'),
    ]

    for col, name, color in categories:
        if col in df.columns:
            fig.add_trace(go.Scatter(
                x=df['day'], y=df[col],
                mode='lines', name=name,
                fill='tonexty' if col != 'nmc_d' else 'tozeroy',
                line={'width': 0, 'color': color},
                fillcolor=color,
            ))

    # Surge region
    if surge_start is not None and surge_dur is not None:
        surge_end_day = surge_start + surge_dur / 24
        fig.add_vrect(
            x0=surge_start, x1=surge_end_day,
            fillcolor='rgba(255,0,0,0.1)',
            line_width=0,
        )
        fig.add_vline(x=surge_start, line_dash='dash',
                      line_color='#FF3B3B', line_width=1,
                      annotation_text='SURGE START',
                      annotation_font={'color': '#FF3B3B', 'size': 10})
        fig.add_vline(x=surge_end_day, line_dash='dash',
                      line_color='#FF3B3B', line_width=1,
                      annotation_text='SURGE END',
                      annotation_font={'color': '#FF3B3B', 'size': 10})

    dark = get_dark_template()
    dark['legend'] = {**dark.get('legend', {}), 'orientation': 'h', 'y': -0.15}
    fig.update_layout(
        **dark,
        title='FLEET STATUS COMPOSITION — TIME SERIES',
        xaxis_title='SIMULATED DAY',
        yaxis_title='NUMBER OF AIRCRAFT',
        height=400,
        showlegend=True,
    )

    st.plotly_chart(fig, use_container_width=True)
