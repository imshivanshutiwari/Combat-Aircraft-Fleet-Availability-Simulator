"""
Statistical distribution functions for the Fleet Live Simulation.

Provides Weibull, lognormal, normal, and Poisson variates using
inverse-CDF methods. All functions take a numpy RandomState object
to ensure zero global random state.
"""

import numpy as np
from scipy.special import gamma as gamma_func


def weibull_rvs(beta, eta, rng):
    """
    Generate one Weibull random variate using inverse CDF.

    Parameters
    ----------
    beta : float
        Shape parameter (> 0).
    eta : float
        Scale parameter in flight hours (> 0).
    rng : numpy.random.RandomState
        Seeded random state.

    Returns
    -------
    float
        Weibull random variate.
    """
    u = rng.uniform()
    return eta * (-np.log(u)) ** (1.0 / beta)


def lognormal_rvs(mu_log, sigma_log, rng):
    """
    Generate one lognormal random variate.

    Parameters
    ----------
    mu_log : float
        Mean of the underlying normal distribution (log-space).
    sigma_log : float
        Standard deviation of the underlying normal (log-space).
    rng : numpy.random.RandomState
        Seeded random state.

    Returns
    -------
    float
        Lognormal random variate (always positive).
    """
    return float(rng.lognormal(mu_log, sigma_log))


def normal_rvs(mean, std, rng):
    """
    Generate one Normal random variate.

    Parameters
    ----------
    mean : float
        Distribution mean.
    std : float
        Distribution standard deviation.
    rng : numpy.random.RandomState
        Seeded random state.

    Returns
    -------
    float
        Normal random variate.
    """
    return float(rng.normal(mean, std))


def poisson_interval(mean_hours, rng):
    """
    Generate one exponential inter-arrival time (Poisson process).

    Parameters
    ----------
    mean_hours : float
        Mean inter-arrival time in hours.
    rng : numpy.random.RandomState
        Seeded random state.

    Returns
    -------
    float
        Exponential random variate in hours (always positive).
    """
    return float(rng.exponential(mean_hours))


def weibull_mean(beta, eta):
    """
    Compute analytical mean of a Weibull distribution.

    Parameters
    ----------
    beta : float
        Shape parameter.
    eta : float
        Scale parameter.

    Returns
    -------
    float
        E[X] = eta * Gamma(1 + 1/beta).
    """
    return eta * gamma_func(1.0 + 1.0 / beta)
