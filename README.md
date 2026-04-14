# Heat Pump Cost Analysis

A collection of quantitative analyses — each backed by Python models — exploring the economics and practicalities of installing an air-source heat pump in a 1930s UK semi-detached house. Six articles are supported:

1. **[Considerations for the Fabric First vs Heat Pump First Debate](considerations.md)** — capital and lifecycle cost optimisation across insulation and heat pump options.
2. **[Impediments to UK Heat Pump Adoption and Possible Solutions](impediments.md)** — qualitative analysis of capital cost, space requirements, and the spark gap.
3. **[How the Spark Gap Drives the Radiator Upgrades for a Heat Pump Installation](operations-static.md)** — steady-state thermal modelling of flow temperature, COP, and required radiator capacity.
4. **[Quantitative Analysis of Dynamic Heat Pump Operation for Domestic Heating](operations-dynamic.md)** — dynamic thermal modelling showing how control strategy impacts heat pump economics, comparing gas boiler, simple thermostat, smooth continuous, and tariff-optimised operation.
5. **[Quantitative Analysis of Dynamic Heat Pump Operation for Design Temperature](operations-design.md)** — feedforward optimisation of heating schedules at design temperature (−2°C), comparing smooth vs interrupted operation (DHW + defrost), with and without radiator upgrades.
6. **[Quantitative Analysis of Heat Pump Operation for Domestic Hot Water](domestic-hot-water.md)** — analysis of DHW costs showing daily cost vs outdoor temperature, required spark gap for economic viability, and annual Cambridge 2025 cost comparison (£288/year HP vs £239/year gas energy-only).

## Project Structure

```
heat-pump-cost/
├── data/
│   ├── heat-pump-ratings.csv           # Heat pump specifications and costs
│   ├── home-improvements.csv           # Insulation improvement options
│   └── temperatures-cambridge-2025.csv # Hourly temperature data for annual analysis
├── src/
│   └── heat_pump_cost/
│       ├── __init__.py
│       ├── __main__.py                      # Module entry point
│       ├── cli.py                           # CLI for considerations analysis
│       ├── cost_calculator.py               # Capital + runtime cost optimisation
│       ├── plot_cost_analysis.py            # Generates considerations plots
│       ├── plotter.py                       # Shared plotting utilities
│       ├── operations_model.py              # Steady-state heat flow model + contour plots
│       ├── radiator_analysis.py             # COP vs power/K plots
│       ├── dynamic_thermal_model.py         # First-order dynamic house model
│       ├── identify_thermal_parameters.py   # Parameter identification from data
│       ├── simulate_gas_boiler.py           # Gas boiler baseline simulation
│       ├── simulate_smooth_heat_pump.py     # Continuous operation heat pump
│       ├── simulate_tariff_optimized.py     # Tariff-optimized heat pump control
│       ├── simulate_design_temperature.py   # Design temperature (−2°C) analysis
│       ├── plot_dhw_cost.py                 # DHW daily cost and spark gap plots
│       └── analyze_annual_dhw.py            # Annual DHW cost analysis from temperature data
├── assets/                                  # Generated plots (committed)
├── considerations.md
├── impediments.md
├── operations-static.md
├── operations-dynamic.md
├── operations-design.md
├── domestic-hot-water.md
└── pyproject.toml
```

## Installation

```bash
pip install -e .
```

Requires Python ≥ 3.8 with `numpy`, `scipy`, and `matplotlib`.

---

## Article 1: Considerations for the Fabric First vs Heat Pump First Debate

**File:** [considerations.md](considerations.md)

Explores the capital and 25-year lifecycle cost trade-off between heat pump capacity and home insulation improvements for a 1930s Cambridge semi-detached house (initial heat loss 9 kW / ~25,000 kWh/year).

### Generate the plots

```bash
# Run with defaults (9 kW initial heat loss, 15p/kWh electricity)
heat-pump-cost

# Or as a module
python -m heat_pump_cost
```

This saves four plots to the current directory:

| File | Description |
|---|---|
| `heat_pump_1_no_grant_capital_only.png` | Capital cost only, no grant |
| `heat_pump_2_with_grant_capital_only.png` | Capital cost only, with £7,500 BUS grant |
| `heat_pump_4_no_grant_with_runtime.png` | Capital + 25-year runtime, no grant |
| `heat_pump_5_with_grant_with_runtime.png` | Capital + 25-year runtime, with £7,500 grant |

### Key parameters

| Parameter | Flag | Default | Note |
|---|---|---|---|
| Initial heat loss | `--initial-heat-loss` | `9.0` kW | Set to your property's design heat loss |
| Electricity rate | `--electricity-rate` | `0.15` | £/kWh; update to current price cap |
| Heat pump data | `--heat-pumps` | `data/heat-pump-ratings.csv` | Edit CSV to add/remove models |
| Improvements data | `--improvements` | `data/home-improvements.csv` | Edit CSV to adjust costs |
| Output directory | `--output-dir` | current dir | |

```bash
# Example: current energy prices, specific heat loss
heat-pump-cost --initial-heat-loss 8.0 --electricity-rate 0.2769

# Full help
heat-pump-cost --help
```

### Data files

**`data/heat-pump-ratings.csv`** — one row per heat pump model:  
`capacity_kw`, `property_type`, `heat_demand_kwh`, `electricity_use_kwh`, `cost_gbp`

**`data/home-improvements.csv`** — one row per improvement option:  
`description`, `cost_gbp`, `heat_loss_reduction_watt` (at design conditions: 21°C inside, 2°C outside)

---

## Article 2: Impediments to UK Heat Pump Adoption and Possible Solutions

**File:** [impediments.md](impediments.md)

A qualitative analysis of the three main barriers — capital cost, space requirements, and the spark gap — and potential paths to making heat pump installations comparable in cost and complexity to a gas boiler replacement. No additional Python scripts; the article builds on the findings of Article 1 and refers forward to Article 3.

---

## Article 3: How the Spark Gap Drives the Radiator Upgrades for a Heat Pump Installation

**File:** [operations-static.md](operations-static.md)

Uses a steady-state lumped-mass thermal model with radiator constant K = 71.2 W/K^1.2 to show how the spark gap (currently 4.67) sets the minimum COP threshold and thereby the required flow temperature and radiator capacity for three heating load scenarios.

### Generate the plots

**Contour plot** (`assets/operations_contour.png`) — constant heating power curves over flow rate and flow temperature:

```bash
heat-pump-operations
# or
python -m heat_pump_cost.operations_model
```

**Performance vs power** (`assets/performance_vs_power.png`) and **performance vs K** (`assets/performance_vs_k.png`):

```bash
python -m heat_pump_cost.radiator_analysis
```

### Key parameters

All constants are defined at the top of each module and can be edited directly:

**`src/heat_pump_cost/operations_model.py`**

| Constant | Default | Description |
|---|---|---|
| `HTC` | `244.0` W/K | House heat transfer coefficient |
| `TI` | `19.0` °C | Indoor temperature |
| `TO` | `5.0` °C | Outdoor temperature (design month) |
| `K_RAD` | `71.2` W/K^1.2 | Radiator constant |
| `N_RAD` | `1.2` | Radiator exponent |
| `Q_TARGET` | `1960.0` W | Average radiator power (from bills) |

**`src/heat_pump_cost/radiator_analysis.py`**

| Constant | Default | Description |
|---|---|---|
| `K_CURRENT` | `71.2` W/K^1.2 | Current radiator constant |
| `COP_EFFICIENCY` | `0.55` | Carnot efficiency factor (η) |
| `T_LIFT` | `5.0` K | Temperature lift: radiator flow → HP condenser |
| `VF_FIXED` | `20 l/min` | Fixed flow rate assumed at high-flow operation |

To model different energy prices, recalculate the spark gap (`p_electricity / p_gas`) and update the break-even COP annotations in `plot_performance_vs_k()`.

### Printed output

Both scripts print a summary to stdout — flow temperatures, COPs, and required K values for each scenario — which can be redirected to a file:

```bash
python -m heat_pump_cost.radiator_analysis > results.txt
```


---

## Article 4: Quantitative Analysis of Dynamic Heat Pump Operation for Domestic Heating

**File:** [operations-dynamic.md](operations-dynamic.md)

Uses a first-order dynamic thermal model with parameters identified from recorded temperature data (C = 21.0 MJ/K, h = 142.6 W/K, τ = 40.9 h) to simulate four heating strategies for a January day (T_o = 5°C):

1. **Gas boiler** — traditional on/off control with morning and evening warm-up periods
2. **Simple thermostat heat pump** — mimics gas boiler operation, shows inefficiency of high flow temperatures
3. **Smooth continuous heat pump** — optimised continuous operation with baseline heating, achieves 19% cheaper than gas
4. **Tariff-optimized heat pump** — exploits Octopus Cosy dynamic pricing by pre-heating during cheap periods

Demonstrates that control strategy is critical: same hardware ranges from 29% more expensive than gas (simple thermostat) to 19% cheaper (smooth continuous operation).

### CLI Commands

#### 1. Parameter Identification

```bash
heat-pump-identify
```

Generates `assets/temperature_plot.png` showing model fit to recorded temperature data from three experimental periods (two cool-down periods and one heating period). Identifies thermal parameters C, h, Q_b using MAP estimation.

#### 2. Gas Boiler Simulation

```bash
heat-pump-gas-boiler
```

Simulates traditional gas boiler operation with schedule:
- 22:00–06:00: OFF (house cools)
- 06:00–09:00: 19°C comfort
- 09:00–17:00: OFF (house cools)
- 17:00–22:00: 19°C comfort

**Results:** 33.2 kWh/day heat, 35.0 kWh/day gas, £2.42/day (gas energy + gas SC)

**Equivalent heat pump (same heating pattern):** 11.2 kWh/day electricity, SCOP 2.96, £3.11/day (29% more expensive, demonstrating why heat pumps shouldn't mimic gas boiler operation)

**Outputs:**
- `assets/gas_boiler_simulation.png` — temperature and power profiles
- `assets/heat_pump_cop_simulation.png` — equivalent heat pump COP analysis

#### 3. Smooth Continuous Heat Pump

```bash
heat-pump-smooth
```

Simulates optimised continuous operation:
- Baseline 800W heating during night/away periods
- Maintains 17–19°C throughout
- Max flow temperature 45°C
- Predictive control with 3-hour lookahead

**Results:** 36.7 kWh/day heat, 7.1 kWh/day electricity, SCOP 5.18, £1.96/day (19% cheaper than gas)

**Outputs:**
- `assets/smooth_heat_pump_operation.png` — temperature and power profiles
- `assets/smooth_heat_pump_cop.png` — flow temperature and COP profiles

#### 4. Tariff-Optimized Heat Pump

```bash
heat-pump-tariff
```

Simulates cost optimization for Octopus Cosy dynamic tariff:
- Cheap periods (14.53p): pre-heating with flow temperatures up to 38–41°C (capped at 55°C)
- Peak period (51.68p): minimal heating, coast on stored energy
- Day periods (33.28p): moderate operation

**Results:** 41.3 kWh/day heat, 8.5 kWh/day electricity, SCOP 4.85, £2.15/day
- Saves £0.20/day vs flat tariff operation (£30/year)
- 11% cheaper than gas (£2.42/day), and saves £30/year vs running the same strategy on a flat tariff

**Outputs:**
- `assets/octopus_cosy_tariff.png` — tariff structure visualization
- `assets/tariff_optimized_operation.png` — temperature and power profiles
- `assets/tariff_optimized_cop.png` — flow temperature and COP profiles

### Key Parameters

All identified from April 2026 experiments:

| Parameter | Value | Description |
|---|---|---|
| `C` | 21.0 MJ/K | House thermal capacity |
| `h` | 142.6 W/K | Heat transfer coefficient |
| `Q_b` | 500 W | Background heat (appliances, occupancy) |
| `τ` | 40.9 hours | Thermal time constant (C/h) |
| `K` | 71.2 W/K^1.2 | Radiator constant |
| `n` | 1.2 | Radiator exponent |

### Energy Prices (January 2026)

- **Gas:** 5.93p/kWh + 35.09p/day standing charge
- **Electricity (flat):** 27.69p/kWh + 54.75p/day standing charge
- **Octopus Cosy:** 14.53p (cheap), 33.28p (day), 51.68p (peak 16:00–19:00)

Electricity standing charges are excluded from all scenarios (all households pay this regardless of heating method). Gas standing charge is included for the gas boiler scenario only, as it would not apply to heat pump households.

---

## Article 5: Quantitative Analysis of Dynamic Heat Pump Operation for Design Temperature

**File:** [operations-design.md](operations-design.md)

Extends the dynamic thermal model to design temperature conditions (T_o = −2°C) using a feedforward optimiser that plans 24-hour heating schedules. Compares:

1. **Smooth operation** — continuous heating with optimised power ramping for comfort periods
2. **Interrupted operation** — realistic operation with DHW slots (2 hours/day) and defrost cycles (10 min/hour)

Each scenario is evaluated with current radiators (K = 71.2 W/K^1.2) and upgraded radiators (K = 93.5 W/K^1.2).

### CLI Command

```bash
heat-pump-design
```

or as a module:

```bash
python -m heat_pump_cost.simulate_design_temperature
```

**Results:**

**Smooth operation (heating only):**
- Current radiators: 60.0 kWh/day heat, 16.4 kWh/day electricity, SCOP 3.66, £4.55/day (vs gas £4.10/day)
- Upgraded radiators: 60.0 kWh/day heat, 15.1 kWh/day electricity, SCOP 3.96, £4.19/day (vs gas £4.10/day)

**Interrupted operation (with DHW + defrost):**
- Current radiators: 59.1 kWh/day space heat, 17.6 kWh/day electricity (space), SCOP 3.36, £4.88/day (vs gas £4.04/day)
- Upgraded radiators: 59.1 kWh/day space heat, 16.1 kWh/day electricity (space), SCOP 3.67, £4.47/day (vs gas £4.04/day)

**Key findings:**
- At design temperature (−2°C), heat pump costs more than gas regardless of radiator upgrade due to spark gap
- Break-even spark gap: 3.36 (current radiators) or 3.67 (upgraded radiators)
- With ~10 design-temperature days/year, radiator upgrade payback is ~490 years at design conditions
- But during typical winter months (5°C), heat pump is 19% cheaper, making the overall economics favourable

**Outputs:**
- `assets/design_heating_profile.png` — temperature and power profiles (smooth operation, current radiators)
- `assets/design_flow_temperature_cop.png` — flow temperature and COP profiles (smooth operation, current radiators)
- `assets/design_flow_temperature_cop_upgrade.png` — flow temperature and COP profiles (smooth operation, upgraded radiators)
- `assets/design_heating_profile_with_gaps.png` — temperature and power profiles (interrupted operation, current radiators)
- `assets/design_flow_temperature_cop_gaps.png` — flow temperature and COP profiles (interrupted operation, current radiators)
- `assets/design_flow_temperature_cop_gaps_upgrade.png` — flow temperature and COP profiles (interrupted operation, upgraded radiators)

### Optimisation Strategy

The feedforward planner optimises hourly power levels to:
- **Pre-heat before comfort periods:** Ramp up power 2 hours before morning (06:00) and evening (17:00) schedules, reaching peak power ~5.5–6 kW
- **Maintain comfort efficiently:** Once 19°C is achieved, reduce to ~3 kW to hold temperature
- **Setback periods:** Deliver steady baseline heating ~2 kW to maintain ~17°C

This approach minimises flow temperatures (peaks at 57–58°C with current radiators) while achieving comfort. Other optimisation strategies (MPC, rule-based, ML) are possible—it's all software.

### DHW and Defrost Model

**DHW slots (4 per day):**
- 04:00–04:40 and 07:00–07:20 (morning routine)
- 15:00–15:40 and 18:00–18:20 (evening routine)
- Total: ~2 hours/day at 55°C flow temperature, COP 2.96

**Defrost cycles:**
- 10 minutes every hour outside DHW slots (~17% downtime)
- Heat pump unavailable for space heating during defrost

The optimiser plans around these interruptions to maintain comfort.

---

---

## Article 6: Quantitative Analysis of Heat Pump Operation for Domestic Hot Water

**File:** [domestic-hot-water.md](domestic-hot-water.md)

Analyses the economics of using a heat pump for domestic hot water (DHW) production at 55°C flow temperature. Shows that whilst heat pump DHW is 20% more expensive than gas on an energy-only basis at current UK spark gap (4.67), a spark gap of only 3.11 would achieve break-even even at the design temperature of −2°C.

### Generate the plots

**Daily cost and spark gap plots:**

```bash
python -m heat_pump_cost.plot_dhw_cost
```

Generates two plots:
- `assets/hot_water_cost.png` — Daily DHW cost (£/day) and COP vs outdoor temperature
- `assets/hot_water_spark_gap.png` — Required spark gap for break-even vs outdoor temperature

**Annual cost analysis:**

```bash
python -m heat_pump_cost.analyze_annual_dhw
```

Analyses full year of Cambridge 2025 hourly temperature data with realistic DHW schedule (100 l at 04:00, 100 l at 15:00). Generates:
- `assets/annual_dhw_cost.png` — Daily DHW costs throughout 2025
- Console output with annual totals and both scenarios

### Key Results

**Daily cost (200 l/day, 10°C → 55°C):**
- Gas boiler: 65.5p/day (95% efficiency, 5.93p/kWh)
- Heat pump: varies with outdoor temperature (0.6–1.0 £/day)
- Break-even: 18.6°C outdoor temperature, COP 4.44

**Annual costs (Cambridge 2025, avg T_o = 10.3°C, avg COP = 3.77):**
- Heat pump: £288/year (electricity)
- Gas boiler: £239/year (energy only)
- Difference: £49/year more expensive (+20%)

**Required spark gap for break-even:**
- At design temperature (−2°C, COP 2.96): 3.11
- At annual average (10.3°C, COP 3.77): 3.56
- Current UK spark gap: 4.67 (too high for economic viability)

The analysis demonstrates that the UK's high spark gap is a policy barrier rather than a physical constraint—many European countries operate with spark gaps below 3, making heat pump DHW economically viable year-round.

---

## Summary of CLI Tools

| Command | Article | Purpose |
|---|---|---|
| `heat-pump-cost` | 1 | Capital and lifecycle cost optimization plots |
| `heat-pump-operations` | 3 | Steady-state operations contour plot |
| `heat-pump-identify` | 4 | Thermal parameter identification plot |
| `heat-pump-gas-boiler` | 4 | Gas boiler baseline simulation |
| `heat-pump-smooth` | 4 | Smooth continuous heat pump operation |
| `heat-pump-tariff` | 4 | Tariff-optimized heat pump operation |
| `heat-pump-design` | 5 | Design temperature (−2°C) analysis |

**Module-only tools (no CLI):**
- `python -m heat_pump_cost.plot_dhw_cost` (Article 6) — DHW daily cost and spark gap plots
- `python -m heat_pump_cost.analyze_annual_dhw` (Article 6) — Annual DHW cost analysis
| `heat-pump-design` | 5 | Design temperature (−2°C) analysis |