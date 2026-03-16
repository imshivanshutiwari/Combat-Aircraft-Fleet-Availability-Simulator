"""Real Data Integration Charts — GAO Benchmarks and NASA C-MAPSS."""

import os
import json
import plotly.graph_objects as go
import streamlit as st
from components.gauge_charts import get_dark_template
from data.cmapss_loader import get_sensor_data, DEGRADING_SENSORS


def render_gao_benchmarks(sim_mcr, sim_fmcr):
    """
    Render a horizontal bar chart comparing simulated fleet MCR
    to real-world GAO benchmarks for various aircraft platforms.
    """
    benchmarks_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '..', 'data', 'gao_benchmarks.json'
    )
    
    if not os.path.exists(benchmarks_path):
        st.warning("GAO benchmarks data not found. Run gao_extractor.py first.")
        return
        
    with open(benchmarks_path, 'r') as f:
        benchmarks = json.load(f)
        
    st.markdown("#### REAL-WORLD BENCHMARK COMPARISON (GAO)")
    
    # Sort benchmarks by actual MCR descending
    platforms = list(benchmarks.keys())
    platforms.sort(key=lambda x: benchmarks[x]['actuals']['mcr'], reverse=True)
    
    names = ['CURRENT SIMULATION'] + platforms
    mcr_vals = [sim_mcr * 100] + [benchmarks[p]['actuals']['mcr'] for p in platforms]
    goals = [None] + [benchmarks[p]['goals']['mcr'] for p in platforms]
    
    # Highlight simulation row vs others
    colors = ['#00FF88'] + ['#2060A0' for _ in platforms]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=mcr_vals, y=names,
        orientation='h',
        marker_color=colors,
        name='Actual / Simulated MCR',
        text=[f"{v:.1f}%" for v in mcr_vals],
        textposition='auto',
    ))
    
    # Add goal markers where available
    for i, g in enumerate(goals):
        if g is not None:
            fig.add_trace(go.Scatter(
                x=[g], y=[names[i]],
                mode='markers',
                marker=dict(symbol='line-ns', size=30, color='#FFB800', line=dict(width=3)),
                name='GAO Goal' if i == 1 else None,
                showlegend=(i == 1),
            ))

    layout_args = get_dark_template()
    layout_args.setdefault('yaxis', {}).update({'autorange': 'reversed'})

    fig.update_layout(
        **layout_args,
        title='MISSION CAPABLE RATE: SIMULATION vs REAL MILITARY FLEETS',
        xaxis_title='MISSION CAPABLE RATE (%)',
        height=350 + len(names) * 30,
        barmode='overlay',
    )
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    
    st.plotly_chart(fig, use_container_width=True)


def render_cmapss_sensors(unit_id=1):
    """
    Render raw sensor signals for a selected C-MAPSS engine unit.
    """
    st.markdown("#### NASA C-MAPSS SENSOR TELEMETRY")
    try:
        unit_data = get_sensor_data('FD001', unit_id)
    except Exception as e:
        st.error(f"Failed to load C-MAPSS data: {e}")
        return
        
    if len(unit_data) == 0:
        st.warning(f"No data for Engine Unit {unit_id}.")
        return

    # Select few key sensors for visualization
    key_sensors = ['s2', 's3', 's4', 's11', 's15']
    sensor_names = {
        's2': 'LPC Outlet Temp (R)',
        's3': 'HPC Outlet Temp (R)',
        's4': 'LPT Outlet Temp (R)',
        's11': 'HPC Outlet Static Pressure (psia)',
        's15': 'Bypass Ratio',
    }
    
    fig = go.Figure()
    colors = ['#00FF88', '#FFB800', '#FF3B3B', '#2A5080', '#A06020']
    
    for idx, s in enumerate(key_sensors):
        if s in unit_data.columns:
            # Normalize to 0-1 for plotting on same axis
            series = unit_data[s]
            s_min = series.min()
            s_max = series.max()
            rng = s_max - s_min if s_max > s_min else 1.0
            norm_series = (series - s_min) / rng
            
            fig.add_trace(go.Scatter(
                x=unit_data['cycle'], y=norm_series,
                mode='lines', name=sensor_names.get(s, s),
                line=dict(color=colors[idx % len(colors)], width=2),
                opacity=0.8,
            ))
            
    # Add failure line
    failure_cycle = unit_data['cycle'].max()
    fig.add_vline(x=failure_cycle, line_width=2, line_dash="dash", line_color="#FF3B3B",
                  annotation_text="ENGINE FAILURE", annotation_font_color="#FF3B3B")

    fig.update_layout(
        **get_dark_template(),
        title=f'SENSOR DEGRADATION SIGNATURE (ENGINE UNIT {unit_id})',
        xaxis_title='OPERATIONAL CYCLES',
        yaxis_title='NORMALIZED SENSOR VALUE (0-1)',
        height=400,
    )
    
    st.plotly_chart(fig, use_container_width=True)

