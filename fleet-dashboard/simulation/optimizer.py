"""
Autonomous Decision Support - AI Optimizer

Uses a stochastic hill climbing algorithm to mathematically find the
optimal minimum staffing levels (O-level, I-level, Depot) that satisfy
a commander-provided target Mission Capable Rate (MCR) while minimizing cost.
"""

import numpy as np
import pandas as pd
from simulation.engine import run_single

# Arbitrary annual cost per technician / slot
COSTS = {
    'o_techs': 100_000,
    'i_techs': 150_000,
    'd_techs': 250_000
}

# Search space bounds
BOUNDS = {
    'o_techs': (2, 24),
    'i_techs': (1, 12),
    'd_techs': (1, 12)
}

def evaluate_config(config, sim_params):
    """
    Run the simulation for a given staffing configuration and return MCR.
    """
    o_techs, i_techs, d_techs = [int(x) for x in config]
    
    # Run a fast, deterministic single run to evaluate
    result = run_single(
        o_techs=o_techs,
        i_techs=i_techs,
        d_techs=d_techs,
        **sim_params
    )
    return result['mcr']


def calculate_cost(config):
    """Calculate the total annual cost of a configuration."""
    o, i, d = config
    return (o * COSTS['o_techs']) + (i * COSTS['i_techs']) + (d * COSTS['d_techs'])


def optimize_staffing(target_mcr, sim_params, max_iterations=30, progress_callback=None):
    """
    Finds the lowest cost configuration that meets the target MCR
    using a Stochastic Hill Climbing Search.
    
    Parameters
    ----------
    target_mcr : float
        The required Mission Capable Rate (0.0 to 1.0).
    sim_params : dict
        Context parameters for the simulation (fleet_size, days, etc.)
    max_iterations : int
        Maximum steps to search. Minimum viable for dashboard speed.
    progress_callback : callable
        Function to update Streamlit progress bar.
        
    Returns
    -------
    dict
        Optimal configuration and history.
    """
    # Start at the maximum configuration to ensure we hit the target initially
    current_config = np.array([BOUNDS['o_techs'][1], BOUNDS['i_techs'][1], BOUNDS['d_techs'][1]])
    current_mcr = evaluate_config(current_config, sim_params)
    current_cost = calculate_cost(current_config)
    
    best_config = current_config.copy()
    best_cost = current_cost
    best_mcr = current_mcr
    
    history = [{
        'iter': 0,
        'o_techs': current_config[0],
        'i_techs': current_config[1],
        'd_techs': current_config[2],
        'cost': current_cost,
        'mcr': current_mcr,
        'valid': current_mcr >= target_mcr
    }]
    
    # If even max configuration can't hit target, return it anyway
    if current_mcr < target_mcr:
        return {
            'success': False,
            'reason': 'Target MCR unreachable even at maximum capacity.',
            'best_config': best_config.tolist(),
            'best_cost': best_cost,
            'best_mcr': best_mcr,
            'history': pd.DataFrame(history)
        }
        
    for i in range(1, max_iterations + 1):
        if progress_callback:
            progress_callback(i, max_iterations)
            
        # Generate a candidate by randomly subtracting 1 from one of the resource pools
        candidate = current_config.copy()
        
        # Pick a random resource to decrease
        idx_to_decrease = np.random.randint(0, 3)
        candidate[idx_to_decrease] -= 1
        
        # Enforce minimum bounds
        candidate[0] = max(candidate[0], BOUNDS['o_techs'][0])
        candidate[1] = max(candidate[1], BOUNDS['i_techs'][0])
        candidate[2] = max(candidate[2], BOUNDS['d_techs'][0])
        
        # If candidate is identical to current (hit lower bounds), pick a different one next time
        if np.array_equal(candidate, current_config):
            continue
            
        candidate_mcr = evaluate_config(candidate, sim_params)
        candidate_cost = calculate_cost(candidate)
        
        valid = candidate_mcr >= target_mcr
        
        history.append({
            'iter': i,
            'o_techs': candidate[0],
            'i_techs': candidate[1],
            'd_techs': candidate[2],
            'cost': candidate_cost,
            'mcr': candidate_mcr,
            'valid': valid
        })
        
        # If candidate meets MCR target and is cheaper (which it will be if we just subtracted hardware)
        # Or if we just maintain the target MCR with less resources
        if valid:
            current_config = candidate
            current_mcr = candidate_mcr
            current_cost = candidate_cost
            
            if current_cost < best_cost:
                best_config = current_config.copy()
                best_cost = current_cost
                best_mcr = current_mcr
        else:
            # We stepped too far down, MCR dropped below target.
            # Try to swap resources - subtract from one, add to another
            candidate = current_config.copy()
            sub_idx = np.random.randint(0, 3)
            add_idx = (sub_idx + np.random.randint(1, 3)) % 3
            
            candidate[sub_idx] -= 1
            candidate[add_idx] += 1
            
            # Enforce bounds
            candidate[0] = np.clip(candidate[0], BOUNDS['o_techs'][0], BOUNDS['o_techs'][1])
            candidate[1] = np.clip(candidate[1], BOUNDS['i_techs'][0], BOUNDS['i_techs'][1])
            candidate[2] = np.clip(candidate[2], BOUNDS['d_techs'][0], BOUNDS['d_techs'][1])
            
            if not np.array_equal(candidate, current_config):
                c_mcr = evaluate_config(candidate, sim_params)
                c_cost = calculate_cost(candidate)
                
                if c_mcr >= target_mcr and c_cost < current_cost:
                    current_config = candidate
                    current_mcr = c_mcr
                    current_cost = c_cost
                    
                    if current_cost < best_cost:
                        best_config = current_config.copy()
                        best_cost = current_cost
                        best_mcr = current_mcr
    
    return {
        'success': True,
        'best_config': best_config.tolist(),
        'best_cost': best_cost,
        'best_mcr': best_mcr,
        'history': pd.DataFrame(history)
    }
