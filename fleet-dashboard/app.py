"""
Military Ops Center Dashboard — Streamlit Application.

Full-featured fleet readiness dashboard with 6 tab views:
1. FLEET STATUS — KPI cards, aircraft matrix, maintenance pipeline
2. TIME SERIES — Animated fleet timeline
3. SENSITIVITY — Sobol parameter sensitivity analysis
4. SURGE ANALYSIS — Surge impact assessment
5. RESEARCH — Technician ratio research study
6. REPORT & EXPORT — Executive summary and data downloads
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

# Must be first Streamlit call
st.set_page_config(
    page_title="FLEET OPS CENTER — Combat Aircraft Readiness",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject military CSS
from styles.military_theme import inject_military_css
st.markdown(f'<style>{inject_military_css()}</style>', unsafe_allow_html=True)

# Imports
from simulation.engine import run_single
from simulation.kpi_calculator import compute_confidence_interval
from utils.cache_manager import cached_single_run, cached_monte_carlo

# ── SIDEBAR ──────────────────────────────────────────────────────────
st.sidebar.markdown("""
<div class="ops-title">FLEET OPS CENTER</div>
<div class="ops-subtitle">COMBAT AIRCRAFT READINESS</div>
<hr class="ops-divider">
""", unsafe_allow_html=True)

st.sidebar.markdown("#### SIMULATION PARAMETERS")

use_real_data = st.sidebar.toggle("NASA C-MAPSS Data Params", value=False)
use_ai_predictions = st.sidebar.toggle("AI Predictive Engine (ML)", value=False)
fleet_size = st.sidebar.slider("Fleet Size", 4, 24, 12, 2)
sim_days = st.sidebar.slider("Simulation Days", 90, 365, 180)
sortie_interval = st.sidebar.slider("Sortie Interval (hrs)", 18, 72, 48)

st.sidebar.markdown("#### MAINTENANCE ESTABLISHMENT")
o_techs = st.sidebar.slider("O-Level Technicians", 2, 16, 8)
i_techs = st.sidebar.slider("I-Level Technicians", 1, 8, 4)
d_techs = st.sidebar.slider("Depot Slots", 1, 10, 6)

st.sidebar.markdown("#### SURGE CONFIGURATION")
enable_surge = st.sidebar.toggle("Enable Surge", value=False)
if enable_surge:
    surge_start_day = st.sidebar.slider("Surge Start (Day)", 30, 300, 60)
    surge_duration_h = st.sidebar.slider("Surge Duration (Hours)", 24, 168, 72)
else:
    surge_start_day = None
    surge_duration_h = None

st.sidebar.markdown("#### MONTE CARLO")
mc_reps = st.sidebar.slider("Replications", 10, 200, 50, 10)
random_seed = st.sidebar.number_input("Random Seed", 1, 9999, 42)

# ── PYGAME LIVE LINK (ZMQ) ──────────────────────────────────────────
from utils.zmq_bridge import CommandPublisher

if 'zmq_pub' not in st.session_state:
    st.session_state['zmq_pub'] = CommandPublisher()

def send_bridge_command(cmd_type):
    st.session_state['zmq_pub'].send_command(cmd_type)

st.sidebar.markdown("#### PYGAME LIVE LINK (ZMQ SOCKET)")
st.sidebar.caption("Low-latency socket bridge active.")
c1, c2 = st.sidebar.columns(2)
if c1.button("⚡ SURGE", use_container_width=True):
    send_bridge_command("SURGE")
    st.sidebar.success("ZMQ: Surge sent!", icon="⚡")
if c2.button("⏸ PAUSE", use_container_width=True):
    send_bridge_command("PAUSE")
    st.sidebar.success("ZMQ: Pause sent!", icon="⏸")

st.sidebar.markdown("---")

# ── RUN SIMULATION ──────────────────────────────────────────────────
run_button = st.sidebar.button("▶ EXECUTE SIMULATION", type="primary",
                               use_container_width=True)

if run_button:
    st.cache_data.clear()

# Run single simulation
with st.spinner("Running simulation..."):
    result = cached_single_run(
        fleet_size=fleet_size,
        o_techs=o_techs, i_techs=i_techs, d_techs=d_techs,
        sortie_interval=sortie_interval,
        sim_days=sim_days,
        surge_start=surge_start_day,
        surge_dur=surge_duration_h,
        seed=random_seed,
        use_real_data=use_real_data,
        use_ai_predictions=use_ai_predictions,
    )

# Run Monte Carlo
mc_df = None
mc_kpi_dfs = None
if run_button or 'mc_df' in st.session_state:
    if run_button:
        with st.spinner(f"Monte Carlo: {mc_reps} replications..."):
            mc_df, mc_kpi_dfs = cached_monte_carlo(
                n_reps=mc_reps,
                fleet_size=fleet_size,
                o_techs=o_techs, i_techs=i_techs, d_techs=d_techs,
                sortie_interval=sortie_interval,
                sim_days=sim_days,
                surge_start=surge_start_day,
                surge_dur=surge_duration_h,
                seed=random_seed,
                use_real_data=use_real_data,
                use_ai_predictions=use_ai_predictions,
            )
            st.session_state['mc_df'] = mc_df
            st.session_state['mc_kpi_dfs'] = mc_kpi_dfs
    else:
        mc_df = st.session_state.get('mc_df')
        mc_kpi_dfs = st.session_state.get('mc_kpi_dfs')

# ── TOP KPI STRIP ──────────────────────────────────────────────────
from components.kpi_cards import render_kpi_strip

mcr_ci_hw = 0.0
fmcr_ci_hw = 0.0
if mc_df is not None and len(mc_df) > 0:
    _, _, _, mcr_ci_hw = compute_confidence_interval(mc_df['mcr'])
    _, _, _, fmcr_ci_hw = compute_confidence_interval(mc_df['fmcr'])

# Compute fleet summary from result
kpi_df = result['kpi_df']
if len(kpi_df) > 0:
    last = kpi_df.iloc[-1]
    fleet_summary = {
        'fmc': int(last.get('fmc', 0)),
        'pmc': int(last.get('pmc', 0)),
        'nmc_m': int(last.get('nmc_m', 0)),
        'nmc_p': int(last.get('nmc_p', 0)),
        'nmc_d': int(last.get('nmc_d', 0)),
    }
else:
    fleet_summary = {'fmc': fleet_size, 'pmc': 0, 'nmc_m': 0, 'nmc_p': 0, 'nmc_d': 0}

render_kpi_strip(result['mcr'], result['fmcr'],
                 mcr_ci_hw, fmcr_ci_hw, fleet_summary)

# ── TABS ────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "FLEET STATUS", "TIME SERIES", "SENSITIVITY",
    "SURGE ANALYSIS", "RESEARCH", "REAL DATA", "AI OPTIMIZATION", "REPORT & EXPORT",
])

# ── TAB 1: FLEET STATUS ────────────────────────────────────────────
with tab1:
    from components.fleet_status_matrix import (
        render_fleet_matrix, render_maintenance_pipeline, render_parts_status,
    )
    from components.gauge_charts import create_gauge_chart

    # Gauge row
    gc1, gc2, gc3 = st.columns(3)
    with gc1:
        fig = create_gauge_chart(result['mcr'] * 100, 'MCR')
        st.plotly_chart(fig, use_container_width=True)
    with gc2:
        fig = create_gauge_chart(result['fmcr'] * 100, 'FMCR')
        st.plotly_chart(fig, use_container_width=True)
    with gc3:
        tempo = result['total_sorties'] / max(1, sim_days)
        fig = create_gauge_chart(tempo, 'DAILY TEMPO',
                                 0, 30, 15, 8)
        st.plotly_chart(fig, use_container_width=True)

    # Fleet matrix using serialized fleet_data
    class _FleetProxy:
        """Lightweight proxy for fleet aircraft data."""
        def __init__(self, data):
            self.id = data['id']
            self.status = data['status']
            self.hours = data['hours']
            self.sorties = data['sorties']
            self.subs = {}
            for n, s in data['subs'].items():
                proxy_sub = type('Sub', (), s)()
                self.subs[n] = proxy_sub

    fleet_proxies = [_FleetProxy(fd) for fd in result['fleet_data']]
    render_fleet_matrix(fleet_proxies)

    st.markdown("---")
    render_maintenance_pipeline(result)
    st.markdown("---")
    render_parts_status(result)

# ── TAB 2: TIME SERIES ─────────────────────────────────────────────
with tab2:
    from components.animated_timeline import render_fleet_timeline
    render_fleet_timeline(result['kpi_df'],
                          surge_start=surge_start_day,
                          surge_dur=surge_duration_h)

    # Inventory over time
    stock_df = result.get('stock_df')
    if stock_df is not None and len(stock_df) > 0:
        import plotly.graph_objects as go
        from components.gauge_charts import get_dark_template
        stock_df_plot = stock_df.iloc[::6].copy()
        stock_df_plot['day'] = stock_df_plot['time'] / 24.0

        fig = go.Figure()
        colors = {'engine': '#FF3B3B', 'avionics': '#FFB800',
                  'hydraulics': '#00FF88', 'airframe': '#2A5080'}
        for part, color in colors.items():
            if part in stock_df_plot.columns:
                fig.add_trace(go.Scatter(
                    x=stock_df_plot['day'], y=stock_df_plot[part],
                    mode='lines', name=part.upper(),
                    line=dict(color=color, width=2),
                ))
        fig.update_layout(
            **get_dark_template(),
            title='SPARE PARTS INVENTORY — TIME SERIES',
            xaxis_title='DAY', yaxis_title='STOCK LEVEL',
            height=350,
        )
        st.plotly_chart(fig, use_container_width=True)

    # Queue lengths over time
    queue_df = result.get('queue_df')
    if queue_df is not None and len(queue_df) > 0:
        import plotly.graph_objects as go
        from components.gauge_charts import get_dark_template
        q_df = queue_df.iloc[::6].copy()
        q_df['day'] = q_df['time'] / 24.0

        fig = go.Figure()
        for col, color, name in [
            ('o_queue', '#2060A0', 'O-Level'),
            ('i_queue', '#A06020', 'I-Level'),
            ('d_queue', '#A02020', 'Depot'),
        ]:
            if col in q_df.columns:
                fig.add_trace(go.Scatter(
                    x=q_df['day'], y=q_df[col],
                    mode='lines', name=name,
                    line=dict(color=color, width=2),
                ))
        fig.update_layout(
            **get_dark_template(),
            title='MAINTENANCE QUEUE LENGTHS — TIME SERIES',
            xaxis_title='DAY', yaxis_title='AIRCRAFT IN QUEUE',
            height=350,
        )
        st.plotly_chart(fig, use_container_width=True)

# ── TAB 3: SENSITIVITY ─────────────────────────────────────────────
with tab3:
    from simulation.sensitivity_runner import run_sensitivity
    from components.sensitivity_charts import (
        render_sensitivity_bar, render_interaction_heatmap,
    )

    if st.button("▶ RUN SENSITIVITY ANALYSIS", key="sens_btn"):
        with st.spinner("Running Sobol sensitivity analysis..."):
            sens_data = run_sensitivity(n_samples=32, sim_days=sim_days)
            st.session_state['sens_data'] = sens_data

    if 'sens_data' in st.session_state:
        render_sensitivity_bar(st.session_state['sens_data'])
        render_interaction_heatmap(st.session_state['sens_data'])

# ── TAB 4: SURGE ANALYSIS ──────────────────────────────────────────
with tab4:
    from components.surge_charts import render_surge_analysis

    if enable_surge and mc_kpi_dfs is not None:
        # Build result dicts from kpi_dfs
        mc_results_for_surge = [{'kpi_df': df} for df in mc_kpi_dfs]
        render_surge_analysis(mc_results_for_surge,
                              surge_start_day, surge_duration_h)
    else:
        st.markdown("""
        <div class="military-intel">
            <h4>SURGE ANALYSIS</h4>
            <p>Enable "Surge" in the sidebar and run the simulation to see
            surge impact assessment with MCR degradation, recovery curves,
            and 95% confidence intervals.</p>
        </div>
        """, unsafe_allow_html=True)

# ── TAB 5: RESEARCH ────────────────────────────────────────────────
with tab5:
    from components.research_charts import (
        render_research_heatmap, render_threshold_curve, render_key_finding,
    )
    from simulation.research_analysis import (
        run_technician_sweep, find_minimum_viable_ratio, get_key_finding,
    )

    st.markdown("""
    <div class="military-intel">
        <h4>RESEARCH QUESTION</h4>
        <p>What is the <strong>minimum viable technician-to-aircraft ratio</strong>
        that maintains ≥ 75% Mission Capable Rate during surge operations?</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("▶ RUN RESEARCH STUDY", key="research_btn"):
        progress = st.progress(0)
        status = st.empty()

        def update_progress(done, total):
            progress.progress(min(1.0, done / total))
            status.text(f"Completed {done}/{total} configurations...")

        with st.spinner("Running technician ratio sweep..."):
            research_df = run_technician_sweep(progress_fn=update_progress)
            st.session_state['research_df'] = research_df
        progress.empty()
        status.empty()

    if 'research_df' in st.session_state:
        research_df = st.session_state['research_df']
        render_research_heatmap(research_df)
        min_ratios = find_minimum_viable_ratio(research_df)
        render_threshold_curve(min_ratios)
        finding = get_key_finding(research_df, fleet_size)
        render_key_finding(finding)

# ── TAB 6: REAL DATA ───────────────────────────────────────────────
with tab6:
    from components.real_data_charts import render_gao_benchmarks, render_cmapss_sensors
    render_gao_benchmarks(result['mcr'], result['fmcr'])
    st.markdown("---")
    # Let user select engine unit to view
    unit_id = st.slider("Select C-MAPSS Engine Unit for Sensor Telemetry", 1, 100, 1)
    render_cmapss_sensors(unit_id=unit_id)

# ── TAB 7: AI OPTIMIZATION ─────────────────────────────────────────
with tab7:
    from components.optimization_view import render_optimization_tab
    
    # We pass the same simulation parameters currently used in the dashboard
    # This ensures the solver optimizes against the current scenario
    sim_params = {
        'fleet_size': fleet_size,
        'sortie_interval': sortie_interval,
        'sim_days': sim_days,
        'surge_start': surge_start_day,
        'surge_dur': surge_duration_h,
        'seed': random_seed,
        'use_real_data': use_real_data,
        'use_ai_predictions': use_ai_predictions,
    }
    render_optimization_tab(sim_params)

# ── TAB 8: REPORT & EXPORT ─────────────────────────────────────────
with tab8:
    from utils.report_generator import render_executive_summary
    from utils.export_handler import render_export_panel

    render_executive_summary(result, mc_df, fleet_size)
    st.markdown("---")
    render_export_panel(result, mc_df)

# ── FOOTER ──────────────────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="color:#7A9CC0;font-size:0.7rem;text-align:center;">
    FLEET OPS CENTER v2.0<br>
    Modelling & Simulation Project<br>
    Combat Aircraft Fleet Availability
</div>
""", unsafe_allow_html=True)
