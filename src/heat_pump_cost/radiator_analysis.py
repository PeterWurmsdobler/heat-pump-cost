"""
Analysis of radiator constant requirements for heat pump operation.

This module generates two key plots:
1. For a given K, show T_f and COP vs Q_r (heating power)
2. For given Q_r values, show T_f and COP vs K (radiator constant)
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from scipy.optimize import fsolve, brentq


# Physical constants
RHO = 1.0  # Water density [kg/l]
CP = 4180.0  # Specific heat capacity of water [J/kg/K]

# House thermal properties
HTC = 244.0  # Heat Transfer Coefficient [W/K]
TI = 19.0  # Indoor temperature [°C]
TO = 5.0  # Outdoor temperature [°C]

# Radiator properties
K_CURRENT = 35.9  # Current radiator constant [W/K^1.2]
N_RAD = 1.2  # Radiator exponent

# Operating parameters
VF_FIXED = 20.0 / 60.0  # Fixed flow rate [l/s] = 20 l/min

# COP model parameters
COP_EFFICIENCY = 0.55  # Carnot efficiency factor for modern heat pumps
T_LIFT = 5.0  # Temperature lift from radiator flow to heat pump condenser [K]


def cop_estimate(t_outdoor, t_flow):
    """
    Estimate heat pump COP based on outdoor and flow temperatures.
    
    Uses Carnot efficiency with practical degradation factor.
    COP = η * T_condenser / (T_condenser - T_evaporator)
    
    Args:
        t_outdoor: Outdoor temperature [°C]
        t_flow: Radiator flow temperature [°C]
    
    Returns:
        Estimated COP
    """
    # Convert to Kelvin
    T_evap = t_outdoor + 273.15
    T_cond = t_flow + T_LIFT + 273.15
    
    # Carnot COP
    cop_carnot = T_cond / (T_cond - T_evap)
    
    # Apply efficiency factor
    cop = COP_EFFICIENCY * cop_carnot
    
    return cop


def solve_for_flow_temp(q_target, k_rad, vf, ti=TI, n=N_RAD):
    """
    Solve for flow temperature T_f given target power, radiator constant, and flow rate.
    
    Two equations to solve simultaneously:
    1. Q = K * ((T_f + T_r)/2 - T_i)^n
    2. Q = V_f * rho * cp * (T_f - T_r)
    
    Args:
        q_target: Target heating power [W]
        k_rad: Radiator constant [W/K^n]
        vf: Flow rate [l/s]
        ti: Indoor temperature [°C]
        n: Radiator exponent
    
    Returns:
        (t_flow, t_return): Flow and return temperatures [°C], or (None, None) if no solution
    """
    def equations(vars):
        tf, tr = vars
        
        # Radiator equation
        t_mean = (tf + tr) / 2.0
        delta_t = t_mean - ti
        if delta_t <= 0:
            q_rad = 0
        else:
            q_rad = k_rad * (delta_t ** n)
        
        # Flow equation
        q_flow = vf * RHO * CP * (tf - tr)
        
        # Both should equal target power
        return [q_rad - q_target, q_flow - q_target]
    
    # Initial guess: reasonable temperature drop
    tf_guess = ti + 30.0
    tr_guess = tf_guess - 5.0
    
    try:
        solution = fsolve(equations, [tf_guess, tr_guess], full_output=True)
        tf, tr = solution[0]
        info = solution[1]
        
        # Check convergence and physical validity
        residual = np.sqrt(info['fvec'][0]**2 + info['fvec'][1]**2)
        if residual < 1.0 and ti < tr < tf < 90.0:
            return tf, tr
        else:
            return None, None
    except:
        return None, None


def plot_performance_vs_power(k_rad=K_CURRENT, vf=VF_FIXED, 
                              power_range=(500, 4000), num_points=50):
    """
    Plot 1: For a given K, show T_f and COP vs heating power Q_r.
    
    Args:
        k_rad: Radiator constant [W/K^n]
        vf: Flow rate [l/s]
        power_range: (min, max) power range [W]
        num_points: Number of points to calculate
    
    Returns:
        fig, (ax1, ax2): Figure and axes
    """
    powers = np.linspace(power_range[0], power_range[1], num_points)
    flow_temps = []
    cops = []
    
    print(f"Calculating performance vs power for K = {k_rad:.1f} W/K^{N_RAD}...")
    
    for q in powers:
        tf, tr = solve_for_flow_temp(q, k_rad, vf)
        if tf is not None:
            flow_temps.append(tf)
            cop = cop_estimate(TO, tf)
            cops.append(cop)
        else:
            flow_temps.append(np.nan)
            cops.append(np.nan)
    
    flow_temps = np.array(flow_temps)
    cops = np.array(cops)
    powers_kw = powers / 1000.0
    
    # Create figure with dual y-axes
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    # Plot flow temperature on bottom axis
    color1 = 'tab:blue'
    ax1.set_xlabel('Heating Power (kW)', fontsize=12)
    ax1.set_ylabel('Flow Temperature (°C)', fontsize=12, color=color1)
    line1 = ax1.plot(powers_kw, flow_temps, color=color1, linewidth=2, 
                     label=f'Flow Temperature (K = {k_rad:.1f} W/K$^{{{N_RAD}}}$)')
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.grid(True, alpha=0.3)
    
    # Mark the three key power levels on temperature axis
    key_powers = [1.96, 2.335, 3.12]
    for qk in key_powers:
        if power_range[0]/1000 <= qk <= power_range[1]/1000:
            idx = np.argmin(np.abs(powers_kw - qk))
            if not np.isnan(flow_temps[idx]):
                ax1.plot(qk, flow_temps[idx], 'o', color=color1, markersize=8)
                ax1.annotate(f'{flow_temps[idx]:.0f}°C', 
                           xy=(qk, flow_temps[idx]), 
                           xytext=(10, 10), textcoords='offset points',
                           fontsize=9, color=color1)
    
    # Create second y-axis on top for COP
    ax2 = ax1.twinx()
    ax2.spines['top'].set_position(('axes', 1.0))
    ax2.spines['top'].set_visible(True)
    ax2.xaxis.set_ticks_position('top')
    ax2.xaxis.set_label_position('top')
    
    color2 = 'tab:green'
    ax2.set_ylabel('COP', fontsize=12, color=color2)
    line2 = ax2.plot(powers_kw, cops, color=color2, linewidth=2, label='Heat Pump COP')
    line3 = ax2.axhline(y=3.6, color='red', linestyle='--', linewidth=2, label='Break-even COP = 3.6')
    ax2.tick_params(axis='y', labelcolor=color2)
    ax2.set_ylim([1.5, 6.0])
    
    # Mark the three key power levels on COP axis
    for qk in key_powers:
        if power_range[0]/1000 <= qk <= power_range[1]/1000:
            idx = np.argmin(np.abs(powers_kw - qk))
            if not np.isnan(cops[idx]):
                ax2.plot(qk, cops[idx], 'o', color=color2, markersize=8)
    
    # Title
    fig.suptitle(f'Flow Temperature and COP vs Heating Power\n(V$_f$ = {vf*60:.0f} l/min, T$_o$ = {TO:.0f}°C)', 
                fontsize=13, y=0.98)
    
    # Combined legend
    lines = line1 + line2 + [line3]
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='center left', fontsize=10)
    
    plt.tight_layout()
    return fig, (ax1, ax2)


def plot_performance_vs_k(power_levels=[1960, 2335, 3120], vf=VF_FIXED,
                          k_range=(30, 100), num_points=50):
    """
    Plot 2: For given power levels, show T_f and COP vs radiator constant K.
    
    Args:
        power_levels: List of power levels [W]
        vf: Flow rate [l/s]
        k_range: (min, max) K values [W/K^n]
        num_points: Number of points to calculate
    
    Returns:
        fig, (ax1, ax2): Figure and axes
        k_required: Dict mapping power levels to required K values for COP=3.6
    """
    k_values = np.linspace(k_range[0], k_range[1], num_points)
    
    # Create figure with dual y-axes
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    colors = ['blue', 'green', 'red']
    k_required = {}
    
    # Plot flow temperature on bottom axis
    ax1.set_xlabel('Radiator Constant K (W/K$^{1.2}$)', fontsize=12)
    ax1.set_ylabel('Flow Temperature (°C)', fontsize=12, color='black')
    ax1.grid(True, alpha=0.3)
    
    # Create second y-axis on top for COP
    ax2 = ax1.twinx()
    ax2.spines['top'].set_position(('axes', 1.0))
    ax2.spines['top'].set_visible(True)
    ax2.xaxis.set_ticks_position('top')
    ax2.xaxis.set_label_position('top')
    ax2.set_ylabel('COP', fontsize=12, color='black')
    ax2.set_ylim([1.5, 5.5])
    
    # Plot break-even line
    ax2.axhline(y=3.6, color='black', linestyle='--', linewidth=2, 
                label='Target COP = 3.6', alpha=0.7)
    
    lines_temp = []
    lines_cop = []
    
    for i, q_target in enumerate(power_levels):
        print(f"Calculating performance vs K for Q = {q_target/1000:.2f} kW...")
        
        flow_temps = []
        cops = []
        
        for k in k_values:
            tf, tr = solve_for_flow_temp(q_target, k, vf)
            if tf is not None:
                flow_temps.append(tf)
                cop = cop_estimate(TO, tf)
                cops.append(cop)
            else:
                flow_temps.append(np.nan)
                cops.append(np.nan)
        
        flow_temps = np.array(flow_temps)
        cops = np.array(cops)
        
        label = f'Q = {q_target/1000:.2f} kW'
        
        # Plot on both axes with same color
        line_t = ax1.plot(k_values, flow_temps, color=colors[i], linewidth=2, 
                         linestyle='-', label=f'{label} (T_f)', alpha=0.7)
        line_c = ax2.plot(k_values, cops, color=colors[i], linewidth=2, 
                         linestyle='--', label=f'{label} (COP)', alpha=0.7)
        
        lines_temp.extend(line_t)
        lines_cop.extend(line_c)
        
        # Find intersection with COP = 3.6
        valid_mask = ~np.isnan(cops)
        if np.any(valid_mask):
            valid_k = k_values[valid_mask]
            valid_cop = cops[valid_mask]
            
            # Find where COP crosses 3.6
            if np.any(valid_cop > 3.6):
                # Interpolate to find exact K where COP = 3.6
                idx = np.where(valid_cop > 3.6)[0][0]
                if idx > 0:
                    # Linear interpolation
                    k1, k2 = valid_k[idx-1], valid_k[idx]
                    cop1, cop2 = valid_cop[idx-1], valid_cop[idx]
                    k_target = k1 + (3.6 - cop1) * (k2 - k1) / (cop2 - cop1)
                    k_required[q_target] = k_target
                    
                    # Mark on both plots
                    tf_target, _ = solve_for_flow_temp(q_target, k_target, vf)
                    if tf_target is not None:
                        ax1.plot(k_target, tf_target, 'o', color=colors[i], 
                               markersize=10, markeredgecolor='black', markeredgewidth=2)
                        ax2.plot(k_target, 3.6, 'o', color=colors[i], 
                               markersize=10, markeredgecolor='black', markeredgewidth=2)
    
    # Title
    fig.suptitle(f'Flow Temperature and COP vs Radiator Constant\n(V$_f$ = {vf*60:.0f} l/min, T$_o$ = {TO:.0f}°C)', 
                fontsize=13, y=0.98)
    
    # Combined legend - show solid lines for temp, dashed for COP
    temp_legend = ax1.legend(loc='lower right', fontsize=9, title='Flow Temp (solid)')
    ax1.add_artist(temp_legend)
    ax2.legend(loc='upper right', fontsize=9, title='COP (dashed)')
    
    plt.tight_layout()
    return fig, (ax1, ax2), k_required


def main():
    """Generate both plots and calculate required K values."""
    
    print("=" * 60)
    print("Radiator Upgrade Analysis")
    print("=" * 60)
    
    # Plot 1: Performance vs Power for current K
    print("\n1. Generating performance vs power plot...")
    fig1, _ = plot_performance_vs_power(k_rad=K_CURRENT, power_range=(500, 4000))
    fig1.savefig('assets/performance_vs_power.png', dpi=150, bbox_inches='tight')
    print("   Saved: assets/performance_vs_power.png")
    
    # Plot 2: Performance vs K for three power levels
    print("\n2. Generating performance vs K plot...")
    power_levels = [1960, 2335, 3120]  # W
    fig2, _, k_required = plot_performance_vs_k(power_levels=power_levels, k_range=(30, 100))
    fig2.savefig('assets/performance_vs_k.png', dpi=150, bbox_inches='tight')
    print("   Saved: assets/performance_vs_k.png")
    
    # Print required K values
    print("\n" + "=" * 60)
    print("REQUIRED RADIATOR CONSTANTS FOR COP = 3.6")
    print("=" * 60)
    print(f"Current K: {K_CURRENT:.1f} W/K^{N_RAD}")
    print()
    
    for q, k in k_required.items():
        factor = k / K_CURRENT
        print(f"For Q_r = {q/1000:.2f} kW:")
        print(f"  Required K = {k:.1f} W/K^{N_RAD}")
        print(f"  Increase factor = {factor:.2f}x")
        
        # Calculate flow temperature at this K
        tf, tr = solve_for_flow_temp(q, k, VF_FIXED)
        if tf is not None:
            cop = cop_estimate(TO, tf)
            print(f"  Flow temperature = {tf:.1f}°C")
            print(f"  COP = {cop:.2f}")
        print()
    
    # For the conclusion, we want the K for peak load (3.12 kW)
    if 3120 in k_required:
        k_peak = k_required[3120]
        factor_peak = k_peak / K_CURRENT
        print("=" * 60)
        print("RECOMMENDATION FOR CONCLUSION:")
        print("=" * 60)
        print(f"To handle peak load of 3.12 kW at COP = 3.6:")
        print(f"  Required K ≈ {k_peak:.0f} W/K^{N_RAD}")
        print(f"  This is approximately {factor_peak:.1f}× current capacity")
        print("=" * 60)


if __name__ == '__main__':
    main()
