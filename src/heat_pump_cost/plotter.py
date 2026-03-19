"""Plotting utilities for heat pump cost analysis."""

import matplotlib.pyplot as plt
import numpy as np
from typing import Dict


class CostPlotter:
    """Create plots for cost analysis results."""
    
    def __init__(self, calculator_result: Dict):
        """Initialize plotter with calculator results.
        
        Args:
            calculator_result: Dictionary from CostCalculator.calculate_total_cost()
        """
        self.result = calculator_result
    
    def create_plot(self, ax=None, title_suffix="") -> plt.Figure:
        """Create a cost analysis plot.
        
        Args:
            ax: Matplotlib axis to plot on (if None, creates new figure)
            title_suffix: Additional text to add to the title
            
        Returns:
            Matplotlib figure object
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(12, 8))
        else:
            fig = ax.figure
        
        # Unpack results
        heat_loss = self.result['heat_loss_values']
        insulation_cost = self.result['insulation_cost_values']
        improvement_names = self.result['improvement_names']
        heat_loss_range = self.result['heat_loss_range']
        total_costs = self.result['total_cost_curve']
        insulation_fit = self.result['insulation_fit']
        hp_fit = self.result['hp_fit']
        hp_arrays = self.result['hp_arrays']
        min_heat_loss = self.result['min_heat_loss']
        min_total_cost = self.result['min_total_cost']
        num_heat_pumps = self.result['num_heat_pumps']
        total_grants = self.result['total_grants']
        runtime_years = self.result['runtime_years']
        
        # Plot insulation improvements
        ax.plot(heat_loss, insulation_cost, 'o-', 
                label='Insulation improvements', 
                color='blue', linewidth=2, markersize=8)
        
        # Plot insulation fit curve
        heat_loss_fine = np.linspace(min(heat_loss), max(heat_loss), 200)
        if len(heat_loss) > 2:
            insulation_cost_fine = np.maximum(0, insulation_fit(heat_loss_fine))  # Ensure non-negative
            ax.plot(heat_loss_fine, insulation_cost_fine, '--', 
                    color='blue', alpha=0.5, linewidth=1,
                    label='Insulation cost trend')
        
        # Calculate heat pump costs for display
        runtime_years_val = runtime_years if runtime_years > 0 else 0
        hp_cost_lifecycle = hp_arrays['cost'] * num_heat_pumps - total_grants
        
        if runtime_years > 0:
            hp_runtime_annual = hp_arrays['electricity'] * self.result['electricity_rate']
            hp_runtime_total = hp_runtime_annual * runtime_years
            hp_cost_with_runtime = hp_cost_lifecycle + hp_runtime_total
        else:
            hp_cost_with_runtime = hp_cost_lifecycle
        
        # Plot heat pump costs
        if runtime_years > 0:
            if num_heat_pumps > 1:
                grant_label = f" ({num_heat_pumps} pumps, £{total_grants:,} grant, {runtime_years}yr runtime)"
            elif total_grants > 0:
                grant_label = f" (£{total_grants:,} grant, {runtime_years}yr runtime)"
            else:
                grant_label = f" ({runtime_years}yr runtime)"
        else:
            if num_heat_pumps > 1:
                grant_label = f" ({num_heat_pumps} pumps, £{total_grants:,} total grant)"
            elif total_grants > 0:
                grant_label = f" (with £{total_grants:,} grant)"
            else:
                grant_label = ""
        
        ax.plot(hp_arrays['demand'], hp_cost_with_runtime, 's-', 
                label=f'Heat pump cost{grant_label}', 
                color='red', linewidth=2, markersize=8)
        
        # Plot heat pump fit curve
        hp_demand_fine = np.linspace(min(hp_arrays['demand']), max(hp_arrays['demand']) + 2000, 200)
        hp_cost_fine = hp_fit(hp_demand_fine)
        ax.plot(hp_demand_fine, hp_cost_fine, '--', 
                color='red', alpha=0.5, linewidth=1,
                label='Heat pump cost trend')
        
        # Plot total cost
        ax.plot(heat_loss_range, total_costs, '-', 
                label='Total cost (Insulation + Heat Pump)', 
                color='green', linewidth=3, alpha=0.7)
        
        # Find and mark the minimum total cost
        ax.plot(min_heat_loss, min_total_cost, 'g*', 
                markersize=20, label=f'Optimal: {min_heat_loss:.0f} kWh, £{min_total_cost:.0f}')
        
        # Add annotation for optimal point
        ax.annotate(f'Optimal Point\n{min_heat_loss:.0f} kWh\n£{min_total_cost:.0f}',
                    xy=(min_heat_loss, min_total_cost),
                    xytext=(0, 80), textcoords='offset points',
                    arrowprops=dict(arrowstyle='->', color='green', lw=2),
                    fontsize=11, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7))
        
        # Annotate home improvements with varied positioning for better readability
        # Define offset patterns that follow the curve progression with minimal y offset
        offset_patterns = [
            (120, 10),   # First improvement (loft) - right, minimal up
            (120, 20),   # Second (bay window) - right, slightly up
            (120, 30),   # Third (entrance glazing) - right, a bit more up
            (120, 40),   # Fourth (ground floor) - right, continuing up
            (120, 50),   # Fifth (render) - right, slightly higher
            (30, 5),     # Sixth (external wall) - small x offset, minimal up
            (30, 5),     # Seventh (triple glazing) - small x offset, minimal up
        ]
        
        for i, name in enumerate(improvement_names):
            if i > 0:  # Skip "Start" as it's at the starting point
                # Use cycling offset pattern
                offset_idx = (i - 1) % len(offset_patterns)
                offset = offset_patterns[offset_idx]
                
                ax.annotate(name.title(), 
                           xy=(heat_loss[i], insulation_cost[i]),
                           xytext=offset, textcoords='offset points',
                           fontsize=8, alpha=0.7,
                           arrowprops=dict(arrowstyle='->', lw=0.5, alpha=0.5, color='blue'))
        
        # Annotate heat pumps
        if 'property_types' in hp_arrays:
            for i, prop_type in enumerate(hp_arrays['property_types']):
                ax.annotate(f"{prop_type}\n{hp_arrays['capacity'][i]:.1f} kW", 
                           xy=(hp_arrays['demand'][i], hp_cost_with_runtime[i]),
                           xytext=(10, -15), textcoords='offset points',
                           fontsize=8, alpha=0.7, color='darkred')
        
        # Labels and title
        ax.set_xlabel('Heat Loss / Heat Demand (kWh/year)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Cost (£)', fontsize=12, fontweight='bold')
        
        title_base = 'Heat Pump vs Insulation Cost Optimization\n' + \
                     'Finding the Optimal Balance for a 1930s Semi-Detached House'
        if title_suffix:
            title_base += f'\n{title_suffix}'
        
        ax.set_title(title_base, fontsize=14, fontweight='bold')
        ax.legend(fontsize=10, loc='best')
        ax.grid(True, alpha=0.3)
        
        return fig
    
    def save_plot(self, filename: str, dpi: int = 300):
        """Save the plot to a file.
        
        Args:
            filename: Output filename (can include path)
            dpi: Resolution in dots per inch
        """
        from pathlib import Path
        
        # Ensure directory exists
        output_path = Path(filename)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        fig = self.create_plot()
        fig.tight_layout()
        fig.savefig(str(output_path), dpi=dpi, bbox_inches='tight')
        plt.close(fig)


def print_summary(result: Dict, title: str = "ANALYSIS SUMMARY"):
    """Print a summary of the cost analysis results.
    
    Args:
        result: Dictionary from CostCalculator.calculate_total_cost()
        title: Title for the summary section
    """
    print("="*60)
    print(title)
    print("="*60)
    print(f"\nInitial heat loss: {result['initial_heat_loss']:,} kWh/year")
    print(f"Optimal heat loss: {result['min_heat_loss']:.0f} kWh/year")
    print(f"Heat loss reduction: {result['initial_heat_loss'] - result['min_heat_loss']:.0f} kWh/year")
    print(f"\nInsulation cost: £{result['insulation_cost']:.0f}")
    print(f"Number of heat pumps: {result['num_heat_pumps']}")
    print(f"Heat pump cost (single unit): £{result['hp_cost_single']:.0f}")
    
    if result['num_heat_pumps'] > 1:
        print(f"Total heat pump cost before grants: £{result['hp_cost_single'] * result['num_heat_pumps']:.0f}")
    
    print(f"Government grants: £{result['total_grants']:.0f}")
    print(f"Heat pump capital cost after grants: £{result['hp_cost_capital_only']:.0f}")
    
    if result['runtime_years'] > 0:
        print(f"\nRuntime period: {result['runtime_years']} years")
        print(f"Electricity rate: £{result['electricity_rate']:.2f}/kWh")
        print(f"Annual electricity consumption: {result['annual_electricity_kwh']:.0f} kWh")
        print(f"Annual electricity cost: £{result['annual_electricity_kwh'] * result['electricity_rate']:.0f}")
        print(f"Total runtime cost: £{result['runtime_cost']:.0f}")
        print(f"Runtime as % of total: {100 * result['runtime_cost'] / result['min_total_cost']:.1f}%")
    
    print(f"\nTOTAL COST: £{result['min_total_cost']:.0f}")
    print("="*60)


def print_comparative_summary(results: list, labels: list, title: str = "COMPARATIVE SUMMARY"):
    """Print a comparative summary of multiple analyses.
    
    Args:
        results: List of result dictionaries
        labels: List of labels for each result
        title: Title for the summary
    """
    print("\n" + "="*90)
    print(title)
    print("="*90)
    
    # Column widths
    metric_width = 50
    col_width = 15
    
    # Header
    header = f"\n{'Metric':<{metric_width}}"
    for label in labels:
        header += f" {label:<{col_width}}"
    print(header)
    print("-"*90)
    
    # Initial heat loss
    row = f"{'Initial heat loss (kWh/year)':<{metric_width}}"
    for result in results:
        row += f" {result['initial_heat_loss']:>{col_width},}"
    print(row)
    
    # Optimal heat loss
    row = f"{'Optimal heat loss (kWh/year)':<{metric_width}}"
    for result in results:
        row += f" {result['min_heat_loss']:>{col_width}.0f}"
    print(row)
    
    # Heat loss reduction
    row = f"{'Heat loss reduction (kWh/year)':<{metric_width}}"
    for result in results:
        row += f" {result['initial_heat_loss'] - result['min_heat_loss']:>{col_width}.0f}"
    print(row)
    
    print()
    print(f"{'CAPITAL COSTS:':<{metric_width}}")
    
    # Insulation cost
    row = f"{'Insulation cost (£)':<{metric_width}}"
    for result in results:
        row += f" {result['insulation_cost']:>{col_width}.0f}"
    print(row)
    
    # Number of heat pumps
    row = f"{'Number of heat pumps':<{metric_width}}"
    for result in results:
        row += f" {result['num_heat_pumps']:>{col_width}}"
    print(row)
    
    # Capital costs
    row = f"{'Heat pump capital cost after grants (£)':<{metric_width}}"
    for result in results:
        row += f" {result['hp_cost_capital_only']:>{col_width}.0f}"
    print(row)
    
    # Runtime costs if applicable
    if any(r['runtime_years'] > 0 for r in results):
        print()
        print(f"RUNTIME COSTS (@ {results[0]['electricity_rate']:.2f}£/kWh):")
        
        row = f"{'Runtime period (years)':<{metric_width}}"
        for result in results:
            row += f" {result['runtime_years']:>{col_width}}"
        print(row)
        
        row = f"{'Total runtime cost (£)':<{metric_width}}"
        for result in results:
            row += f" {result['runtime_cost']:>{col_width}.0f}"
        print(row)
    
    print()
    # Total cost
    row = f"{'TOTAL COST (£)':<{metric_width}}"
    for result in results:
        row += f" {result['min_total_cost']:>{col_width}.0f}"
    print(row)
    
    print("-"*90)
    
    # Savings vs first scenario
    row = f"{'Savings vs ' + labels[0] + ' (£)':<{metric_width}}"
    for i, result in enumerate(results):
        if i == 0:
            row += f" {'—':>{col_width}}"
        else:
            row += f" {results[0]['min_total_cost'] - result['min_total_cost']:>{col_width}.0f}"
    print(row)
    
    print("="*90)
