"""Distribution functions for the dashboard simulation."""

import numpy as np
from scipy.special import gamma as gamma_func


def weibull_rvs(beta, eta, rng):
    """Weibull random variate using inverse CDF."""
    return eta * (-np.log(rng.uniform())) ** (1.0 / beta)


def lognormal_rvs(mu, sigma, rng):
    """Lognormal random variate."""
    return float(rng.lognormal(mu, sigma))


def normal_rvs(mean, std, rng):
    """Normal random variate."""
    return float(rng.normal(mean, std))


def poisson_interval(mean_hours, rng):
    """Exponential inter-arrival time."""
    return float(rng.exponential(mean_hours))


def weibull_mean(beta, eta):
    """Analytical Weibull mean."""
    return eta * gamma_func(1.0 + 1.0 / beta)
