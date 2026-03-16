"""Streamlit cache manager for simulation results."""

import streamlit as st
from simulation.engine import run_single, run_monte_carlo


@st.cache_data(show_spinner=False)
def cached_single_run(fleet_size, o_techs, i_techs, d_techs,
                      sortie_interval, sim_days, surge_start,
                      surge_dur, seed, use_real_data=False, use_ai_predictions=False):
    """
    Cached single simulation run.

    Returns serializable results (strips SimPy objects).
    """
    r = run_single(
        fleet_size=fleet_size, o_techs=o_techs, i_techs=i_techs,
        d_techs=d_techs, sortie_interval=sortie_interval,
        sim_days=sim_days, surge_start=surge_start,
        surge_dur=surge_dur, seed=seed, use_real_data=use_real_data,
        use_ai_predictions=use_ai_predictions
    )
    # Strip non-serializable fleet objects — extract key data
    fleet_data = []
    for ac in r['fleet']:
        fleet_data.append({
            'id': ac.id,
            'status': ac.status,
            'hours': ac.hours,
            'sorties': ac.sorties,
            'subs': {n: {'health': s.health, 'hours': s.hours,
                         'failed': s.failed}
                     for n, s in ac.subs.items()},
            'events': ac.events,
        })

    return {
        'mcr': r['mcr'], 'fmcr': r['fmcr'], 'pam': r['pam'],
        'total_sorties': r['total_sorties'],
        'total_hours': r['total_hours'],
        'kpi_df': r['kpi_df'],
        'stock_df': r['stock_df'],
        'queue_df': r['queue_df'],
        'maint_log': r['maint_log'],
        'fleet_data': fleet_data,
        'fleet_size': r['fleet_size'],
    }


@st.cache_data(show_spinner=False)
def cached_monte_carlo(n_reps, fleet_size, o_techs, i_techs, d_techs,
                       sortie_interval, sim_days, surge_start,
                       surge_dur, seed, use_real_data=False, use_ai_predictions=False):
    """Cached Monte Carlo runs. Returns summary DataFrame."""
    mc_df, all_results = run_monte_carlo(
        n_reps=n_reps,
        fleet_size=fleet_size, o_techs=o_techs, i_techs=i_techs,
        d_techs=d_techs, sortie_interval=sortie_interval,
        sim_days=sim_days, surge_start=surge_start,
        surge_dur=surge_dur, seed=seed, use_real_data=use_real_data,
        use_ai_predictions=use_ai_predictions
    )
    # Only return serializable data
    kpi_dfs = [r['kpi_df'] for r in all_results]
    return mc_df, kpi_dfs
