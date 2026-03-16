Do alag prompts hain. Dono alag conversations mein paste karo.

---

# PROMPT 1 — PYGAME LIVE ANIMATED SIMULATION

Copy karo aur naye conversation mein paste karo.

---

You are an expert Python game developer and defence systems engineer. I want you to build a complete, fully working, visually stunning Pygame-based live animated simulation of a Combat Aircraft Fleet Air Base. This is not a game — it is a real discrete event simulation with a professional military visual interface. Every frame must show something meaningful happening. Zero placeholder code. Every single line must be implemented and runnable.

---

**WHAT THE USER SEES**

When the simulation starts the user sees a top-down 2D view of a military air base at night. Dark background like satellite imagery. The base has these zones clearly visible with labeled borders:

A runway strip on the left side of the screen — long horizontal grey rectangle with white centerline dashes that animate (dashes scroll when a jet is taking off or landing).

Twelve aircraft parking spots arranged in two rows of six in the center — each spot is a small concrete-colored rectangle with a yellow outline.

Three maintenance bays on the right side — larger rectangles colored differently: O-level bay (blue tint), I-level bay (orange tint), D-level depot bay (red tint). Each bay shows how many technicians are currently working inside as small human-shaped icons.

A parts warehouse in the bottom right corner — shows 4 bar graphs (one per part type: engine, avionics, hydraulics, airframe) showing current stock level vs reorder point. When stock hits zero the bar turns red and pulses.

A control panel strip along the very bottom of the screen — dark panel with buttons and live readout numbers.

---

**AIRCRAFT VISUAL STATES**

Each aircraft on its parking spot must be drawn as a small top-down fighter jet silhouette (draw this using pygame.draw polygons — a triangle for fuselage, two small triangles for wings, one small triangle for tail). Size approximately 40x25 pixels.

Aircraft color must reflect status:
BRIGHT GREEN with a soft glow effect — FMC (fully mission capable, ready to fly).
YELLOW with pulsing glow — PMC (partially mission capable, can fly with limitations).
RED with static glow — NMC due to subsystem failure, waiting for maintenance.
ORANGE blinking — NMC due to parts shortage (PAM status). Blink rate 1Hz.
BLUE moving slowly toward maintenance bay — aircraft being towed to maintenance.
WHITE with motion trail — aircraft on sortie, shown moving along runway then disappearing off screen left.
GREY — aircraft in depot, not on base.

When an aircraft changes state there must be a smooth color transition over 0.5 seconds — not an instant snap.

When an aircraft goes on sortie: animate it taxiing from its parking spot to the runway (smooth movement, 2 seconds), then accelerating along the runway with an afterburner effect (two small orange flame polygons at the tail that grow larger), then disappearing off the left edge of the screen. After sortie duration it reappears from the right edge, decelerates, and taxis back to its spot.

When an aircraft moves to maintenance bay: animate a slow tow (1/4 speed of sortie movement) from parking spot to the appropriate bay. Show a small tow truck rectangle leading it.

---

**TECHNICIAN ANIMATIONS**

Each maintenance bay shows technician figures as small stick figures (5 pixels tall, drawn with pygame.draw.line calls). When a technician is actively working on an aircraft the figure has a small animated wrench (rotating line) next to it. When waiting for parts the figure is stationary with a question mark above it. When off shift the figure is not visible.

Shift changes must be visually dramatic: at 0600 and 1800 simulated time, show a brief flash of the maintenance bays, new technician figures walk in from the side of the screen (smooth horizontal movement), old figures walk off the opposite side.

---

**HUD ELEMENTS — always visible**

Top left corner: Simulated date and time displayed as "DAY 047 — 14:32" in a military stencil-style font. Time runs at 60x real speed by default (1 simulated hour = 1 real second). Speed multiplier shown next to time.

Top center: Three large circular gauges drawn with pygame.draw.arc. Left gauge: MCR (Mission Capable Rate) — needle sweeps from 0 to 100%, colored green above 75%, amber 60-75%, red below 60%. Center gauge: FMCR. Right gauge: Fleet Tempo (sorties per day). Each gauge has tick marks at 25%, 50%, 75%, 100%. The needle animates smoothly — does not snap.

Top right: Event log — a scrolling list of the last 8 events in small white text on dark background. Events like "AC-07 engine failure detected", "AC-03 cleared for sortie", "Parts reorder triggered: avionics", "Shift change: night crew on duty". New events slide in from the top, old ones slide out the bottom.

Bottom panel (control strip): 
SPEED button — cycles through 30x, 60x, 120x, 300x simulation speed.
SURGE button — when clicked turns red, surge mode activates, sortie tempo doubles, a red "SURGE ACTIVE" text pulses in the top center.
PAUSE button — freezes simulation, all animations pause, overlay text "SIMULATION PAUSED" appears.
RESET button — restarts simulation from day 0.
Four small MCR history sparklines (tiny 80x30 pixel line graphs) showing MCR trend for last 30 simulated days. These update every simulated day.

---

**PARTICLE AND VISUAL EFFECTS**

Afterburner effect: when an aircraft takes off, draw 8-12 small orange and yellow circles at the tail position that expand and fade over 0.3 seconds. New particles generated every frame during takeoff roll.

Failure effect: when a subsystem fails on an aircraft, show a brief red flash (fill the aircraft rectangle with red at 50% alpha for 0.5 seconds) then a small smoke puff (grey expanding circle that fades).

Parts arrival effect: when a parts reorder arrives at the warehouse, show a small green flash on the warehouse and a "+N" text that floats upward and fades.

Shift change effect: brief white horizontal sweep across the maintenance bay area, like a searchlight.

Surge activation effect: entire screen briefly flashes amber, then a persistent red tint is added to the screen edges (vignette effect) for the duration of surge.

---

**SIMULATION ENGINE UNDERNEATH**

The Pygame display is the front-end. The simulation engine underneath is the full SimPy discrete event simulation from the fleet availability project. The two run in separate threads. SimPy thread runs the actual simulation logic. Pygame thread reads the current state from a shared thread-safe state dictionary and renders it every frame at 60 FPS.

The shared state dictionary is updated by the SimPy thread every simulated hour and contains: list of 12 aircraft with their current status, position, target position, subsystem health values. Maintenance bay occupancy. Parts inventory levels. Current KPI values. Event log queue.

Use Python threading.Lock() to protect the shared state from race conditions. The Pygame thread never writes to the shared state — read only. The SimPy thread never reads from Pygame — write only. This clean separation means the simulation never slows down due to rendering and the rendering never blocks the simulation.

---

**EXACT FILE STRUCTURE**

```
fleet-live-sim/
    engine/
        simulation.py
        aircraft.py
        subsystem.py
        maintenance.py
        inventory.py
        distributions.py
        shared_state.py
    display/
        renderer.py
        aircraft_sprite.py
        gauges.py
        maintenance_bay.py
        warehouse_display.py
        event_log.py
        particles.py
        hud.py
        controls.py
    assets/
        colors.py
        fonts.py
    main.py
    requirements.txt
    README.md
```

---

**EXACT FILE CONTENTS**

**shared_state.py** must contain a class `SharedState` with a threading.Lock and these fields: aircraft_states (list of 12 dicts, each with keys: id, status, x, y, target_x, target_y, health_engine, health_avionics, health_hydraulics, health_airframe, color_transition_progress). bay_states (dict with keys o_level, i_level, depot, each containing: occupancy count, max capacity, technician_count, active_repairs list). inventory_levels (dict with engine, avionics, hydraulics, airframe stock levels and reorder points). kpi (dict with current_mcr, current_fmcr, current_tempo, mcr_history list of last 30 daily values). event_log (collections.deque maxlen 8, each entry is a tuple of (timestamp_string, message, color)). sim_time (float, current simulated hours). surge_active (boolean). paused (boolean). speed_multiplier (int).

**colors.py** must define the full color palette as named constants:
```
BACKGROUND = (8, 12, 18)
RUNWAY_COLOR = (45, 50, 55)
RUNWAY_LINE = (200, 200, 150)
BAY_O_LEVEL = (20, 40, 80)
BAY_I_LEVEL = (60, 35, 10)
BAY_DEPOT = (60, 10, 10)
AIRCRAFT_FMC = (50, 255, 100)
AIRCRAFT_PMC = (255, 220, 50)
AIRCRAFT_NMC = (255, 60, 60)
AIRCRAFT_PAM = (255, 140, 0)
AIRCRAFT_SORTIE = (255, 255, 255)
AIRCRAFT_DEPOT = (100, 100, 120)
GAUGE_GREEN = (50, 220, 80)
GAUGE_AMBER = (255, 180, 0)
GAUGE_RED = (220, 50, 50)
HUD_BG = (12, 16, 24)
HUD_TEXT = (180, 210, 255)
EVENT_FAILURE = (255, 80, 80)
EVENT_REPAIR = (80, 255, 120)
EVENT_PARTS = (255, 200, 50)
EVENT_SHIFT = (150, 180, 255)
SURGE_TINT = (80, 20, 20)
PARTICLE_AFTERBURNER = [(255, 200, 50), (255, 140, 20), (255, 80, 0)]
```

**aircraft_sprite.py** must contain a class `AircraftSprite` with method `draw(surface, x, y, status, heading, color, transition_progress, afterburner_active)`. The jet shape must be drawn entirely with pygame.draw.polygon calls — no image files. Draw: main fuselage as a pointed elongated hexagon, left wing as a swept triangle, right wing as mirror, vertical tail as small triangle at rear, two engine nacelles as small rectangles under wings. When afterburner_active is True draw 3 expanding flame particles at the tail. The color must be blended between old_color and new_color using transition_progress (0.0 to 1.0) for smooth transitions.

**gauges.py** must contain a class `CircularGauge` with method `draw(surface, center_x, center_y, radius, value, min_val, max_val, label, unit)`. Draw: outer ring with pygame.draw.circle (stroke only), tick marks at every 10% as small lines, colored arc from min to current value using pygame.draw.arc, needle as a line from center to the arc position, value text in center, label below. Color the arc and needle based on value thresholds (green/amber/red).

**particles.py** must contain a class `ParticleSystem` with methods: `emit_afterburner(x, y)`, `emit_failure_flash(x, y)`, `emit_parts_arrival(x, y)`, `update()`, `draw(surface)`. Each particle has position, velocity, lifetime, max_lifetime, color, size. `update()` advances all particles one frame and removes dead ones. `emit_afterburner` creates 5 particles per call with random velocity spread in the backward direction, orange-yellow colors, lifetime 0.3 seconds.

**renderer.py** must contain the main `Renderer` class that owns the pygame window (1400x800 pixels) and calls all sub-renderers in the correct order each frame: (1) fill background, (2) draw runway, (3) draw parking spots, (4) draw maintenance bays, (5) draw warehouse, (6) update and draw particles, (7) draw aircraft sprites, (8) draw technician figures, (9) draw HUD gauges, (10) draw event log, (11) draw control panel, (12) draw surge vignette if active, (13) pygame.display.flip().

**main.py** must start two threads: SimPy simulation thread and Pygame render thread. Main thread runs the Pygame event loop (handling button clicks, keyboard shortcuts: SPACE=pause, S=surge, R=reset, 1/2/3/4=speed). Button clicks write to SharedState with lock acquired. Simulation thread reads speed_multiplier and surge_active from SharedState to adjust its behavior. On window close both threads must exit cleanly.

---

**KEYBOARD SHORTCUTS**

SPACE — pause/resume.
S — toggle surge mode.
R — reset simulation.
1 — 30x speed.
2 — 60x speed (default).
3 — 120x speed.
4 — 300x speed.
ESC — quit.
F — toggle fullscreen.

---

**REQUIREMENTS.txt**

pygame>=2.4.0, numpy>=1.24.0, scipy>=1.10.0, simpy>=4.1.0

---

**DELIVER**

Every file completely. Zero truncation. Zero placeholders. Start with shared_state.py, then colors.py, then the engine files, then the display files, then main.py. The simulation must run with `python main.py` on a clean install. The window must open at 1400x800. Aircraft must be visibly moving within the first 10 simulated days. The gauges must be updating. The event log must be scrolling.

---

---

# PROMPT 2 — STREAMLIT MILITARY OPS DASHBOARD

Copy karo aur alag naye conversation mein paste karo.

---

You are an expert Streamlit developer, data visualisation engineer, and defence systems analyst. I want you to build a complete, fully working, visually stunning Streamlit dashboard for a Combat Aircraft Fleet Availability Simulator. This must look like a real military operations center display — dark theme, glowing gauges, animated charts, live updating KPIs. Not a boring data science dashboard. A proper military product.

Build every single file completely. Zero placeholder code. Zero truncation. Must run on first try with `streamlit run app.py`.

---

**OVERALL VISUAL DESIGN**

Dark military theme throughout. Background color #0A0F1A (near black with blue tint). All panels are dark cards with subtle blue borders (#1A3A5C border, #0D1B2A background). Text is #E0E8FF (soft blue-white) for primary, #7A9CC0 for secondary. Accent colors: green #00FF88 for good status, amber #FFB800 for warning, red #FF3B3B for critical. Font is monospace for numbers (to look like instrument displays) and sans-serif for labels.

Apply this custom CSS at the very top of app.py using st.markdown with unsafe_allow_html=True. The CSS must style: page background, all st.metric components (large monospace numbers with glow effect), all st.dataframe components (dark table with blue header), sidebar (darker than main panel), all plotly charts (dark background matching page).

---

**PAGE LAYOUT**

The page title at the top must be styled as: large bold text "FLEET READINESS OPERATIONS CENTER" in a military stencil style, with a subtitle "Combat Aircraft Availability Analysis System — Classified: RESTRICTED" in small amber text. Add a thin horizontal amber line below the title.

Below the title: a live "mission clock" showing current simulated day and time, updating every second using st.empty() and a while loop inside a thread. Format: "SIM DAY 047 | 14:32 HRS | SPEED: 60x".

The main layout is three columns for the top KPI strip, then full-width charts below, then tabs for detailed analysis.

---

**TOP KPI STRIP — Three columns**

Each column shows one big metric card. Style each as a glowing panel.

Left card — MCR (Mission Capable Rate): giant number like "74.2%" in green monospace font with a green glow (text-shadow CSS). Below the number: "± 2.1% (95% CI)" in small text. Below that: a tiny sparkline (10-day trend) drawn as an SVG line chart embedded in HTML. A status label: "OPERATIONAL" in green, "DEGRADED" in amber, or "CRITICAL" in red based on thresholds.

Center card — FMCR (Full Mission Capable Rate): same layout as MCR card but separate value.

Right card — Fleet Status Breakdown: not a single number but a mini horizontal stacked bar showing how many of the 12 aircraft are in each status right now. Like "FMC:7 | PMC:2 | NMC-M:2 | NMC-P:1". Each segment colored appropriately. Update this every time simulation runs.

---

**MAIN ANIMATED CHART — Full width**

A Plotly animated figure showing fleet status composition over time as a stacked area chart. X-axis is simulated day. Y-axis is number of aircraft (0 to 12). Five stacked areas: FMC (green), PMC (yellow), NMC-maintenance (orange), NMC-parts (red), NMC-depot (dark red). 

This chart must use Plotly animation frames — not a static chart. When the simulation runs, use st.plotly_chart with the full animated figure that plays automatically showing how the fleet composition evolved day by day. Play button visible. Slider below the chart showing time progression. Frame rate 10 frames per second.

Add vertical dashed lines on this chart for: surge start and end (red dashed, labeled "SURGE START" and "SURGE END"), shift changes (subtle grey dashed every 12 hours visible when zoomed in).

---

**SIDEBAR — Full control panel**

Style the sidebar header as "MISSION PARAMETERS" in amber stencil text.

Group controls into sections with styled headers:

Section "FLEET CONFIGURATION":
Fleet size: st.slider 4 to 24, default 12, step 2. Show the current value as "12 AIRCRAFT" in military style.
Simulation duration: st.selectbox options "90 DAYS", "180 DAYS", "365 DAYS".
Random seed: st.number_input labeled "SEED (REPRODUCIBILITY)".

Section "MAINTENANCE RESOURCES":
Day shift O-level technicians: st.slider 2 to 16, default 8.
Day shift I-level technicians: st.slider 1 to 8, default 4.
Show a derived metric: "TECH:AIRCRAFT RATIO = 0.83" that updates as sliders change. Color this green if above 0.8, amber if 0.5-0.8, red if below 0.5.

Section "OPERATIONAL TEMPO":
Peacetime sortie interval: st.slider 24 to 96 hours, default 48.
Show derived "SORTIES/DAY/AIRCRAFT = 0.5" that updates.

Section "SURGE OPERATIONS":
Enable surge: st.toggle styled with red color when on.
Show a warning box when surge enabled: st.warning "SURGE MODE: Expect 15-25% MCR degradation".
Surge start day: st.slider shown only when surge enabled.
Surge duration: st.slider shown only when surge enabled.

Section "ANALYSIS":
Monte Carlo replications: st.selectbox options 10, 50, 100, 500.
A styled "EXECUTE SIMULATION" button — large, full sidebar width, amber background, dark text. When clicked shows a progress bar with military-style messages: "INITIALISING FLEET...", "LOADING MAINTENANCE PROTOCOLS...", "RUNNING SIMULATION DAY 1/365...", "COMPUTING STATISTICS...".

---

**FIVE TABS — Main analysis area**

**TAB 1 — OPERATIONS OVERVIEW**

Sub-section "FLEET STATUS MATRIX": A 3x4 grid of aircraft cards. Each card shows: aircraft ID (AC-01 through AC-12), current status as a colored badge, subsystem health as four small horizontal bars (engine, avionics, hydraulics, airframe), flight hours accumulated, and sorties completed. Build this entirely in HTML/CSS using st.markdown with unsafe_allow_html=True. Each card is a dark rounded rectangle with a colored left border matching status color. Green border for FMC. Yellow for PMC. Red for NMC. This must look like a real aircraft status board.

Sub-section "MAINTENANCE PIPELINE": Three columns showing O-level bay, I-level bay, D-level depot. Each shows: current occupancy as "3/8 BAYS OCCUPIED", queue length as "2 AIRCRAFT WAITING", mean wait time, and a horizontal progress bar for capacity utilisation. Style as dark instrument panels.

Sub-section "PARTS WAREHOUSE STATUS": Four columns (engine, avionics, hydraulics, airframe parts). Each shows current stock as a vertical bar gauge drawn in Plotly with color zones: green zone (above reorder point), amber zone (at reorder point), red zone (zero stock). Show "REORDER IN TRANSIT" with an animated dot if an order is currently in transit.

**TAB 2 — STATISTICAL ANALYSIS**

Left half: Plotly histogram of MCR across all Monte Carlo replications. Dark background. Green bars. Overlay a fitted Normal distribution curve in white. Add vertical lines at 5th percentile (red dashed), 50th percentile (white), 95th percentile (green dashed). Label each line. Title: "MCR DISTRIBUTION — N=500 REPLICATIONS".

Right half: Plotly convergence plot showing running mean MCR and 95% CI band as replications increase from 1 to 500. X-axis "NUMBER OF REPLICATIONS", Y-axis "MEAN MCR ESTIMATE". The CI band fills with a semi-transparent green. Add a horizontal dashed line at the final converged value. Add annotation: "CI HALF-WIDTH < 1% AT N=47 REPLICATIONS".

Below both: A styled summary statistics table using st.dataframe with these columns: Metric, Mean, Std Dev, 5th Pct, 95th Pct, 95% CI Lower, 95% CI Upper. Rows: MCR, FMCR, PAM Fraction, Mean Maintenance Time, Total Annual Sorties. Apply custom CSS to make the table dark with blue headers and alternating row colors.

**TAB 3 — SENSITIVITY ANALYSIS**

Title: "PARAMETER SENSITIVITY — SOBOL VARIANCE DECOMPOSITION"

A styled explanation box: "Sobol indices show what fraction of MCR variance is explained by each input parameter. S1 = direct effect. ST = total effect including interactions."

Main figure: Plotly horizontal bar chart with two bars per parameter (S1 in solid color, ST in outlined bar). Parameters sorted by ST descending. Color code: top 3 parameters in amber (dominant), rest in blue (minor). X-axis labeled "SOBOL SENSITIVITY INDEX (0 = no effect, 1 = full effect)". Add a vertical dashed line at x=0.05 labeled "SIGNIFICANCE THRESHOLD".

Below the chart: a styled recommendation box using st.info: "KEY FINDING: [top parameter] and [second parameter] together explain [X]% of MCR variance. Focus maintenance investment on these factors first."

A second smaller chart: interaction effects heatmap. 8x8 grid showing pairwise Sobol interaction indices. Color scale from white (no interaction) to deep red (strong interaction). Title: "PARAMETER INTERACTION MATRIX".

**TAB 4 — SURGE ANALYSIS**

Title: "SURGE OPERATIONS IMPACT ASSESSMENT"

Top: Three metric cards styled in amber/red color scheme: "MCR DURING SURGE", "MCR 7-DAY POST-SURGE", "RECOVERY TIME TO BASELINE".

Main chart: Plotly time series of mean MCR with 95% CI band (from 100 replications). X-axis in days. Y-axis 0-100%. Shade the surge period in semi-transparent red. Add annotations: arrow pointing to MCR drop onset with label "SURGE BEGINS — MCR DROPS", arrow at recovery point labeled "BASELINE RESTORED — DAY X". Add a horizontal dashed green line at 75% labeled "OPERATIONAL THRESHOLD".

Below: Two side-by-side charts. Left: maintenance queue length during and after surge showing backlog buildup and clearance. Right: parts stockout frequency per day showing how surge depletes inventory.

Recommendation box at bottom: styled as a military intel summary in amber border box. "ASSESSMENT: Under current maintenance establishment (8 O-level, 4 I-level), fleet MCR drops from X% to Y% during 72-hour surge. Recovery to baseline requires Z days. Minimum technician augmentation to maintain 75% MCR during surge: N additional O-level technicians."

**TAB 5 — RESEARCH FINDINGS**

Title: "RESEARCH QUESTION: MINIMUM VIABLE TECHNICIAN RATIO"

A styled abstract box in dark blue border: "This analysis answers the operational planning question: what is the minimum technician-to-aircraft ratio that maintains MCR above 75% during surge operations? Results are based on a full factorial simulation study across 5 fleet sizes and 6 staffing levels with 50 replications per configuration (1,500 total simulation runs)."

Main figure: Plotly heatmap. X-axis: fleet size (8, 10, 12, 16, 20 aircraft). Y-axis: technician-to-aircraft ratio (0.4 to 1.5). Color: mean surge MCR. Color scale: red (below 60%) through amber (60-75%) to green (above 75%). Add a thick white contour line at MCR=75% labeled "OPERATIONAL THRESHOLD". This is the most important chart in the entire project.

Below heatmap: Plotly line chart of minimum viable ratio vs fleet size. Show whether the relationship is linear or superlinear (fit and display the equation). Add annotation: "SUPERLINEAR SCALING: larger fleets require disproportionately more technicians per aircraft."

Key finding box — style as a highlighted military intelligence report: dark background, amber left border, bold amber text for the key number. "FOR A 12-AIRCRAFT FLEET: Minimum technician-to-aircraft ratio = X.X | Minimum day-shift O-level technicians = N | Exceeding this threshold yields diminishing returns above MCR = 82%."

Download button styled in green: "DOWNLOAD FULL RESEARCH REPORT (PDF)". When clicked triggers download of the research_report.pdf generated by reportlab.

---

**LIVE UPDATING FEATURE**

At the very top of the main panel, below the mission clock, add a "LIVE MODE" toggle. When enabled, the simulation reruns automatically every 30 seconds with the current parameters and updates all charts. Show a pulsing green dot next to "LIVE MODE ACTIVE". Use st.rerun() inside a time.sleep loop in a background thread to trigger updates. When live mode is off show a grey dot and "STATIC MODE — Press EXECUTE to update."

---

**EXPORT FEATURES**

Floating action button in bottom right corner (positioned with CSS fixed positioning): a dark circle with a download icon. When clicked expands to show three export options: "EXPORT ALL CHARTS (PNG)", "EXPORT DATA (CSV)", "EXPORT RESEARCH REPORT (PDF)". Each option triggers the appropriate download using st.download_button.

---

**EXACT FILE STRUCTURE**

```
fleet-dashboard/
    app.py
    simulation/
        engine.py
        distributions.py
        kpi_calculator.py
        sensitivity_runner.py
        research_analysis.py
    components/
        fleet_status_matrix.py
        gauge_charts.py
        animated_timeline.py
        sensitivity_charts.py
        surge_charts.py
        research_charts.py
        kpi_cards.py
    styles/
        military_theme.py
    utils/
        cache_manager.py
        export_handler.py
        report_generator.py
    requirements.txt
    README.md
```

---

**military_theme.py** must contain one function `inject_military_css()` that returns a complete CSS string covering every visual element described above. This function is called once at the top of app.py. The CSS must include: page background, card styles, metric number glow effect, sidebar styling, button styling, table styling, badge styles for FMC/PMC/NMC status, the aircraft status card grid layout, the amber recommendation box style, the key finding highlight box style.

**cache_manager.py** must use st.cache_data with hash_funcs for the SimPy simulation. Cache key is a tuple of all simulation parameters. TTL is 3600 seconds. Include a function `clear_cache_if_params_changed(current_params, previous_params)` that calls st.cache_data.clear() if any parameter has changed.

---

**REQUIREMENTS.txt**

streamlit>=1.28.0, numpy>=1.24.0, scipy>=1.10.0, matplotlib>=3.7.0, pandas>=2.0.0, simpy>=4.1.0, SALib>=1.4.7, plotly>=5.15.0, reportlab>=4.0.0, tqdm>=4.65.0

---

**CODE QUALITY**

Every component function has a docstring. All Plotly figures have consistent dark theme applied via a `get_dark_template()` function in gauge_charts.py that returns a plotly layout dict — call this on every single figure, never style charts individually. All st.cache_data decorated functions have explicit show_spinner messages in military language. No st.experimental functions — use only stable Streamlit API. The app must run with zero errors and zero warnings on `streamlit run app.py`.

---

**DELIVER**

Every file completely. Zero truncation. Zero placeholders. Start with styles/military_theme.py, then simulation files, then component files, then app.py last. After all files confirm: (1) the page loads without error, (2) the Execute Simulation button runs and updates all charts, (3) the fleet status matrix shows all 12 aircraft cards with correct colors, (4) the Sobol heatmap renders correctly, (5) the PDF download works.