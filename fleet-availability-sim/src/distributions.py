"""
Distribution functions for the Fleet Availability Simulator.

This module provides custom implementations of probability distributions
used throughout the simulation: Weibull (for failure modelling),
lognormal (for repair times), normal, and Poisson (for sortie generation).

All functions accept numpy RandomState objects for full reproducibility.
No global random state is used anywhere.

References
----------
MIL-HDBK-338B, Electronic Reliability Design Handbook.
Law, A.M. and Kelton, W.D. "Simulation Modeling and Analysis", 5th ed.
"""

import numpy as np
from scipy.special import gamma as gamma_func
from scipy.optimize import minimize


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
HOURS_PER_DAY = 24


# ---------------------------------------------------------------------------
# Random variate generators
# ---------------------------------------------------------------------------

def weibull_rvs(beta, eta, rng):
    """
    Generate one Weibull random variate using inverse CDF method.

    Parameters
    ----------
    beta : float
        Shape parameter (> 0).
    eta : float
        Scale parameter in hours (> 0).
    rng : numpy.random.RandomState
        Seeded random state for reproducibility.

    Returns
    -------
    float
        Random variate in hours.

    Notes
    -----
    Formula: eta * (-ln(U))^(1/beta) where U ~ Uniform(0,1).
    This is the standard inverse CDF (quantile) method for Weibull.
    """
    u = rng.uniform()
    return eta * (-np.log(u)) ** (1.0 / beta)


def lognormal_rvs(mean_hours, sigma_log, rng):
    """
    Generate one lognormal random variate.

    Parameters
    ----------
    mean_hours : float
        Mean of the underlying normal distribution in log-space (mu parameter).
    sigma_log : float
        Standard deviation in log-space (sigma parameter).
    rng : numpy.random.RandomState
        Seeded random state for reproducibility.

    Returns
    -------
    float
        Random variate in hours (always positive).

    Notes
    -----
    The generated variate is exp(N(mean_hours, sigma_log^2)).
    mean_hours here is mu in the lognormal parameterisation (log-space mean).
    """
    z = rng.normal(loc=mean_hours, scale=sigma_log)
    return np.exp(z)


def normal_rvs(mean, std, rng):
    """
    Generate one Normal random variate.

    Parameters
    ----------
    mean : float
        Mean of the distribution.
    std : float
        Standard deviation of the distribution.
    rng : numpy.random.RandomState
        Seeded random state for reproducibility.

    Returns
    -------
    float
        Random variate.
    """
    return rng.normal(loc=mean, scale=std)


def poisson_interval(mean_hours, rng):
    """
    Generate one exponential inter-arrival time for a Poisson process.

    Parameters
    ----------
    mean_hours : float
        Mean inter-arrival time in hours.
    rng : numpy.random.RandomState
        Seeded random state for reproducibility.

    Returns
    -------
    float
        Inter-arrival time in hours (always positive).

    Notes
    -----
    Uses inverse CDF of exponential: -mean * ln(U).
    """
    u = rng.uniform()
    return -mean_hours * np.log(u)


# ---------------------------------------------------------------------------
# Analytical Weibull functions
# ---------------------------------------------------------------------------

def weibull_pdf(t, beta, eta):
    """
    Weibull probability density function.

    Parameters
    ----------
    t : float or array-like
        Time in hours (>= 0).
    beta : float
        Shape parameter (> 0).
    eta : float
        Scale parameter in hours (> 0).

    Returns
    -------
    float or ndarray
        PDF value(s) at time t.
    """
    t = np.asarray(t, dtype=float)
    pdf = (beta / eta) * (t / eta) ** (beta - 1.0) * np.exp(-((t / eta) ** beta))
    return np.where(t >= 0, pdf, 0.0)


def weibull_reliability(t, beta, eta):
    """
    Weibull reliability (survival) function R(t).

    Parameters
    ----------
    t : float or array-like
        Time in hours (>= 0).
    beta : float
        Shape parameter (> 0).
    eta : float
        Scale parameter in hours (> 0).

    Returns
    -------
    float or ndarray
        Reliability R(t) = exp(-(t/eta)^beta).
    """
    t = np.asarray(t, dtype=float)
    return np.exp(-((t / eta) ** beta))


def weibull_mean(beta, eta):
    """
    Analytical mean of a Weibull distribution.

    Parameters
    ----------
    beta : float
        Shape parameter (> 0).
    eta : float
        Scale parameter in hours (> 0).

    Returns
    -------
    float
        Mean time to failure in hours = eta * Gamma(1 + 1/beta).
    """
    return eta * gamma_func(1.0 + 1.0 / beta)


# ---------------------------------------------------------------------------
# Weibull MLE fitting
# ---------------------------------------------------------------------------

def fit_weibull_mle(failure_times):
    """
    Fit Weibull parameters to observed failure time data using MLE.

    Parameters
    ----------
    failure_times : array-like
        Observed failure times (must be > 0).

    Returns
    -------
    dict
        {'beta': fitted_beta, 'eta': fitted_eta, 'log_likelihood': ll}

    Notes
    -----
    Minimises the negative log-likelihood using scipy.optimize.minimize
    with the L-BFGS-B method. Initial guesses: beta=1.5, eta=median.
    """
    data = np.asarray(failure_times, dtype=float)
    data = data[data > 0]
    n = len(data)
    log_data = np.log(data)

    def neg_log_likelihood(params):
        b, e = params
        if b <= 0 or e <= 0:
            return 1e12
        ll = (n * np.log(b)
              - n * b * np.log(e)
              + (b - 1.0) * np.sum(log_data)
              - np.sum((data / e) ** b))
        return -ll

    x0 = [1.5, np.median(data)]
    bounds = [(0.1, 20.0), (1.0, 1e6)]
    result = minimize(neg_log_likelihood, x0, method='L-BFGS-B', bounds=bounds)

    fitted_beta = result.x[0]
    fitted_eta = result.x[1]
    return {
        'beta': fitted_beta,
        'eta': fitted_eta,
        'log_likelihood': -result.fun,
    }
