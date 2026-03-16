# Military Ops Center Dashboard

A full-featured Streamlit dashboard styled as a military operations center
for monitoring fleet readiness and combat aircraft availability.

## Running

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Features

### 6 Tab Views

| Tab | Content |
|-----|---------|
| **FLEET STATUS** | KPI gauges, 3×4 aircraft matrix with health bars, maintenance pipeline, parts warehouse |
| **TIME SERIES** | Animated stacked area chart of fleet composition, inventory trends, queue lengths |
| **SENSITIVITY** | Sobol parameter sensitivity analysis with bar charts and interaction heatmap |
| **SURGE ANALYSIS** | Surge impact assessment with MCR degradation, recovery curves, 95% CI bands |
| **RESEARCH** | Technician ratio sweep study — heatmap, threshold curve, key finding |
| **REPORT & EXPORT** | Executive summary with recommendations, CSV/JSON data downloads |

### Sidebar Controls
- Fleet size (4-24 aircraft)
- Simulation duration (90-365 days)
- Sortie interval (18-72 hours)
- Maintenance technician allocation
- Surge configuration
- Monte Carlo replications

### Military Styling
- Dark operations center theme
- Monospace instrument fonts
- Glowing metric readouts
- Color-coded status badges (FMC/PMC/NMC-M/NMC-P/NMC-D)
- Health bars with gradient fills
- Amber warning highlights
