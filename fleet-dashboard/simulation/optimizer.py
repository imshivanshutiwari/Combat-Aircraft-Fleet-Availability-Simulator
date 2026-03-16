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


def calculate_fitness(config, target_mcr, sim_params):
    """
    Calculate fitness: Inverse of cost, with high penalty if MCR < target.
    """
    mcr = evaluate_config(config, sim_params)
    cost = calculate_cost(config)
    
    # Massive penalty for failing to meet the mission target
    penalty = 0
    if mcr < target_mcr:
        # Penalty proportional to the shortfall
        penalty = (target_mcr - mcr) * 10_000_000 
        
    # We want to minimize cost + penalty, so fitness is the inverse (or negative)
    return -(cost + penalty), mcr, cost

def optimize_staffing(target_mcr, sim_params, max_iterations=20, progress_callback=None):
    """
    Finds the absolute global optimum configuration using an Evolutionary Genetic Algorithm.
    
    Parameters
    ----------
    max_iterations : int
        Now represents the number of Generations.
    """
    pop_size = 12 # Small pop for dashboard speed
    generations = max_iterations
    
    # 1. Initialize random population within bounds
    population = []
    for _ in range(pop_size):
        ind = [
            np.random.randint(BOUNDS['o_techs'][0], BOUNDS['o_techs'][1] + 1),
            np.random.randint(BOUNDS['i_techs'][0], BOUNDS['i_techs'][1] + 1),
            np.random.randint(BOUNDS['d_techs'][0], BOUNDS['d_techs'][1] + 1)
        ]
        population.append(np.array(ind))
        
    best_ind = None
    best_fitness = -np.inf
    history = []
    
    for gen in range(generations):
        if progress_callback:
            progress_callback(gen, generations)
            
        # 2. Evaluate fitness
        fitness_data = [calculate_fitness(ind, target_mcr, sim_params) for ind in population]
        fitnesses = [f[0] for f in fitness_data]
        
        # Track best
        current_best_idx = np.argmax(fitnesses)
        if fitnesses[current_best_idx] > best_fitness:
            best_fitness = fitnesses[current_best_idx]
            best_ind = population[current_best_idx].copy()
            
        # Log generation stats
        history.append({
            'iter': gen,
            'o_techs': population[current_best_idx][0],
            'i_techs': population[current_best_idx][1],
            'd_techs': population[current_best_idx][2],
            'cost': fitness_data[current_best_idx][2],
            'mcr': fitness_data[current_best_idx][1],
            'valid': fitness_data[current_best_idx][1] >= target_mcr
        })
        
        # 3. Selection (Tournament)
        new_population = []
        for _ in range(pop_size):
            # Pick 3, best one wins
            candidates = np.random.choice(len(population), 3, replace=False)
            winner = population[candidates[np.argmax([fitnesses[c] for c in candidates])]]
            new_population.append(winner.copy())
            
        # 4. Crossover (Single Point)
        for i in range(0, pop_size, 2):
            if i+1 < pop_size and np.random.rand() < 0.7:
                cp = np.random.randint(1, 3) # crossover point
                new_population[i][cp:], new_population[i+1][cp:] = \
                    new_population[i+1][cp:].copy(), new_population[i][cp:].copy()
                    
        # 5. Mutation
        for i in range(pop_size):
            if np.random.rand() < 0.2:
                idx = np.random.randint(0, 3)
                key = ['o_techs', 'i_techs', 'd_techs'][idx]
                new_population[i][idx] = np.random.randint(BOUNDS[key][0], BOUNDS[key][1] + 1)
                
        population = new_population

    # Final evaluation of the best found
    final_f, final_mcr, final_cost = calculate_fitness(best_ind, target_mcr, sim_params)
    
    return {
        'success': final_mcr >= target_mcr,
        'best_config': best_ind.tolist(),
        'best_cost': final_cost,
        'best_mcr': final_mcr,
        'history': pd.DataFrame(history)
    }
