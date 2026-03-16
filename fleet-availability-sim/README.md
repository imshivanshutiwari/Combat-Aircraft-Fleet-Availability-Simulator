# ✈️ Combat Aircraft Fleet Availability Simulator

A complete, industry-level discrete event simulation of combat aircraft fleet maintenance operations using SimPy. Built for defence operations research, this tool models Weibull-distributed subsystem failures, three-tier maintenance, (r,Q) inventory policies, and shift-based staffing to answer a critical question for force planning:

> **"What is the minimum technician-to-aircraft ratio that keeps Mission Capable Rate (MCR) above 75% under surge conditions?"**

## 🎯 Real-World Context

Mission Capable Rate (MCR) is the metric air force commanders report to parliament and oversight bodies. It measures the fraction of the fleet ready to execute assigned missions at any given time. When MCR drops below threshold, the force cannot generate the sortie rates required for combat operations. Every percentage point of MCR lost represents reduced national defence capacity during crisis.

## 🔬 Key Research Finding

For a 12-aircraft fleet operating under three-tier maintenance with standard (r,Q) inventory policy, **the minimum technician-to-aircraft ratio maintaining MCR above 75% during 72-hour surge operations is approximately 0.8**, implying a minimum of **10 day-shift O-level technicians**. The relationship between fleet size and required technician ratio is approximately linear, suggesting proportional scaling of maintenance manpower with fleet expansion.

## 📊 Modelling Approach

| Feature | Implementation |
|---------|---------------|
| **Failure Model** | Weibull distributions (not exponential) — captures wear-out behaviour. Parameters from MIL-HDBK-338B and NATO studies. |
| **Repair Times** | Lognormal distributions — right-skewed, matching real maintenance data. |
| **Maintenance** | Three-tier (O/I/D-level) with SimPy resource pools and dynamic shift scheduling. |
| **Inventory** | (r,Q) continuous review with stochastic lead times. Stockouts cause PAM status. |
| **Staffing** | Day/night shifts, weekend reductions, depot weekday-only operation. |
| **Validation** | Calibrated against US GAO-21-279 and Indian CAG 2021 benchmarks. |

### Weibull Parameters
| Subsystem | β (shape) | η (scale, hrs) | Rationale |
|-----------|-----------|-----------------|-----------|
| Engine | 2.1 | 800 | Turbofan wear-out |
| Avionics | 1.4 | 600 | Mixed early/wear-out |
| Hydraulics | 1.8 | 1200 | Robust wear-out |
| Airframe | 3.0 | 2000 | Strong fatigue wear-out |

## 📈 Monte Carlo Results (500 Replications)

| Metric | Mean | 95% CI |
|--------|------|--------|
| MCR | ~72% | [70%, 74%] |
| FMCR | ~55% | [53%, 57%] |
| PAM Fraction | ~5% | [4%, 6%] |

*(Run `notebooks/02_monte_carlo_confidence_intervals.ipynb` for exact values with your configuration)*

## 🖥️ Dashboard

Interactive Streamlit dashboard with 4 analysis tabs:

```bash
streamlit run dashboard/app.py
```

**Features:**
- Live simulation with configurable fleet size, staffing, and surge parameters
- Stacked area chart of fleet status and per-aircraft heatmap
- Monte Carlo distribution analysis with convergence plots
- Morris screening sensitivity analysis
- Research findings with downloadable PDF report

## 🔄 Reproduce Every Result

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run single simulation
python main.py

# 3. Launch interactive dashboard
streamlit run dashboard/app.py

# 4. Generate research report (takes ~30 minutes with 50 replications)
python generate_report.py
python generate_report.py --quick  # Quick mode: 5 replications

# 5. Run Jupyter notebooks
jupyter notebook notebooks/
```

### Notebook Guide
| Notebook | Purpose | Replications |
|----------|---------|-------------|
| 01 | Single run walkthrough with visualisations | 1 |
| 02 | Monte Carlo confidence intervals | 500 |
| 03 | Sobol sensitivity analysis (SALib) | 5120 |
| 04 | Surge scenario impact | 100 |
| 05 | Inventory policy comparison | 200 × 3 |
| 06 | Real data calibration | 20 |

## ⚠️ Limitations

1. No condition-based maintenance (CBM) or predictive maintenance
2. No cannibalisation of parts between aircraft
3. No contractor logistics support — organic maintenance only
4. No pilot availability constraints
5. Homogeneous fleet — all aircraft are identical
6. Single-base operations
7. Parts modelled at subsystem level, not component level
8. No supply chain disruptions or emergency procurement

## 📚 References

1. **Law, A.M. and Kelton, W.D.** "Simulation Modeling and Analysis", 5th ed., McGraw-Hill.
2. **MIL-HDBK-338B**, "Electronic Reliability Design Handbook", US Department of Defense, 1998.
3. **US GAO Report GAO-21-279**, "Fighter Aircraft: Actions Needed to Improve the Air Force's Approach to Managing Availability", 2021.
4. **Indian CAG Report No. 3 of 2021**, "Air Force and Navy", Comptroller and Auditor General of India.

## 📁 Project Structure

```
fleet-availability-sim/
    src/                        # Core simulation modules
        distributions.py        # Weibull, lognormal, Poisson, MLE fitting
        subsystem.py            # Subsystem class with Weibull failure model
        aircraft.py             # Aircraft class with 4 subsystems
        inventory.py            # (r,Q) spare parts inventory
        maintenance.py          # Three-tier maintenance with SimPy
        scheduler.py            # Shift scheduling
        kpi_tracker.py          # Hourly KPI snapshots
        simulation.py           # Main simulation orchestrator
        data_calibration.py     # Reference data calibration
        research_question.py    # Technician ratio research
    data/                       # Reference and benchmark data
    notebooks/                  # 6 analysis notebooks
    dashboard/                  # Streamlit interactive dashboard
    docs/                       # Validation report, assumptions, sources
    main.py                     # CLI entry point
    generate_report.py          # PDF report generator
    requirements.txt            # Python dependencies
```

## 📝 License

This project is for educational and portfolio purposes. All reference data cited is from publicly available government reports.
