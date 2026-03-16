"""
Dashboard component — Sensitivity analysis chart.

Runs Morris screening and displays parameter importance bar chart.
"""

import numpy as np
import plotly.graph_objects as go
import streamlit as st


def run_morris_screening(sim_class, n_trajectories=10):
    """
    Run Morris One-At-A-Time (OAT) screening on simulation parameters.

    Parameters
    ----------
    sim_class : class
        FleetSimulation class.
    n_trajectories : int
        Number of trajectories (reduced for dashboard speed).

    Returns
    -------
    dict
        Parameter names, mu_star values, sigma values.
    """
    # Parameter definitions
    params = {
        'engine_eta': (600, 1000),
        'avionics_eta': (400, 800),
        'hydraulics_eta': (800, 1600),
        'engine_reorder': (1, 4),
        'lead_time_mean': (7, 21),
        'o_level_techs': (4, 12),
        'i_level_techs': (2, 6),
        'sortie_interval': (36, 60),
    }

    param_names = list(params.keys())
    k = len(param_names)
    bounds = [params[p] for p in param_names]

    # Generate Morris trajectories
    rng = np.random.RandomState(42)
    all_effects = {p: [] for p in param_names}

    for traj in range(n_trajectories):
        # Base point (random in parameter space)
        base = np.array([rng.uniform(lo, hi) for lo, hi in bounds])
        delta = 0.5  # Step size as fraction of range

        # Evaluate base
        base_mcr = _evaluate_sim(sim_class, param_names, bounds, base)

        # One-at-a-time perturbations
        for i, pname in enumerate(param_names):
            perturbed = base.copy()
            step = delta * (bounds[i][1] - bounds[i][0])
            perturbed[i] = min(bounds[i][1], base[i] + step)
            pert_mcr = _evaluate_sim(sim_class, param_names, bounds, perturbed)
            effect = (pert_mcr - base_mcr) / delta
            all_effects[pname].append(effect)

    # Compute mu_star (mean of absolute effects) and sigma
    mu_star = {p: np.mean(np.abs(all_effects[p])) for p in param_names}
    sigma = {p: np.std(all_effects[p]) for p in param_names}

    return {
        'param_names': param_names,
        'mu_star': mu_star,
        'sigma': sigma,
    }


def _evaluate_sim(sim_class, param_names, bounds, values):
    """
    Evaluate simulation at a given parameter point.

    Parameters
    ----------
    sim_class : class
        FleetSimulation class.
    param_names : list
        Parameter names.
    bounds : list of tuple
        Parameter bounds.
    values : array
        Current parameter values.

    Returns
    -------
    float
        MCR value.
    """
    val_dict = {p: v for p, v in zip(param_names, values)}

    subsystem_params = {
        'engine': {'eta': val_dict.get('engine_eta', 800)},
        'avionics': {'eta': val_dict.get('avionics_eta', 600)},
        'hydraulics': {'eta': val_dict.get('hydraulics_eta', 1200)},
    }

    inventory_params = {
        'engine': {
            'reorder_point': int(val_dict.get('engine_reorder', 2)),
            'lead_time_mean_days': val_dict.get('lead_time_mean', 14),
        },
    }

    sim = sim_class(
        fleet_size=12,
        o_level_techs_day=int(val_dict.get('o_level_techs', 8)),
        i_level_techs_day=int(val_dict.get('i_level_techs', 4)),
        sortie_interval_hours=val_dict.get('sortie_interval', 48),
        subsystem_params=subsystem_params,
        inventory_params=inventory_params,
    )

    result = sim.run(simulation_days=90, random_seed=42)
    return result['mcr']


def render_sensitivity_chart(morris_results):
    """
    Render horizontal bar chart of Morris mu* values.

    Parameters
    ----------
    morris_results : dict
        Output from run_morris_screening().
    """
    params = morris_results['param_names']
    mu_star = morris_results['mu_star']

    # Sort by importance
    sorted_params = sorted(params, key=lambda p: mu_star[p])
    sorted_values = [mu_star[p] for p in sorted_params]

    fig = go.Figure(go.Bar(
        x=sorted_values,
        y=sorted_params,
        orientation='h',
        marker=dict(
            color=sorted_values,
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title='μ*'),
        ),
    ))

    fig.update_layout(
        title='Parameter Sensitivity (Morris μ* — Main Effects)',
        xaxis_title='μ* (Mean Absolute Elementary Effect)',
        template='plotly_dark',
        height=400,
        margin=dict(l=150, r=40, t=60, b=40),
    )

    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Parameters sorted by influence on MCR. Longer bar = more important."
    )
