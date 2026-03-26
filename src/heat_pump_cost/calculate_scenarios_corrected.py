"""
Calculate flow temperatures for different scenarios accounting for log burner properly.
"""
import sys
sys.path.insert(0, '/home/wup1cbg/github/heat-pump-cost/src')

from heat_pump_cost.operations_model import calculate_heating_power, solve_return_temp
from scipy.optimize import minimize_scalar
import numpy as np

def estimate_cop(tf, to=5.0):
    """Estimate COP based on flow temperature and outdoor temperature."""
    t_cond = tf + 5  # °C
    t_evap = to - 5  # Evaporating temp below outdoor temp
    
    T_cond = t_cond + 273.15
    T_evap = t_evap + 273.15
    
    cop_carnot = T_cond / (T_cond - T_evap)
    cop_real = 0.5 * cop_carnot
    
    return cop_real

def find_flow_temp_for_power(target_power_kw, vf_lpm):
    """Find required flow temperature to deliver target power at given flow rate."""
    target_power_w = target_power_kw * 1000
    vf_lps = vf_lpm / 60.0
    
    def objective(tf):
        q = calculate_heating_power(vf_lps, tf)
        if np.isnan(q):
            return 1e9
        return abs(q - target_power_w)
    
    result = minimize_scalar(objective, bounds=(35, 70), method='bounded')
    
    if result.fun < 100:
        return result.x
    return None

print("="*80)
print("CORRECTED SCENARIO ANALYSIS")
print("Accounting for log burner contribution in heat balance")
print("="*80)

# Actual measurements from January 2026
Qr_measured = 2.4  # kW from radiators (gas system)
Qb_measured = 0.375  # kW from log burner (9 kWh/day ÷ 24h)
Ql_total = Qr_measured + Qb_measured  # Total actual heat demand

print(f"\nActual January 2026 performance:")
print(f"  Radiator output: {Qr_measured:.2f} kW (from gas system)")
print(f"  Log burner output: {Qb_measured:.3f} kW (0.375 kW average)")
print(f"  Total heat delivered: {Ql_total:.3f} kW")
print(f"  Theoretical heat loss (244 W/K × 13K): 3.17 kW")
print(f"  Actual is {100*Ql_total/3.17:.0f}% of theoretical (thermal mass + internal gains)")

print("\n" + "="*80)
print("SCENARIO 1: Current Gas Boiler + Log Burner")
print("="*80)

vf_low = 1.5
vf_high = 20

print(f"\nRadiators deliver: {Qr_measured:.2f} kW")
print(f"Log burner delivers: {Qb_measured:.3f} kW")
print(f"Total: {Ql_total:.3f} kW")

# Gas boiler at observed flow temp
tf_gas = find_flow_temp_for_power(Qr_measured, vf_high)
if tf_gas:
    tr_gas = solve_return_temp(vf_high/60, tf_gas)
    print(f"\nGas boiler operation (observed):")
    print(f"  Flow rate: ~{vf_high:.0f} l/min")
    print(f"  Flow temp: {tf_gas:.1f}°C")
    print(f"  Return temp: {tr_gas:.1f}°C")
    print(f"  ΔT = {tf_gas - tr_gas:.1f}K")
    
    gas_input = Qr_measured / 0.9  # 90% efficiency
    daily_gas = gas_input * 24
    daily_cost = daily_gas * 0.07
    print(f"  Gas input: {gas_input:.2f} kW")
    print(f"  Daily gas: {daily_gas:.1f} kWh")
    print(f"  Daily cost: £{daily_cost:.2f}")

print("\n" + "="*80)
print("SCENARIO 2: Heat Pump + Log Burner")
print("="*80)

print(f"\nHeat pump delivers: {Qr_measured:.2f} kW")
print(f"Log burner delivers: {Qb_measured:.3f} kW")
print(f"Total: {Ql_total:.3f} kW")

# Heat pump needs to deliver same as gas system
tf_hp_with_log = find_flow_temp_for_power(Qr_measured, vf_high)
if tf_hp_with_log:
    tr_hp_with_log = solve_return_temp(vf_high/60, tf_hp_with_log)
    cop_with_log = estimate_cop(tf_hp_with_log)
    
    print(f"\nHeat pump operation (high flow):")
    print(f"  Flow rate: {vf_high:.0f} l/min")
    print(f"  Flow temp: {tf_hp_with_log:.1f}°C")
    print(f"  Return temp: {tr_hp_with_log:.1f}°C")
    print(f"  ΔT = {tf_hp_with_log - tr_hp_with_log:.1f}K")
    print(f"  Estimated COP: {cop_with_log:.2f}")
    
    elec_input = Qr_measured / cop_with_log
    daily_elec = elec_input * 24
    daily_cost_hp = daily_elec * 0.25
    print(f"  Electrical input: {elec_input:.2f} kW")
    print(f"  Daily electricity: {daily_elec:.1f} kWh")
    print(f"  Daily cost: £{daily_cost_hp:.2f}")
    print(f"  Saving vs gas: £{daily_cost - daily_cost_hp:.2f}/day")

print("\n" + "="*80)
print("SCENARIO 3: Heat Pump WITHOUT Log Burner")
print("="*80)

# Without log burner, need to deliver the full measured load
Qr_no_log = Ql_total  # All heating from radiators
print(f"\nHeat pump must deliver: {Qr_no_log:.3f} kW (full measured load)")
print(f"Note: This is actual measured need, not theoretical 3.17 kW")

tf_hp_no_log = find_flow_temp_for_power(Qr_no_log, vf_high)
if tf_hp_no_log:
    tr_hp_no_log = solve_return_temp(vf_high/60, tf_hp_no_log)
    cop_no_log = estimate_cop(tf_hp_no_log)
    
    print(f"\nHeat pump operation (high flow):")
    print(f"  Flow rate: {vf_high:.0f} l/min")
    print(f"  Flow temp: {tf_hp_no_log:.1f}°C")
    print(f"  Return temp: {tr_hp_no_log:.1f}°C")
    print(f"  ΔT = {tf_hp_no_log - tr_hp_no_log:.1f}K")
    print(f"  Estimated COP: {cop_no_log:.2f}")
    
    elec_input_no_log = Qr_no_log / cop_no_log
    daily_elec_no_log = elec_input_no_log * 24
    daily_cost_hp_no_log = daily_elec_no_log * 0.25
    print(f"  Electrical input: {elec_input_no_log:.2f} kW")
    print(f"  Daily electricity: {daily_elec_no_log:.1f} kWh")
    print(f"  Daily cost: £{daily_cost_hp_no_log:.2f}")
    print(f"  vs Gas: £{daily_cost_hp_no_log - daily_cost:.2f}/day ({100*(daily_cost_hp_no_log - daily_cost)/daily_cost:+.0f}%)")
    print(f"  vs HP+log: £{daily_cost_hp_no_log - daily_cost_hp:.2f}/day ({100*(daily_cost_hp_no_log - daily_cost_hp)/daily_cost_hp:+.0f}%)")

print("\n" + "="*80)
print("SCENARIO 4: Heat Pump for THEORETICAL Full Load (Conservative)")
print("="*80)

Qr_theoretical = 3.17  # Full theoretical heat loss
print(f"\nHeat pump must deliver: {Qr_theoretical:.2f} kW (theoretical HTC × ΔT)")
print(f"This represents coldest conditions with no thermal mass benefit")

tf_hp_theory = find_flow_temp_for_power(Qr_theoretical, vf_high)
if tf_hp_theory:
    tr_hp_theory = solve_return_temp(vf_high/60, tf_hp_theory)
    cop_theory = estimate_cop(tf_hp_theory)
    
    print(f"\nHeat pump operation (high flow):")
    print(f"  Flow rate: {vf_high:.0f} l/min")
    print(f"  Flow temp: {tf_hp_theory:.1f}°C")
    print(f"  Return temp: {tr_hp_theory:.1f}°C")
    print(f"  ΔT = {tf_hp_theory - tr_hp_theory:.1f}K")
    print(f"  Estimated COP: {cop_theory:.2f}")
    
    elec_input_theory = Qr_theoretical / cop_theory
    daily_elec_theory = elec_input_theory * 24
    daily_cost_theory = daily_elec_theory * 0.25
    print(f"  Electrical input: {elec_input_theory:.2f} kW")
    print(f"  Daily electricity: {daily_elec_theory:.1f} kWh")
    print(f"  Daily cost: £{daily_cost_theory:.2f}")
    print(f"  Note: This is conservative worst-case; actual would be scenario 3")

print("\n" + "="*80)
print("SUMMARY & CONCLUSIONS")
print("="*80)
print(f"""
1. With log burner (current):
   - Gas boiler: £{daily_cost:.2f}/day
   - Heat pump: £{daily_cost_hp:.2f}/day at {tf_hp_with_log:.1f}°C
   - Saving: £{daily_cost - daily_cost_hp:.2f}/day ({100*(daily_cost - daily_cost_hp)/daily_cost:.0f}%)

2. Without log burner (actual measured load {Qr_no_log:.2f} kW):
   - Heat pump: £{daily_cost_hp_no_log:.2f}/day at {tf_hp_no_log:.1f}°C
   - vs Gas+log: £{daily_cost_hp_no_log - daily_cost:.2f}/day ({100*(daily_cost_hp_no_log - daily_cost)/daily_cost:+.0f}%)
   - Still viable but less attractive

3. Radiator upgrade recommendation:
   - Current: Can deliver {Qr_no_log:.2f} kW at {tf_hp_no_log:.1f}°C (COP {cop_no_log:.2f})
   - With upgrade (K→65): Could deliver {Qr_no_log:.2f} kW at ~{tf_hp_no_log-5:.0f}°C (COP ~{cop_no_log+0.3:.2f})
   - Would reduce daily cost by ~£{0.25 * daily_elec_no_log * (1 - cop_no_log/(cop_no_log+0.3)):.2f}
   
4. Key insight:
   - Flow temps are LOWER than previously calculated because log burner 
     reduces radiator requirement from 3.17 kW to 2.775 kW actual
   - Heat pump is economically viable even without radiator upgrade if 
     log burner continues to be used
""")

print("="*80)
