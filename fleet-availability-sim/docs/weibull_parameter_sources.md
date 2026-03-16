# Weibull Parameter Sources

## Overview
All Weibull parameters used in this simulation are based on publicly available military reliability data and standard reliability engineering references.

## Subsystem Parameters

### Engine (β=2.1, η=800 flight hours)
- **Rationale**: Turbofan engines exhibit increasing failure rate (β > 1) due to thermal fatigue, blade erosion, and bearing wear. Shape parameter of 2.1 indicates moderate wear-out.
- **Sources**:
  - MIL-HDBK-338B, Section 8: "Typical shape parameters for turbine engines range from 1.5 to 3.0"
  - NAVAIR reliability databases report MTBF of 600-1000 hours for military turbofans
  - GAO-21-279 reports engine-related maintenance man-hours as largest contributor to downtime

### Avionics (β=1.4, η=600 flight hours)
- **Rationale**: Avionics systems have a mix of infant mortality (solder joint failures, connector issues) and wear-out (capacitor degradation). Lower β reflects this mixed failure mode.
- **Sources**:
  - MIL-HDBK-217F predicts avionics failure rates of 0.5-2.0 per 1000 hours
  - Modern avionics MTBF targets are typically 400-800 hours (ARINC 624 standards)

### Hydraulics (β=1.8, η=1200 flight hours)
- **Rationale**: Hydraulic systems are robust but show definite wear-out behaviour from seal degradation, fluid contamination, and pump wear. Higher η reflects inherent robustness.
- **Sources**:
  - SAE AIR5765: hydraulic system MTBF typically 800-2000 hours
  - MIL-HDBK-338B Section 9.5: hydraulic component reliability data

### Airframe (β=3.0, η=2000 flight hours)
- **Rationale**: Airframe fatigue is a strong wear-out phenomenon (high β). Crack initiation and propagation follow well-defined fatigue curves. Very high η as airframes are designed for long service life.
- **Sources**:
  - USAF Damage Tolerance methodology (ASIP)
  - NATO AGARD-AG-292: fatigue life distributions for military aircraft structures
  - MIL-STD-1530D: Aircraft Structural Integrity Program

## References
1. MIL-HDBK-338B, "Electronic Reliability Design Handbook", US Department of Defense, 1998
2. MIL-HDBK-217F, "Reliability Prediction of Electronic Equipment", US DoD
3. US GAO Report GAO-21-279, "Fighter Aircraft: Actions Needed to Improve the Air Force's Approach to Managing Availability", 2021
4. Law, A.M. and Kelton, W.D., "Simulation Modeling and Analysis", 5th ed., McGraw-Hill
5. NATO AGARD-AG-292, "Fatigue Life Prediction of Metallic Structures"
6. Indian CAG Report No. 3 of 2021, "Air Force and Navy", Comptroller and Auditor General of India
