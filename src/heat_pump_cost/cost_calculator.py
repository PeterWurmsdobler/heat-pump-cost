"""Cost calculator for heat pump and insulation analysis."""

import csv
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
from scipy.optimize import curve_fit


class CostCalculator:
    """Calculate optimal costs for heat pump and insulation investments.
    
    Constants:
        DESIGN_HEAT_LOSS_KW: Initial design heating power in kW (21°C inside, 2°C outside)
        IMPROVED_HEAT_LOSS_KW: Heating power after improvements (except last two)
        ACTUAL_ANNUAL_KWH: Actual measured annual heating consumption in kWh/year
        KW_TO_KWH_YEAR: Empirical conversion factor from heating power to annual energy (≈2790)
        MIN_HEAT_LOSS_KW: Minimum heating power (hot water, ventilation, etc.)
    """
    
    # Empirical conversion factor: 4.3 kW heating power → 12000 kWh/year actual
    DESIGN_HEAT_LOSS_KW = 9.0  # Initial heating power without improvements
    IMPROVED_HEAT_LOSS_KW = 4.3  # After all improvements except external wall & triple glazing
    ACTUAL_ANNUAL_KWH = 12000  # Actual measured annual heat energy consumption
    KW_TO_KWH_YEAR = ACTUAL_ANNUAL_KWH / IMPROVED_HEAT_LOSS_KW  # ≈ 2790 kWh/kW (thermal)
    SCOP = 4.0  # Seasonal Coefficient of Performance (heat output / electricity input)
    MIN_HEAT_LOSS_KW = 1.0  # Minimum heating power (hot water, ventilation, etc.)
    
    def __init__(self, initial_heat_loss: float, 
                 heat_pumps_csv: str, 
                 improvements_csv: str):
        """Initialize the cost calculator.
        
        Args:
            initial_heat_loss: Initial heating power in kW
            heat_pumps_csv: Path to heat pump ratings CSV file
            improvements_csv: Path to home improvements CSV file
        """
        self.initial_heat_loss = initial_heat_loss
        self.heat_pumps = self._load_heat_pumps(heat_pumps_csv)
        self.improvements = self._load_improvements(improvements_csv)
        
    def _load_heat_pumps(self, csv_path: str) -> List[Dict]:
        """Load heat pump data from CSV file."""
        heat_pumps = []
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                heat_pumps.append({
                    'capacity_kw': float(row['capacity_kw']),
                    'property_type': row['property_type'],
                    'cost_gbp': float(row['cost_gbp'])
                })
        return heat_pumps
    
    def _load_improvements(self, csv_path: str) -> List[Dict]:
        """Load home improvement data from CSV file and sort by cost-effectiveness.
        
        Reads heat loss reduction in Watts (at design conditions: 21°C inside, 2°C outside),
        converts to kW, and sorts by heat reduction per pound.
        """
        improvements = []
        
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert Watts to kW
                heat_reduction_w = float(row['heat_loss_reduction_watt'])
                heat_reduction_kw = heat_reduction_w / 1000.0
                
                improvements.append({
                    'description': row['description'],
                    'cost_gbp': float(row['cost_gbp']),
                    'heat_reduction_kw': heat_reduction_kw,
                    'cost_effectiveness': heat_reduction_w / float(row['cost_gbp'])
                })
        
        # Sort by cost-effectiveness (W per £) in descending order
        improvements.sort(key=lambda x: x['cost_effectiveness'], reverse=True)
        return improvements
    
    def calculate_insulation_costs(self) -> Tuple[List[float], List[float]]:
        """Calculate accumulated insulation costs and remaining heating power.
        
        Ensures heating power doesn't go below 1.0 kW (minimum for hot water).
        
        Returns:
            Tuple of (heating_power_values, insulation_cost_values) in kW
        """
        heating_power = [self.initial_heat_loss]
        insulation_cost = [0]
        
        cumulative_cost = 0
        cumulative_reduction = 0
        
        for improvement in self.improvements:
            cumulative_cost += improvement['cost_gbp']
            cumulative_reduction += improvement['heat_reduction_kw']
            
            # Ensure we don't reduce heating power below minimum
            remaining_power = max(self.MIN_HEAT_LOSS_KW, 
                                     self.initial_heat_loss - cumulative_reduction)
            
            # Stop if we've already reached minimum heating power
            if heating_power[-1] <= self.MIN_HEAT_LOSS_KW:
                break
                
            insulation_cost.append(cumulative_cost)
            heating_power.append(remaining_power)
        
        return heating_power, insulation_cost
    
    def get_heat_pump_arrays(self) -> Dict[str, np.ndarray]:
        """Get heat pump data as numpy arrays.
        
        Uses the capacity (kW) as the matching criterion for heating power.
        Estimates annual electricity consumption using the empirical ratio and SCOP.
        
        Returns:
            Dictionary with capacities, costs, electricity use arrays, and property types
        """
        hp_capacity = np.array([hp['capacity_kw'] for hp in self.heat_pumps])
        hp_cost = np.array([hp['cost_gbp'] for hp in self.heat_pumps])
        # Calculate annual electricity from heating power using empirical ratio divided by SCOP
        # Heat demand (thermal) = capacity * KW_TO_KWH_YEAR
        # Electricity demand = heat demand / SCOP
        hp_electricity = hp_capacity * self.KW_TO_KWH_YEAR / self.SCOP
        hp_property_types = [hp['property_type'] for hp in self.heat_pumps]
        
        return {
            'capacity': hp_capacity,
            'cost': hp_cost,
            'electricity': hp_electricity,
            'property_types': hp_property_types
        }
    
    def calculate_total_cost(self, 
                            num_heat_pumps: int = 1,
                            heat_pump_grants: List[float] = None,
                            runtime_years: int = 0,
                            electricity_rate: float = 0.15) -> Dict:
        """Calculate total costs over lifecycle.
        
        Args:
            num_heat_pumps: Number of heat pump replacements
            heat_pump_grants: List of grants for each heat pump
            runtime_years: Years of operation to include runtime costs
            electricity_rate: Cost per kWh in £
            
        Returns:
            Dictionary with cost analysis results
        """
        if heat_pump_grants is None:
            heat_pump_grants = [0] * num_heat_pumps
        
        heating_power, insulation_cost = self.calculate_insulation_costs()
        hp_arrays = self.get_heat_pump_arrays()
        
        # Calculate heat pump lifecycle costs
        total_grants = sum(heat_pump_grants[:num_heat_pumps])
        hp_cost_lifecycle = hp_arrays['cost'] * num_heat_pumps - total_grants
        
        # Calculate runtime costs if specified
        if runtime_years > 0:
            hp_runtime_annual = hp_arrays['electricity'] * electricity_rate
            hp_runtime_total = hp_runtime_annual * runtime_years
            hp_cost_with_runtime = hp_cost_lifecycle + hp_runtime_total
        else:
            hp_cost_with_runtime = hp_cost_lifecycle
            hp_runtime_total = np.zeros_like(hp_arrays['cost'])
        
        # Fit curves
        insulation_cost_array = np.array(insulation_cost[1:])
        heating_power_array = np.array(heating_power[1:])
        
        # Insulation fit using power law: cost = a / heating_power^b + c
        # This ensures monotonic decreasing cost as heating power increases
        def power_law_func(x, a, b, c):
            return np.maximum(0, a / (x ** b) + c)  # Ensure non-negative
        
        try:
            # Fit with reasonable initial guesses and bounds to ensure positive result
            popt, _ = curve_fit(power_law_func, heating_power_array, insulation_cost_array,
                               p0=[1e5, 1.5, 0], maxfev=10000,
                               bounds=([0, 0, -1e5], [1e8, 5, 1e5]))
            insulation_fit = lambda x: np.maximum(0, power_law_func(x, *popt))
        except:
            # Fallback to polynomial fit if curve_fit fails
            insulation_coeffs = np.polyfit(1/heating_power_array, insulation_cost_array, 2)
            insulation_fit = lambda x: np.maximum(0, np.poly1d(insulation_coeffs)(1/x))
        
        # Heat pump fit (linear) - use capacity as x-axis
        hp_coeffs = np.polyfit(hp_arrays['capacity'], hp_cost_with_runtime, 1)
        hp_fit = np.poly1d(hp_coeffs)
        
        # Calculate total cost curve
        heating_power_range = np.linspace(min(heating_power), max(heating_power), 100)
        total_costs = []
        
        for hp in heating_power_range:
            ins_cost = np.interp(hp, heating_power[::-1], insulation_cost[::-1])
            hp_cost_val = hp_fit(hp)
            total_costs.append(ins_cost + hp_cost_val)
        
        # Find optimal point
        min_idx = np.argmin(total_costs)
        min_heating_power = heating_power_range[min_idx]
        min_total_cost = total_costs[min_idx]
        
        # Calculate runtime costs for optimal point
        if runtime_years > 0:
            # Electricity is proportional to heating power using KW_TO_KWH_YEAR / SCOP
            # Heat demand (thermal) = heating power * KW_TO_KWH_YEAR
            # Electricity demand = heat demand / SCOP
            optimal_electricity_annual = min_heating_power * self.KW_TO_KWH_YEAR / self.SCOP
            optimal_runtime_cost = optimal_electricity_annual * electricity_rate * runtime_years
        else:
            optimal_electricity_annual = 0
            optimal_runtime_cost = 0
        
        # Build improvement names list (Starting point + improvements)
        improvement_names = ['Start'] + [imp['description'] for imp in self.improvements]
        
        return {
            'min_heat_loss': min_heating_power,
            'min_total_cost': min_total_cost,
            'insulation_cost': np.interp(min_heating_power, heating_power[::-1], insulation_cost[::-1]),
            'hp_cost': hp_fit(min_heating_power),
            'hp_cost_single': np.interp(min_heating_power, hp_arrays['capacity'], hp_arrays['cost']),
            'hp_cost_capital_only': np.interp(min_heating_power, hp_arrays['capacity'], hp_arrays['cost']) * num_heat_pumps - total_grants,
            'runtime_cost': optimal_runtime_cost,
            'runtime_years': runtime_years,
            'electricity_rate': electricity_rate,
            'annual_electricity_kwh': optimal_electricity_annual,
            'total_grants': total_grants,
            'num_heat_pumps': num_heat_pumps,
            'initial_heat_loss': self.initial_heat_loss,
            'heat_loss_values': heating_power,
            'insulation_cost_values': insulation_cost,
            'improvement_names': improvement_names,
            'heat_loss_range': heating_power_range,
            'total_cost_curve': total_costs,
            'insulation_fit': insulation_fit,
            'hp_fit': hp_fit,
            'hp_arrays': hp_arrays
        }
