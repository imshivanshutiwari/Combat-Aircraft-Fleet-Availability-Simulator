# Model Assumptions

## Failure Process
1. Subsystem failures are **statistically independent** — failure of one subsystem does not affect failure rates of other subsystems on the same aircraft.
2. Time-to-failure follows **Weibull distributions** with constant parameters throughout the simulation (no fleet aging or reliability growth).
3. Failures are **self-announcing** — they are detected immediately upon occurrence and do not require separate diagnostic processes.
4. Only **hard failures** are modelled — degradation below 40% health triggers failure. No grace degradation between soft and hard failure.

## Maintenance Process
5. Repair restores subsystem to **"as good as new"** condition (perfect repair assumption).
6. Maintenance resources are **pooled** — any technician at a given tier can work on any subsystem.
7. Service discipline is **FIFO** (First In, First Out) — no priority queueing based on aircraft criticality or mission requirements.
8. Repair times follow **lognormal distributions**, which is standard in maintenance literature due to right-skewed nature of repair durations.
9. No **cannibalisation** — parts are not removed from one aircraft to repair another.
10. No **contractor logistics support** — all maintenance is performed by organic military technicians.

## Inventory
11. Spare parts are **generic per subsystem class** — e.g., one "engine part" type, not multiple component types per subsystem.
12. **(r, Q) continuous review** inventory policy with Normal lead time distributions.
13. No **emergency procurement** — when stock is zero, aircraft waits until scheduled reorder arrives.
14. No **excess or obsolescence** — parts do not expire or become obsolete.

## Operations
15. Sortie generation follows a **Poisson process** — inter-sortie times are exponentially distributed.
16. Sortie duration is **Uniform(1.2, 2.8)** flight hours — no mission-type differentiation.
17. All aircraft are **identical** — homogeneous fleet with same parameters.
18. **No pilot constraints** — unlimited qualified pilots available.
19. **Flat Earth approximation** — no weather, terrain, or time-zone effects on sortie timing.

## Staffing
20. **Shift scheduling** follows fixed patterns (day 0600-1800, night 1800-0600) with known staffing levels.
21. **Weekend depot closure** — D-level maintenance only operates Monday-Friday 0800-1700.
22. Technician **proficiency is homogeneous** — no skill differentiation or learning curves.

## Financial
23. Costs are in **Indian Rupees (₹)** using the following rates:
    - Holding: ₹100 per part per day
    - Stockout: ₹50,000 per aircraft per PAM day
    - Labour: ₹2,000 per technician per shift
24. No **discount rate** is applied — all costs are nominal.
