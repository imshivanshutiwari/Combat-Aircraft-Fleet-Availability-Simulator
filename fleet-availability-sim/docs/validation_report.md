# Validation Report — Combat Aircraft Fleet Availability Simulator

## 1. Conceptual Validation

### 1.1 System Description
This simulation models a fleet of combat aircraft operating under realistic military maintenance constraints. The system comprises:
- **Fleet**: Configurable number of aircraft (default 12), each with four independent subsystems (engine, avionics, hydraulics, airframe)
- **Failure Model**: Weibull distributions for time-to-failure, parameterised from publicly available military reliability data
- **Maintenance**: Three-tier system matching real air force operations (O-level, I-level, D-level)
- **Inventory**: (r, Q) continuous review spare parts policy with stochastic lead times
- **Staffing**: Shift-based scheduling with day/night/weekend variations
- **Operations**: Poisson sortie generation with peacetime and surge OPTEMPO

### 1.2 Assumptions
1. Subsystem failures are independent (no common-cause failures)
2. Weibull parameters are constant over the simulation horizon (no aging of the fleet)
3. Repair times follow lognormal distributions (right-skewed, as standard in maintenance literature)
4. Spare parts are generic per subsystem class (not component-level granularity)
5. All aircraft are of the same type (homogeneous fleet)
6. Weather does not affect sortie generation (flat Earth approximation for sortie timing)
7. Maintenance resources are pooled (any technician can work any aircraft)
8. No priority queueing (FIFO service discipline)

### 1.3 What Is NOT Modelled
- **Condition-Based Maintenance (CBM)**: No predictive maintenance triggers
- **Cannibalisation**: No robbing of parts from one aircraft to repair another
- **Contractor Maintenance**: All maintenance is organic (military technicians)
- **Pilot Availability**: Pilot scheduling is not a constraint
- **Multi-Base Operations**: Single-base model
- **Supply Chain Disruptions**: Lead times are stochastic but not subject to systemic disruption
- **Training and Proficiency**: Technician skill levels are homogeneous

## 2. Verification Tests

### 2.1 Test 1: Weibull Distribution Verification
**Procedure**: Generate 10,000 Weibull variates for each subsystem using `weibull_rvs()`. Compare sample mean against analytical mean `eta * Gamma(1 + 1/beta)`.

**Pass Criterion**: Sample mean within 2% of analytical mean.

```python
from src.distributions import weibull_rvs, weibull_mean
import numpy as np

rng = np.random.RandomState(42)
params = {'engine': (2.1, 800), 'avionics': (1.4, 600),
          'hydraulics': (1.8, 1200), 'airframe': (3.0, 2000)}

for name, (beta, eta) in params.items():
    samples = [weibull_rvs(beta, eta, rng) for _ in range(10000)]
    sample_mean = np.mean(samples)
    analytical = weibull_mean(beta, eta)
    error = abs(sample_mean - analytical) / analytical * 100
    print(f'{name}: sample={sample_mean:.1f}, analytical={analytical:.1f}, error={error:.2f}%')
    assert error < 2.0, f"FAIL: {name} error {error:.2f}% exceeds 2%"
```

**Expected Result**: All four subsystems pass with error < 2%.

### 2.2 Test 2: M/M/1 Queue Verification
**Procedure**: Configure a simplified system with exponential inter-arrival and service times. Verify that simulated mean queue length matches `L = rho/(1-rho)` analytical formula.

**Pass Criterion**: Simulated mean queue length within 15% of analytical prediction (allowing for warm-up and finite simulation effects).

### 2.3 Test 3: Inventory Level Verification
**Procedure**: Verify mean stock level approximates `(r + Q/2) - demand × lead_time` for each part class under steady-state conditions.

**Pass Criterion**: Mean stock level consistent with analytical approximation within 20% (accounting for demand variability and stochastic lead times).

## 3. Operational Validation

### 3.1 Benchmark Comparison
The calibrated model is compared against the following publicly available benchmarks:

| Source | Aircraft | MCR |
|--------|----------|-----|
| US GAO Report GAO-21-279 | F-16 | 71.9% |
| US GAO Report GAO-21-279 | F/A-18 | 62.1% |
| US GAO Report GAO-21-279 | F-35A | 54.6% |
| Indian CAG Report 2021 | IAF Fighters (high readiness) | 75–80% |

### 3.2 Statistical Validation
The calibrated model produces MCR values statistically consistent with published benchmarks at the 5% significance level, as verified by the two-sample Kolmogorov-Smirnov test in Notebook 06.

The KS test result confirms that we fail to reject the null hypothesis that simulated and reference MCR distributions are drawn from the same population, providing confidence in the model's operational validity.

### 3.3 Sensitivity Analysis Validation
Sobol sensitivity analysis (Notebook 03) confirms that the dominant parameters are subsystem reliability (Weibull eta) and technician staffing levels, which aligns with operational experience and published maintenance engineering literature.
