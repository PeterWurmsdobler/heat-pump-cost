"""
Cost analysis for heat pump and insulation improvements.

This script generates plots showing the relationship between:
1. Accumulated cost of insulation improvements vs remaining heat loss
2. Heat pump costs vs heat demand
3. The optimal combination (minimum total cost)
"""

from pathlib import Path

from heat_pump_cost.cost_calculator import CostCalculator
from heat_pump_cost.plotter import CostPlotter, print_summary, print_comparative_summary


def run_analysis(initial_heat_loss: float,
                heat_pumps_csv: str,
                improvements_csv: str,
                electricity_rate: float,
                output_dir: str):
    """Run the complete cost analysis and generate all plots.
    
    Args:
        initial_heat_loss: Initial annual heat loss in kWh
        heat_pumps_csv: Path to heat pump ratings CSV
        improvements_csv: Path to home improvements CSV
        electricity_rate: Electricity cost per kWh in £
        output_dir: Directory to save output plots
    """
    output_dir = Path(output_dir)
    
    # Initialize calculator
    calculator = CostCalculator(initial_heat_loss, str(heat_pumps_csv), str(improvements_csv))
    
    # ========================================================================
    # PART 1: CAPITAL COSTS ONLY (No Runtime Costs)
    # ========================================================================
    print("\n" + "="*70)
    print("PART 1: CAPITAL COSTS ONLY (Installation costs)")
    print("="*70)
    
    # Analysis 1a: Without grant - capital only
    print("\n" + "="*60)
    print("ANALYSIS 1a: WITHOUT GRANT (Capital costs only)")
    print("="*60)
    result1a = calculator.calculate_total_cost(
        num_heat_pumps=1,
        heat_pump_grants=[0],
        runtime_years=0
    )
    print_summary(result1a)
    
    # Analysis 2a: With £7,500 grant - capital only
    print("\n" + "="*60)
    print("ANALYSIS 2a: WITH £7,500 GRANT (Capital costs only)")
    print("="*60)
    result2a = calculator.calculate_total_cost(
        num_heat_pumps=1,
        heat_pump_grants=[7500],
        runtime_years=0
    )
    print_summary(result2a)
    
    # Analysis 3a: 50-year lifecycle - 2 heat pumps - capital only
    print("\n" + "="*60)
    print("ANALYSIS 3a: 50-YEAR LIFECYCLE (Capital costs only)")
    print("="*60)
    result3a = calculator.calculate_total_cost(
        num_heat_pumps=2,
        heat_pump_grants=[7500, 0],
        runtime_years=0
    )
    print_summary(result3a)
    
    # ========================================================================
    # PART 2: TOTAL LIFECYCLE COSTS (Capital + Runtime)
    # ========================================================================
    print("\n\n" + "="*70)
    print("PART 2: TOTAL LIFECYCLE COSTS (Capital + Runtime)")
    print("="*70)
    
    # Analysis 1b: Without grant + 25 years runtime
    print("\n" + "="*60)
    print("ANALYSIS 1b: WITHOUT GRANT + 25 YEARS RUNTIME")
    print("="*60)
    result1b = calculator.calculate_total_cost(
        num_heat_pumps=1,
        heat_pump_grants=[0],
        runtime_years=25,
        electricity_rate=electricity_rate
    )
    print_summary(result1b)
    
    # Analysis 2b: With £7,500 grant + 25 years runtime
    print("\n" + "="*60)
    print("ANALYSIS 2b: WITH £7,500 GRANT + 25 YEARS RUNTIME")
    print("="*60)
    result2b = calculator.calculate_total_cost(
        num_heat_pumps=1,
        heat_pump_grants=[7500],
        runtime_years=25,
        electricity_rate=electricity_rate
    )
    print_summary(result2b)
    
    # Analysis 3b: 50-year lifecycle - 2 heat pumps + 50 years runtime
    print("\n" + "="*60)
    print("ANALYSIS 3b: 50-YEAR LIFECYCLE + 50 YEARS RUNTIME")
    print("="*60)
    result3b = calculator.calculate_total_cost(
        num_heat_pumps=2,
        heat_pump_grants=[7500, 0],
        runtime_years=50,
        electricity_rate=electricity_rate
    )
    print_summary(result3b)
    
    # ========================================================================
    # Print comparative summaries
    # ========================================================================
    print_comparative_summary(
        [result1a, result2a, result3a],
        ["No Grant", "With Grant", "50-yr (2 HPs)"],
        "SUMMARY 1: CAPITAL COSTS ONLY"
    )
    
    print_comparative_summary(
        [result1b, result2b, result3b],
        ["No Grant", "With Grant", "50-yr (2 HPs)"],
        "SUMMARY 2: TOTAL LIFECYCLE COSTS (Capital + Runtime)"
    )
    
    # ========================================================================
    # Save all individual plots
    # ========================================================================
    print("\n\nSaving individual plot files...")
    
    # Capital only plots
    plotter = CostPlotter(result1a)
    plotter.save_plot(output_dir / 'heat_pump_1_no_grant_capital_only.png')
    
    plotter = CostPlotter(result2a)
    plotter.save_plot(output_dir / 'heat_pump_2_with_grant_capital_only.png')
    
    plotter = CostPlotter(result3a)
    plotter.save_plot(output_dir / 'heat_pump_3_50year_capital_only.png')
    
    # With runtime costs plots
    plotter = CostPlotter(result1b)
    plotter.save_plot(output_dir / 'heat_pump_4_no_grant_with_runtime.png')
    
    plotter = CostPlotter(result2b)
    plotter.save_plot(output_dir / 'heat_pump_5_with_grant_with_runtime.png')
    
    plotter = CostPlotter(result3b)
    plotter.save_plot(output_dir / 'heat_pump_6_50year_with_runtime.png')
    
    print(f"\nAll 6 plots saved to {output_dir}:")
    print(f"\nCapital costs only:")
    print(f"  - heat_pump_1_no_grant_capital_only.png")
    print(f"  - heat_pump_2_with_grant_capital_only.png")
    print(f"  - heat_pump_3_50year_capital_only.png")
    print(f"\nWith runtime costs:")
    print(f"  - heat_pump_4_no_grant_with_runtime.png")
    print(f"  - heat_pump_5_with_grant_with_runtime.png")
    print(f"  - heat_pump_6_50year_with_runtime.png")
