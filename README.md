# Heat Pump Cost Analysis

Analysis tool for optimising the balance between heat pump and insulation investments.

## Project Structure

```
heat-pump-cost/
├── data/
│   ├── heat-pump-ratings.csv      # Heat pump specifications and costs
│   └── home-improvements.csv       # Insulation improvement options
├── src/
│   └── heat_pump_cost/
│       ├── __init__.py
│       ├── __main__.py             # Module entry point
│       ├── cli.py                  # Command-line interface
│       ├── cost_calculator.py      # CostCalculator class
│       ├── plotter.py              # Plotting utilities
│       └── plot_cost_analysis.py   # Main analysis script
├── article.md                      # Detailed analysis article
└── pyproject.toml                  # Project configuration
```

## Installation

```bash
# Install the package in editable mode
pip install -e .
```

## Usage

### Run with default settings

```bash
# Using the installed console script
heat-pump-cost

# Or as a Python module
python -m heat_pump_cost
```

### CLI Options

```bash
# Show help
heat-pump-cost --help

# Specify custom initial heat loss
heat-pump-cost --initial-heat-loss 20000

# Use custom data files
heat-pump-cost \
  --heat-pumps data/my-heat-pumps.csv \
  --improvements data/my-improvements.csv

# Specify output directory
heat-pump-cost --output-dir results/

# Custom electricity rate (20p/kWh)
heat-pump-cost --electricity-rate 0.20
```

## Output

The analysis generates 4 plots:

### Capital Costs Only (Installation costs)
1. `heat_pump_1_no_grant_capital_only.png` - No grant scenario
2. `heat_pump_2_with_grant_capital_only.png` - With £7,500 grant

### Total Lifecycle Costs (Capital + Runtime, 25 years)
3. `heat_pump_4_no_grant_with_runtime.png` - No grant + 25 years runtime
4. `heat_pump_5_with_grant_with_runtime.png` - With £7,500 grant + 25 years runtime

## Data Files

### heat-pump-ratings.csv

CSV file with heat pump specifications:
- `capacity_kw`: Heat pump capacity in kW
- `property_type`: Property size category
- `heat_demand_kwh`: Typical annual heat demand in kWh
- `electricity_use_kwh`: Estimated annual electricity consumption in kWh
- `cost_gbp`: Installation cost in £

### home-improvements.csv

CSV file with insulation improvement options:
- `description`: Name of the improvement
- `cost_gbp`: Cost in £
- `heat_loss_reduction_watt`: Heat loss reduction in Watts at design conditions (21°C inside, 2°C outside)

## Key Findings

The analysis reveals:

1. **Without runtime costs**: Optimal strategy is minimal insulation (loft and bay window) reducing heat loss to 13,333 kWh/year for £350.
   - No grant: £13,223 total
   - With £7,500 grant: £5,723 total

2. **With runtime costs over 25 years**: Optimal point shifts to 12,901 kWh/year (£928 insulation), making additional insulation investment economically beneficial.
   - No grant: £28,523 total
   - With £7,500 grant: £21,023 total

3. **Runtime costs dominate**: Over a 25-year lifecycle, runtime costs represent 52-71% of total costs, fundamentally changing the optimisation equation.

4. **Government grant impact**: The £7,500 grant significantly reduces upfront costs (from £13,223 to £5,723) but doesn't change the optimal insulation level when considering capital costs alone.

5. **Empirical conversion factor**: Heat loss reduction in Watts (at design conditions) is converted to annual kWh using an empirical factor of 2.78, derived from real-world data (9,000 W design → 25,000 kWh/year actual).

## Development

### Code Structure

- **CostCalculator**: Core calculation engine that reads data from CSV files and computes optimal costs
- **CostPlotter**: Plotting utilities for visualizing results
- **CLI**: Command-line interface for running analyses with custom parameters

### Extending the Analysis

To add new scenarios:

```python
from cost_calculator import CostCalculator
from plotter import CostPlotter

calculator = CostCalculator(
    initial_heat_loss=25000,
    heat_pumps_csv="data/heat-pump-ratings.csv",
    improvements_csv="data/home-improvements.csv"
)

result = calculator.calculate_total_cost(
    num_heat_pumps=3,
    heat_pump_grants=[7500, 5000, 0],
    runtime_years=75,
    electricity_rate=0.20
)

plotter = CostPlotter(result)
plotter.save_plot("custom_analysis.png")
```

## License

See project documentation for details.
