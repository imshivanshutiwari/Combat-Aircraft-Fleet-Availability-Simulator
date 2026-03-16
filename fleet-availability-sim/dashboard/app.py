"""
Combat Aircraft Fleet Availability Simulator — Streamlit Dashboard.

Interactive analysis tool for defence operations research.
Provides simulation controls, live results, distribution analysis,
sensitivity analysis, and research findings.

Usage
-----
    streamlit run dashboard/app.py
"""

import sys
import os

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from scipy.stats import norm

from src.simulation import FleetSimulation, run_monte_carlo
from dashboard.components.kpi_cards import render_kpi_cards
from dashboard.components.fleet_status_chart import (
    render_fleet_status_chart, render_aircraft_heatmap
)
from dashboard.components.sensitivity_chart import (
    run_morris_screening, render_sensitivity_chart
)
from dashboard.components.surge_animator import (
    render_surge_timeline, render_queue_timeline
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Combat Aircraft Fleet Availability Simulator",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load custom CSS
css_path = os.path.join(os.path.dirname(__file__), 'assets', 'style.css')
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown("""
<div class="dashboard-header">
    <h1>✈️ Combat Aircraft Fleet Availability Simulator</h1>
    <p style="color: #a0a0a0; font-size: 1.1rem;">
        Interactive Analysis Tool — Defence Operations Research
    </p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar controls
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## ⚙️ Simulation Parameters")
    st.markdown("---")

    fleet_size = st.slider("Fleet Size", min_value=4, max_value=24,
                           value=12, step=2)
    o_level_techs = st.slider("Day Shift O-level Technicians",
                               min_value=2, max_value=16, value=8)
    i_level_techs = st.slider("Day Shift I-level Technicians",
                               min_value=1, max_value=8, value=4)
    sortie_interval = st.slider("Peacetime Sortie Interval (hours)",
                                 min_value=24, max_value=96, value=48)

    st.markdown("---")
    st.markdown("### 🔥 Surge Configuration")

    enable_surge = st.toggle("Enable Surge", value=False)

    surge_start_day = None
    surge_duration = None
    if enable_surge:
        surge_start_day = st.slider("Surge Start Day",
                                     min_value=30, max_value=150, value=60)
        surge_duration = st.slider("Surge Duration (hours)",
                                    min_value=24, max_value=168, value=72)

    st.markdown("---")
    st.markdown("### 📊 Simulation Settings")

    sim_days = st.selectbox("Simulation Duration (days)",
                            options=[90, 180, 365], index=1)
    n_replications = st.selectbox("Number of Replications",
                                   options=[10, 50, 100], index=1)
    random_seed = st.number_input("Random Seed", value=42, min_value=1)

    st.markdown("---")
    run_button = st.button("🚀 Run Simulation", use_container_width=True,
                           type="primary")


# ---------------------------------------------------------------------------
# Simulation execution
# ---------------------------------------------------------------------------
@st.cache_data(ttl=600, show_spinner=False)
def run_simulation_cached(fleet_size, o_techs, i_techs, sortie_int,
                          sim_days, seed, surge_start, surge_dur):
    """Run and cache a single simulation."""
    sim = FleetSimulation(
        fleet_size=fleet_size,
        o_level_techs_day=o_techs,
        i_level_techs_day=i_techs,
        sortie_interval_hours=sortie_int,
    )
    result = sim.run(
        simulation_days=sim_days,
        surge_start_day=surge_start,
        surge_duration_hours=surge_dur,
        random_seed=seed,
    )
    
    # Extract serializable maintenance events for the heatmap
    maintenance_events_by_aircraft = {
        ac.aircraft_id: ac.maintenance_events for ac in result['fleet']
    }
    
    # Strip out unserializable SimPy objects for Streamlit caching
    serial_result = {k: v for k, v in result.items() if k not in ['fleet', 'inventory', 'kpi_tracker']}
    serial_result['maintenance_events'] = maintenance_events_by_aircraft
    serial_result['fleet_size'] = len(result['fleet'])
    
    return serial_result


@st.cache_data(ttl=600, show_spinner=False)
def run_monte_carlo_cached(fleet_size, o_techs, i_techs, sortie_int,
                            sim_days, n_reps, seed, surge_start, surge_dur):
    """Run and cache Monte Carlo replications."""
    config = {
        'fleet_size': fleet_size,
        'o_level_techs_day': o_techs,
        'i_level_techs_day': i_techs,
        'sortie_interval_hours': sortie_int,
    }
    run_kwargs = {
        'simulation_days': sim_days,
        'random_seed': seed,
    }
    if surge_start is not None and surge_dur is not None:
        run_kwargs['surge_start_day'] = surge_start
        run_kwargs['surge_duration_hours'] = surge_dur

    return run_monte_carlo(config, n_reps, show_progress=False, **run_kwargs)


# ---------------------------------------------------------------------------
# Main panel — Tabs
# ---------------------------------------------------------------------------
if run_button or 'results' in st.session_state:
    if run_button:
        with st.spinner("🛩️ Running simulation..."):
            # Single run for timeline
            single_result = run_simulation_cached(
                fleet_size, o_level_techs, i_level_techs, sortie_interval,
                sim_days, random_seed, surge_start_day, surge_duration,
            )

            # Monte Carlo for CIs
            mc_df = run_monte_carlo_cached(
                fleet_size, o_level_techs, i_level_techs, sortie_interval,
                sim_days, n_replications, random_seed,
                surge_start_day, surge_duration,
            )

            st.session_state['results'] = single_result
            st.session_state['mc_df'] = mc_df
            st.session_state['params'] = {
                'fleet_size': fleet_size,
                'surge_start_day': surge_start_day,
                'surge_duration': surge_duration,
            }

    single_result = st.session_state.get('results')
    mc_df = st.session_state.get('mc_df')
    params = st.session_state.get('params', {})

    if single_result and mc_df is not None:
        tab1, tab2, tab3, tab4 = st.tabs([
            "📈 Live Results",
            "📊 Distribution Analysis",
            "🔬 Sensitivity Analysis",
            "📋 Research Findings",
        ])

        # ---- Tab 1: Live Results ----
        with tab1:
            # MCR confidence intervals
            mcr_mean = mc_df['mcr'].mean()
            mcr_std = mc_df['mcr'].std()
            mcr_ci = (
                mcr_mean - 1.96 * mcr_std / np.sqrt(len(mc_df)),
                mcr_mean + 1.96 * mcr_std / np.sqrt(len(mc_df)),
            )
            fmcr_mean = mc_df['fmcr'].mean()
            fmcr_std = mc_df['fmcr'].std()
            fmcr_ci = (
                fmcr_mean - 1.96 * fmcr_std / np.sqrt(len(mc_df)),
                fmcr_mean + 1.96 * fmcr_std / np.sqrt(len(mc_df)),
            )

            render_kpi_cards(
                mcr=mcr_mean,
                fmcr=fmcr_mean,
                pam_fraction=mc_df['pam_fraction'].mean(),
                mcr_ci=mcr_ci,
                fmcr_ci=fmcr_ci,
            )

            st.markdown("---")

            # Fleet status chart
            kpi_df = single_result['kpi_dataframe']
            render_fleet_status_chart(kpi_df)

            # Surge timeline if surge enabled
            if params.get('surge_start_day') is not None:
                render_surge_timeline(
                    kpi_df,
                    params['surge_start_day'],
                    params.get('surge_duration', 72),
                )

            # Aircraft heatmap
            render_aircraft_heatmap(
                kpi_df, 
                single_result.get('maintenance_events', {}),
                single_result.get('fleet_size', 12)
            )

        # ---- Tab 2: Distribution Analysis ----
        with tab2:
            col1, col2 = st.columns(2)

            with col1:
                # Histogram of MCR
                fig_hist = go.Figure()
                fig_hist.add_trace(go.Histogram(
                    x=mc_df['mcr'] * 100,
                    nbinsx=20,
                    marker_color='#3498db',
                    opacity=0.7,
                    name='MCR Distribution',
                ))
                # Normal fit overlay
                x_range = np.linspace(
                    mc_df['mcr'].min() * 100,
                    mc_df['mcr'].max() * 100, 100
                )
                fitted_pdf = norm.pdf(
                    x_range, mcr_mean * 100, mcr_std * 100
                )
                fig_hist.add_trace(go.Scatter(
                    x=x_range,
                    y=fitted_pdf * len(mc_df) * (mc_df['mcr'].max() - mc_df['mcr'].min()) * 100 / 20,
                    mode='lines',
                    name='Normal Fit',
                    line=dict(color='#e74c3c', width=2),
                ))
                fig_hist.update_layout(
                    title='MCR Distribution Across Replications',
                    xaxis_title='MCR (%)',
                    yaxis_title='Count',
                    template='plotly_dark',
                    height=400,
                )
                st.plotly_chart(fig_hist, use_container_width=True)

            with col2:
                # Box plots
                fig_box = go.Figure()
                fig_box.add_trace(go.Box(
                    y=mc_df['mcr'] * 100, name='MCR',
                    marker_color='#2ecc71',
                ))
                fig_box.add_trace(go.Box(
                    y=mc_df['fmcr'] * 100, name='FMCR',
                    marker_color='#3498db',
                ))
                fig_box.add_trace(go.Box(
                    y=mc_df['pam_fraction'] * 100, name='PAM',
                    marker_color='#e74c3c',
                ))
                fig_box.update_layout(
                    title='KPI Distributions',
                    yaxis_title='Percentage (%)',
                    template='plotly_dark',
                    height=400,
                )
                st.plotly_chart(fig_box, use_container_width=True)

            # Convergence plot
            running_means = mc_df['mcr'].expanding().mean() * 100
            running_std = mc_df['mcr'].expanding().std()
            n_values = np.arange(1, len(mc_df) + 1)
            ci_half = 1.96 * running_std * 100 / np.sqrt(n_values)

            fig_conv = go.Figure()
            fig_conv.add_trace(go.Scatter(
                x=n_values, y=running_means,
                name='Running Mean MCR',
                line=dict(color='#2980b9', width=2),
            ))
            fig_conv.add_trace(go.Scatter(
                x=n_values, y=running_means + ci_half,
                mode='lines', name='Upper 95% CI',
                line=dict(color='#2ecc71', width=1, dash='dash'),
            ))
            fig_conv.add_trace(go.Scatter(
                x=n_values, y=running_means - ci_half,
                mode='lines', name='Lower 95% CI',
                line=dict(color='#2ecc71', width=1, dash='dash'),
                fill='tonexty',
                fillcolor='rgba(46, 204, 113, 0.1)',
            ))
            fig_conv.update_layout(
                title='Convergence: CI Width vs. Number of Replications',
                xaxis_title='Number of Replications',
                yaxis_title='MCR (%)',
                template='plotly_dark',
                height=350,
            )
            st.plotly_chart(fig_conv, use_container_width=True)

        # ---- Tab 3: Sensitivity Analysis ----
        with tab3:
            st.markdown("### Morris Screening — Parameter Sensitivity")
            st.info("Running Morris screening with 10 trajectories... "
                    "This may take a moment.")

            @st.cache_data(ttl=600, show_spinner=False)
            def cached_morris():
                return run_morris_screening(FleetSimulation, n_trajectories=10)

            with st.spinner("Running sensitivity analysis..."):
                morris_results = cached_morris()

            render_sensitivity_chart(morris_results)

        # ---- Tab 4: Research Findings ----
        with tab4:
            st.markdown("### 🔬 Research: Minimum Technician-to-Aircraft Ratio")

            st.markdown("""
            <div class="key-finding">
                <h4>Research Question</h4>
                <p>What is the minimum technician-to-aircraft ratio that keeps
                MCR above 75% under surge conditions, and how does this
                threshold vary with fleet size?</p>
            </div>
            """, unsafe_allow_html=True)

            st.info("To generate full research results, run: "
                    "`python generate_report.py`")

            # Check for existing research report
            report_path = os.path.join(PROJECT_ROOT, 'docs',
                                        'research_report.pdf')
            if os.path.exists(report_path):
                st.success("Research report available for download!")
                with open(report_path, 'rb') as f:
                    st.download_button(
                        label="📥 Download Research Report (PDF)",
                        data=f,
                        file_name="research_report.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )

            # Quick heatmap with reduced parameters
            st.markdown("---")
            st.markdown("#### Quick Technician Ratio Analysis")
            st.caption("Reduced parameter set for interactive exploration. "
                       "Full analysis requires `generate_report.py`.")

            if st.button("🔄 Run Quick Analysis", key="quick_research"):
                with st.spinner("Running quick technician sweep..."):
                    from src.research_question import ResearchAnalysis
                    analysis = ResearchAnalysis(
                        fleet_sizes=[8, 12, 16],
                        tech_ratios=[0.4, 0.8, 1.0, 1.2],
                        replications_per_config=10,
                    )
                    results_df = analysis.run_technician_sweep()
                    min_ratios = analysis.find_minimum_viable_ratio()

                    # Display results table
                    st.dataframe(results_df[[
                        'fleet_size', 'tech_ratio', 'mean_surge_MCR',
                        'std_surge_MCR', 'p75_threshold_met'
                    ]].style.format({
                        'mean_surge_MCR': '{:.1%}',
                        'std_surge_MCR': '{:.1%}',
                    }), use_container_width=True)

                    # Key finding
                    if 12 in min_ratios and min_ratios[12] is not None:
                        st.markdown(f"""
                        <div class="key-finding">
                            <h4>📌 Key Finding</h4>
                            <p>For a 12-aircraft fleet, the minimum
                            technician-to-aircraft ratio maintaining MCR above
                            75% during 72-hour surge operations is
                            <strong>{min_ratios[12]:.1f}</strong>, implying a
                            minimum of
                            <strong>{max(2, int(round(min_ratios[12]*12)))}</strong>
                            day-shift O-level technicians.</p>
                        </div>
                        """, unsafe_allow_html=True)

else:
    # No results yet
    st.markdown("""
    <div style="text-align: center; padding: 3rem 0;">
        <h2>👈 Configure parameters and press Run Simulation</h2>
        <p style="color: #a0a0a0; font-size: 1.1rem;">
            Adjust fleet size, staffing levels, and surge parameters
            in the sidebar, then click the Run button.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Show benchmark data
    st.markdown("### 📊 Reference Benchmarks")
    benchmark_df = pd.DataFrame({
        'Aircraft': ['F-16', 'F-35A', 'F/A-18', 'MiG-21', 'Mirage 2000',
                      'Su-30MKI'],
        'Source': ['GAO-21-279', 'GAO-21-279', 'GAO-21-279',
                   'CAG India 2021', 'CAG India 2021', 'CAG India 2021'],
        'MCR (%)': [71.9, 54.6, 62.1, 75.0, 78.0, 72.0],
    })
    st.dataframe(benchmark_df, use_container_width=True, hide_index=True)
