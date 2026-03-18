"""Cost calculator for heat pump and insulation analysis."""

import csv
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
from scipy.optimize import curve_fit


class CostCalculator:
    """Calculate optimal costs for heat pump and insulation investments.
    
    Constants:
        DESIGN_HEAT_LOSS_W: Design heat loss in Watts (21°C inside, 2°C outside)
        ACTUAL_ANNUAL_KWH: Actual annual heating consumption in kWh/year
        WATTS_TO_KWH_YEAR: Empirical conversion factor (≈2.778)
        MIN_HEAT_LOSS_KWH: Minimum heat loss (hot water, ventilation, etc.)
    """
    
    # Empirical conversion factor: 9000W design → 25000 kWh/year actual
    DESIGN_HEAT_LOSS_W = 9000
    ACTUAL_ANNUAL_KWH = 25000
    WATTS_TO_KWH_YEAR = ACTUAL_ANNUAL_KWH / DESIGN_HEAT_LOSS_W  # ≈ 2.778
    MIN_HEAT_LOSS_KWH = 1000  # Minimum heat loss (hot water, ventilation, etc.)
    
    def __init__(self, initial_heat_loss: float, 
                 heat_pumps_csv: str, 
                 improvements_csv: str):
        """Initialize the cost calculator.
        
        Args:
            initial_heat_loss: Initial annual heat loss in kWh
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
                    'heat_demand_kwh': float(row['heat_demand_kwh']),
                    'electricity_use_kwh': float(row['electricity_use_kwh']),
                    'cost_gbp': float(row['cost_gbp'])
                })
        return heat_pumps
    
    def _load_improvements(self, csv_path: str) -> List[Dict]:
        """Load home improvement data from CSV file and sort by cost-effectiveness.
        
        Reads heat loss reduction in Watts (at design conditions: 21°C inside, 2°C outside),
        converts to kWh/year using empirically-derived factor, and sorts by heat reduction per pound.
        """
        improvements = []
        
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert Watts to kWh/year using empirical factor
                heat_reduction_w = float(row['heat_loss_reduction_watt'])
                heat_reduction_kwh_year = heat_reduction_w * self.WATTS_TO_KWH_YEAR
                
                improvements.append({
                    'description': row['description'],
                    'cost_gbp': float(row['cost_gbp']),
                    'heat_reduction_kwh': heat_reduction_kwh_year,
                    'cost_effectiveness': heat_reduction_w / float(row['cost_gbp'])
                })
        
        # Sort by cost-effectiveness (W per £) in descending order
        improvements.sort(key=lambda x: x['cost_effectiveness'], reverse=True)
        return improvements
    
    def calculate_insulation_costs(self) -> Tuple[List[float], List[float]]:
        """Calculate accumulated insulation costs and remaining heat loss.
        
        Ensures heat loss doesn't go below 1000 kWh/year (minimum for hot water).
        
        Returns:
            Tuple of (heat_loss_values, insulation_cost_values)
        """
        heat_loss = [self.initial_heat_loss]
        insulation_cost = [0]
        
        cumulative_cost = 0
        cumulative_reduction = 0
        
        for improvement in self.improvements:
            cumulative_cost += improvement['cost_gbp']
            cumulative_reduction += improvement['heat_reduction_kwh']
            
            # Ensure we don't reduce heat loss below minimum
            remaining_heat_loss = max(self.MIN_HEAT_LOSS_KWH, 
                                     self.initial_heat_loss - cumulative_reduction)
            
            # Stop if we've already reached minimum heat loss
            if heat_loss[-1] <= self.MIN_HEAT_LOSS_KWH:
                break
                
            insulation_cost.append(cumulative_cost)
            heat_loss.append(remaining_heat_loss)
        
        return heat_loss, insulation_cost
    
    def get_heat_pump_arrays(self) -> Dict[str, np.ndarray]:
        """Get heat pump data as numpy arrays.
        
        Returns:
            Dictionary with capacities, demands, costs, electricity use arrays, and property types
        """
        hp_capacity = np.array([hp['capacity_kw'] for hp in self.heat_pumps])
        hp_demand = np.array([hp['heat_demand_kwh'] for hp in self.heat_pumps])
        hp_cost = np.array([hp['cost_gbp'] for hp in self.heat_pumps])
        hp_electricity = np.array([hp['electricity_use_kwh'] for hp in self.heat_pumps])
        hp_property_types = [hp['property_type'] for hp in self.heat_pumps]
        
        return {
            'capacity': hp_capacity,
            'demand': hp_demand,
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
        
        heat_loss, insulation_cost = self.calculate_insulation_costs()
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
        heat_loss_array = np.array(heat_loss[1:])
        
        # Insulation fit using power law: cost = a / heat_loss^b + c
        # This ensures monotonic decreasing cost as heat loss increases
        def power_law_func(x, a, b, c):
            return np.maximum(0, a / (x ** b) + c)  # Ensure non-negative
        
        try:
            # Fit with reasonable initial guesses and bounds to ensure positive result
            popt, _ = curve_fit(power_law_func, heat_loss_array, insulation_cost_array,
                               p0=[1e7, 1.5, 0], maxfev=10000,
                               bounds=([0, 0, -1e5], [1e10, 5, 1e5]))
            insulation_fit = lambda x: np.maximum(0, power_law_func(x, *popt))
        except:
            # Fallback to polynomial fit if curve_fit fails
            insulation_coeffs = np.polyfit(1/heat_loss_array, insulation_cost_array, 2)
            insulation_fit = lambda x: np.maximum(0, np.poly1d(insulation_coeffs)(1/x))
        
        # Heat pump fit (linear)
        hp_coeffs = np.polyfit(hp_arrays['demand'], hp_cost_with_runtime, 1)
        hp_fit = np.poly1d(hp_coeffs)
        
        # Calculate total cost curve
        heat_loss_range = np.linspace(min(heat_loss), max(heat_loss), 100)
        total_costs = []
        
        for hl in heat_loss_range:
            ins_cost = np.interp(hl, heat_loss[::-1], insulation_cost[::-1])
            hp_cost_val = hp_fit(hl)
            total_costs.append(ins_cost + hp_cost_val)
        
        # Find optimal point
        min_idx = np.argmin(total_costs)
        min_heat_loss = heat_loss_range[min_idx]
        min_total_cost = total_costs[min_idx]
        
        # Calculate runtime costs for optimal point
        if runtime_years > 0:
            elec_coeffs = np.polyfit(hp_arrays['demand'], hp_arrays['electricity'], 1)
            elec_fit = np.poly1d(elec_coeffs)
            optimal_electricity_annual = elec_fit(min_heat_loss)
            optimal_runtime_cost = optimal_electricity_annual * electricity_rate * runtime_years
        else:
            optimal_electricity_annual = 0
            optimal_runtime_cost = 0
        
        # Build improvement names list (Starting point + improvements)
        improvement_names = ['Start'] + [imp['description'] for imp in self.improvements]
        
        return {
            'min_heat_loss': min_heat_loss,
            'min_total_cost': min_total_cost,
            'insulation_cost': np.interp(min_heat_loss, heat_loss[::-1], insulation_cost[::-1]),
            'hp_cost': hp_fit(min_heat_loss),
            'hp_cost_single': np.interp(min_heat_loss, hp_arrays['demand'], hp_arrays['cost']),
            'hp_cost_capital_only': np.interp(min_heat_loss, hp_arrays['demand'], hp_arrays['cost']) * num_heat_pumps - total_grants,
            'runtime_cost': optimal_runtime_cost,
            'runtime_years': runtime_years,
            'electricity_rate': electricity_rate,
            'annual_electricity_kwh': optimal_electricity_annual,
            'total_grants': total_grants,
            'num_heat_pumps': num_heat_pumps,
            'initial_heat_loss': self.initial_heat_loss,
            'heat_loss_values': heat_loss,
            'insulation_cost_values': insulation_cost,
            'improvement_names': improvement_names,
            'heat_loss_range': heat_loss_range,
            'total_cost_curve': total_costs,
            'insulation_fit': insulation_fit,
            'hp_fit': hp_fit,
            'hp_arrays': hp_arrays
        }
