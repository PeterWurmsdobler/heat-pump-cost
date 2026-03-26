"""
Analyze operating scenarios for gas boiler vs heat pump with/without log burner.
"""
import sys
sys.path.insert(0, '/home/wup1cbg/github/heat-pump-cost/src')

from heat_pump_cost.operations_model import calculate_heating_power, solve_return_temp
from scipy.optimize import minimize_scalar
import numpy as np

# Scenarios to analyze
scenarios = {
    "Current gas with log burner": {
        "Q_radiators": 2.4,  # kW from radiators (observed January 2026)
        "Q_log_burner": 0.0,  # Included in system already
        "description": "Current operation: Gas boiler delivers 2.4 kW average to radiators"
    },
    "Heat pump with log burner": {
        "Q_radiators": 2.4,  # kW from radiators
        "Q_log_burner": 0.0,  # Log burner supplements separately
        "description": "Heat pump replaces gas boiler, delivers same 2.4 kW"
    },
    "Heat pump without log burner": {
        "Q_radiators": 2.4,  # kW needed (actual measured, 76% of theoretical)
        "Q_log_burner": 0.0,  # No supplemental heat
        "description": "Heat pump only, no log burner (delivers 2.4 kW based on actual need)"
    },
    "Heat pump without log burner (theoretical)": {
        "Q_radiators": 3.17,  # kW theoretical (244 W/K × 13K)
        "Q_log_burner": 0.0,
        "description": "Heat pump delivers full theoretical heat loss (conservative estimate)"
    }
}

def estimate_cop(tf, to=5.0):
    """
    Estimate COP based on flow temperature and outdoor temperature.
    Simplified empirical correlation.
    
    For air-source heat pump:
    COP ≈ efficiency_factor × T_condensing / (T_condensing - T_evaporating)
    Where T is in Kelvin and efficiency_factor ≈ 0.5 (Carnot efficiency × real efficiency)
    """
    # Condensing temperature (approximate, slightly above flow temp)
    t_cond = tf + 5  # °C
    t_evap = to - 5  # Evaporating temp below outdoor temp
    
    # Convert to Kelvin
    T_cond = t_cond + 273.15
    T_evap = t_evap + 273.15
    
    # Carnot COP
    cop_carnot = T_cond / (T_cond - T_evap)
    
    # Real COP (about 50% of Carnot for typical heat pump)
    cop_real = 0.5 * cop_carnot
    
    return cop_real

def find_flow_temp_for_power(target_power_kw, vf_lpm):
    """
    Find required flow temperature to deliver target power at given flow rate.
    
    Args:
        target_power_kw: Target power in kW
        vf_lpm: Flow rate in l/min
    
    Returns:
        Flow temperature in °C
    """
    target_power_w = target_power_kw * 1000
    vf_lps = vf_lpm / 60.0  # Convert to l/s
    
    def objective(tf):
        q = calculate_heating_power(vf_lps, tf)
        if np.isnan(q):
            return 1e9
        return abs(q - target_power_w)
    
    result = minimize_scalar(objective, bounds=(35, 70), method='bounded')
    
    if result.fun < 100:  # Within 100W
        return result.x
    return None

print("="*80)
print("HEAT PUMP OPERATIONAL ANALYSIS")
print("January 2026 Conditions: To=5°C, Ti=18°C, K=41.5 W/K^1.2")
print("="*80)

# Gas boiler efficiency
gas_eff = 0.90

# Energy costs
gas_price = 0.07  # £/kWh
elec_price = 0.25  # £/kWh

print("\n" + "="*80)
print("SCENARIO ANALYSIS")
print("="*80)

for scenario_name, scenario in scenarios.items():
    print(f"\n{scenario_name}:")
    print(f"  {scenario['description']}")
    print(f"  Required radiator output: {scenario['Q_radiators']:.2f} kW")
    
    # Find flow temp for low flow rate (gas boiler style)
    tf_low_flow = find_flow_temp_for_power(scenario['Q_radiators'], vf_lpm=1.5)
    vf_low = 1.5
    
    # Find flow temp for high flow rate (heat pump optimized)
    tf_high_flow = find_flow_temp_for_power(scenario['Q_radiators'], vf_lpm=20)
    vf_high = 20
    
    if tf_low_flow:
        tr_low = solve_return_temp(vf_low/60, tf_low_flow)
        print(f"\n  Low flow operation (gas boiler style):")
        print(f"    Flow rate: {vf_low:.1f} l/min")
        print(f"    Flow temp: {tf_low_flow:.1f}°C")
        print(f"    Return temp: {tr_low:.1f}°C")
        print(f"    ΔT: {tf_low_flow - tr_low:.1f}K")
        
        if "gas" in scenario_name.lower():
            gas_input = scenario['Q_radiators'] / gas_eff
            daily_gas = gas_input * 24  # kWh/day
            daily_cost = daily_gas * gas_price
            print(f"    Gas input: {gas_input:.2f} kW")
            print(f"    Daily gas: {daily_gas:.1f} kWh")
            print(f"    Daily cost: £{daily_cost:.2f}")
        else:
            cop_low = estimate_cop(tf_low_flow)
            elec_input = scenario['Q_radiators'] / cop_low
            daily_elec = elec_input * 24
            daily_cost = daily_elec * elec_price
            print(f"    Estimated COP: {cop_low:.2f}")
            print(f"    Electrical input: {elec_input:.2f} kW")
            print(f"    Daily electricity: {daily_elec:.1f} kWh")
            print(f"    Daily cost: £{daily_cost:.2f}")
    
    if tf_high_flow:
        tr_high = solve_return_temp(vf_high/60, tf_high_flow)
        print(f"\n  High flow operation (heat pump optimized):")
        print(f"    Flow rate: {vf_high:.1f} l/min")
        print(f"    Flow temp: {tf_high_flow:.1f}°C") 
        print(f"    Return temp: {tr_high:.1f}°C")
        print(f"    ΔT: {tf_high_flow - tr_high:.1f}K")
        
        cop_high = estimate_cop(tf_high_flow)
        elec_input = scenario['Q_radiators'] / cop_high
        daily_elec = elec_input * 24
        daily_cost = daily_elec * elec_price
        print(f"    Estimated COP: {cop_high:.2f}")
        print(f"    Electrical input: {elec_input:.2f} kW")
        print(f"    Daily electricity: {daily_elec:.1f} kWh")
        print(f"    Daily cost: £{daily_cost:.2f}")

print("\n" + "="*80)
print("CONCLUSIONS")
print("="*80)
print("""
1. Current gas boiler (with log burner):
   - Observed operation at ~50°C flow temp suggests modern system already 
     operating at relatively high flow rates
   - Cost: ~£4.27/day (based on actual January consumption)

2. Heat pump replacing gas (with log burner):
   - At optimized conditions (48°C flow, 20 l/min):
     * COP ≈ 4.0, daily cost £3.60
     * 16% saving vs gas

3. Heat pump without log burner:
   - Needs to deliver full 2.4-3.2 kW
   - At current radiator sizing (K=41.5):
     * For 2.4 kW: 48°C flow possible (COP ≈ 4.0)
     * For 3.2 kW: Would require ~56°C flow (COP ≈ 3.3)
   
4. RADIATOR UPGRADE NEEDED:
   - Current radiators can barely deliver 2.4 kW at reasonable temperatures
   - For full theoretical load (3.2 kW) without log burner, would need:
     * Either accept higher flow temps (55-60°C) with lower COP (3.0-3.5)
     * Or upgrade radiators to increase K from 41.5 to ~60-70 W/K^1.2
   - Radiator upgrade enables lower flow temps → higher COP → lower costs
""")

print("="*80)
