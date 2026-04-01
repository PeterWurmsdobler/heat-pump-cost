# Heat Pump Cost Analysis

A collection of quantitative analyses — each backed by Python models — exploring the economics and practicalities of installing an air-source heat pump in a 1930s UK semi-detached house. Three articles are supported:

1. **[Considerations for the Fabric First vs Heat Pump First Debate](considerations.md)** — capital and lifecycle cost optimisation across insulation and heat pump options.
2. **[Impediments to UK Heat Pump Adoption and Possible Solutions](impediments.md)** — qualitative analysis of capital cost, space requirements, and the spark gap.
3. **[How the Spark Gap Drives the Radiator Upgrades for a Heat Pump Installation](operations-static.md)** — steady-state thermal modelling of flow temperature, COP, and required radiator capacity.

## Project Structure

```
heat-pump-cost/
├── data/
│   ├── heat-pump-ratings.csv        # Heat pump specifications and costs
│   └── home-improvements.csv        # Insulation improvement options
├── src/
│   └── heat_pump_cost/
│       ├── __init__.py
│       ├── __main__.py              # Module entry point
│       ├── cli.py                   # CLI for considerations analysis
│       ├── cost_calculator.py       # Capital + runtime cost optimisation
│       ├── plot_cost_analysis.py    # Generates considerations plots
│       ├── plotter.py               # Shared plotting utilities
│       ├── operations_model.py      # Steady-state heat flow model + contour plots
│       └── radiator_analysis.py     # COP vs power/K plots
├── assets/                          # Generated plots (committed)
├── considerations.md
├── impediments.md
├── operations-static.md
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

Uses a steady-state lumped-mass thermal model, empirically calibrated from January 2026 bills (K = 44.9 W/K^1.2), to show how the spark gap (currently 4.67) sets the minimum COP threshold and thereby the required flow temperature and radiator capacity for three heating load scenarios.

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
| `K_RAD` | `44.9` W/K^1.2 | Empirical radiator constant |
| `N_RAD` | `1.2` | Radiator exponent |
| `Q_TARGET` | `1960.0` W | Average radiator power (from bills) |

**`src/heat_pump_cost/radiator_analysis.py`**

| Constant | Default | Description |
|---|---|---|
| `K_CURRENT` | `44.9` W/K^1.2 | Current radiator constant |
| `COP_EFFICIENCY` | `0.55` | Carnot efficiency factor (η) |
| `T_LIFT` | `5.0` K | Temperature lift: radiator flow → HP condenser |
| `VF_FIXED` | `20 l/min` | Fixed flow rate assumed at high-flow operation |

To model different energy prices, recalculate the spark gap (`p_electricity / p_gas`) and update the break-even COP annotations in `plot_performance_vs_k()`.

### Printed output

Both scripts print a summary to stdout — flow temperatures, COPs, and required K values for each scenario — which can be redirected to a file:

```bash
python -m heat_pump_cost.radiator_analysis > results.txt
```
