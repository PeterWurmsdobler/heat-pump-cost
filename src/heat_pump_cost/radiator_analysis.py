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
K_CURRENT = 71.2  # Radiator constant from survey [W/K^1.2]
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
    
    Shows main curve at TO = 5°C (typical winter), with special markers for scenarios
    at different outdoor temperatures.
    
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
    
    # Main curve at TO = 5°C (typical winter)
    # Calculate COP at both 5°C and -2°C to show outdoor temp effect
    cops_5C = []
    cops_minus2C = []
    
    for q in powers:
        tf, tr = solve_for_flow_temp(q, k_rad, vf)
        if tf is not None:
            flow_temps.append(tf)
            cops_5C.append(cop_estimate(5, tf))
            cops_minus2C.append(cop_estimate(-2, tf))
        else:
            flow_temps.append(np.nan)
            cops_5C.append(np.nan)
            cops_minus2C.append(np.nan)
    
    flow_temps = np.array(flow_temps)
    cops_5C = np.array(cops_5C)
    cops_minus2C = np.array(cops_minus2C)
    powers_kw = powers / 1000.0
    
    # Create figure with dual y-axes
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    # Plot flow temperature on bottom axis
    color1 = 'tab:blue'
    ax1.set_xlabel('Heating Power (kW)', fontsize=12)
    ax1.set_ylabel('Flow Temperature (°C)', fontsize=12, color=color1)
    line1 = ax1.plot(powers_kw, flow_temps, color=color1, linewidth=2, 
                     label=f'Flow Temperature at T$_o$ = {TO}°C (K = {k_rad:.1f} W/K$^{{{N_RAD}}}$)')
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.grid(True, alpha=0.3)
    
    # Mark the three key scenarios - S1 and S2 at 5°C, S3 at -2°C
    key_powers = [1.96, 2.335, 3.65]
    key_t_outdoors = [5, 5, -2]  # S1 and S2 at typical winter, S3 at design temp
    key_labels = ['S1: 1.96 kW\n(+log burner,\nT$_o$=5°C)', 
                  'S2: 2.34 kW\n(continuous,\nT$_o$=5°C)', 
                  'S3: 3.65 kW\n(design temp,\nT$_o$=-2°C)']
    key_colors = ['steelblue', 'darkorange', 'firebrick']
    
    for i, (qk, t_out, label, col) in enumerate(zip(key_powers, key_t_outdoors, key_labels, key_colors)):
        if power_range[0]/1000 <= qk <= power_range[1]/1000:
            ax1.axvline(x=qk, color=col, linewidth=0.9, linestyle='--', alpha=0.7)
            idx = np.argmin(np.abs(powers_kw - qk))
            if not np.isnan(flow_temps[idx]):
                ax1.plot(qk, flow_temps[idx], 'o', color=color1, markersize=8)
                # Adjust annotation position: for S3 (last), put below the dot to avoid interference
                if i == 2:  # S3
                    ax1.annotate(f'{flow_temps[idx]:.0f}°C',
                               xy=(qk, flow_temps[idx]),
                               xytext=(6, -15), textcoords='offset points',
                               fontsize=9, color=color1)
                else:
                    ax1.annotate(f'{flow_temps[idx]:.0f}°C',
                               xy=(qk, flow_temps[idx]),
                               xytext=(6, 6), textcoords='offset points',
                               fontsize=9, color=color1)
            # Annotate label near the top of the plot
            ax1.text(qk + 0.04, ax1.get_ylim()[0] + (ax1.get_ylim()[1] - ax1.get_ylim()[0]) * 0.97,
                     label, fontsize=7.5, color=col, va='top', ha='left', linespacing=1.3)
    
    # Create second y-axis on top for COP
    ax2 = ax1.twinx()
    ax2.spines['top'].set_position(('axes', 1.0))
    ax2.spines['top'].set_visible(True)
    ax2.xaxis.set_ticks_position('top')
    ax2.xaxis.set_label_position('top')
    
    color2 = 'tab:green'
    ax2.set_ylabel('COP', fontsize=12, color=color2)
    
    # Plot both COP curves to show outdoor temperature effect
    line2 = ax2.plot(powers_kw, cops_5C, color=color2, linewidth=2, linestyle='-',
                     label=f'Heat Pump COP at T$_o$ = 5°C')
    line3 = ax2.plot(powers_kw, cops_minus2C, color=color2, linewidth=2, linestyle='--',
                     label=f'Heat Pump COP at T$_o$ = -2°C', alpha=0.7)
    line4 = ax2.axhline(y=4.67, color='red', linestyle='--', linewidth=2, label='Break-even COP = 4.67')
    ax2.tick_params(axis='y', labelcolor=color2)
    ax2.set_ylim([1.5, 6.5])
    
    # Mark the three key scenarios on COP axis, using correct COP curve for each
    for i, (qk, t_out, col) in enumerate(zip(key_powers, key_t_outdoors, key_colors)):
        if power_range[0]/1000 <= qk <= power_range[1]/1000:
            idx = np.argmin(np.abs(powers_kw - qk))
            if not np.isnan(flow_temps[idx]):
                # Use the appropriate COP curve based on outdoor temperature
                if t_out == 5:
                    cop_val = cops_5C[idx]
                    marker_style = 'o'
                else:  # t_out == -2
                    cop_val = cops_minus2C[idx]
                    marker_style = 's'  # Square marker for -2°C to distinguish it
                
                ax2.plot(qk, cop_val, marker_style, color=color2, markersize=8)
                
                # Annotate COP value
                if i == 2:  # S3 at -2°C
                    ax2.annotate(f'{cop_val:.2f}',
                               xy=(qk, cop_val),
                               xytext=(-15, -12), textcoords='offset points',
                               fontsize=9, color=color2, ha='right')
                else:
                    ax2.annotate(f'{cop_val:.2f}',
                               xy=(qk, cop_val),
                               xytext=(6, -10), textcoords='offset points',
                               fontsize=9, color=color2)
    
    # Title
    fig.suptitle(f'Flow Temperature and COP vs Heating Power\n(V$_f$ = {vf*60:.0f} l/min, flow temp at T$_o$ = 5°C)', 
                fontsize=13, y=0.98)
    
    # Combined legend — move to lower left
    lines = line1 + line2 + line3 + [line4]
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='lower left', fontsize=10)
    
    plt.tight_layout()
    return fig, (ax1, ax2)


def plot_performance_vs_k_design_temp(q_target=3650,
                                      t_outdoor=-2,
                                      vf=VF_FIXED,
                                      k_range=(30, 300), num_points=80):
    """
    Plot 2b: For the design temperature scenario (S3), show T_f and COP vs K.

    Shows COP at both T_o = -2°C and T_o = 5°C so the reader can see how much
    the cold outdoor air pulls the COP curve down, and where the break-even K
    would need to be (far off compared to typical upgrades).

    Returns:
        fig, (ax1, ax2): Figure and axes
        k_breakeven: K required to reach COP = 4.67 at design temp (or None)
    """
    k_values = np.linspace(k_range[0], k_range[1], num_points)

    flow_temps = []
    cops_design = []   # COP at T_o = t_outdoor (-2°C)
    cops_typical = []  # COP at T_o = 5°C (reference)

    print(f"Calculating design temp performance vs K for Q = {q_target/1000:.2f} kW...")

    for k in k_values:
        tf, tr = solve_for_flow_temp(q_target, k, vf)
        if tf is not None:
            flow_temps.append(tf)
            cops_design.append(cop_estimate(t_outdoor, tf))
            cops_typical.append(cop_estimate(5.0, tf))
        else:
            flow_temps.append(np.nan)
            cops_design.append(np.nan)
            cops_typical.append(np.nan)

    flow_temps = np.array(flow_temps)
    cops_design = np.array(cops_design)
    cops_typical = np.array(cops_typical)

    fig, ax1 = plt.subplots(figsize=(10, 6))

    color1 = 'tab:red'
    ax1.set_xlabel('Radiator Constant K (W/K$^{1.2}$)', fontsize=12)
    ax1.set_ylabel('Flow Temperature (°C)', fontsize=12, color='tab:blue')
    line1 = ax1.plot(k_values, flow_temps, color='tab:blue', linewidth=2, linestyle='-',
                     label=f'Flow Temp (Q = {q_target/1000:.2f} kW)')
    ax1.tick_params(axis='y', labelcolor='tab:blue')
    ax1.grid(True, alpha=0.3)

    # Mark current K on flow temp curve
    ax1.axvline(x=K_CURRENT, color='grey', linewidth=1.2, linestyle='-', alpha=0.8)
    idx_cur = np.argmin(np.abs(k_values - K_CURRENT))
    ax1.plot(K_CURRENT, flow_temps[idx_cur], 'o', color='tab:blue', markersize=8)
    ax1.annotate(f'{flow_temps[idx_cur]:.0f}°C',
                 xy=(K_CURRENT, flow_temps[idx_cur]),
                 xytext=(6, 6), textcoords='offset points', fontsize=9, color='tab:blue')
    y_top = ax1.get_ylim()[0] + (ax1.get_ylim()[1] - ax1.get_ylim()[0]) * 0.97
    ax1.text(K_CURRENT + 1.5, y_top, f'Current\nK={K_CURRENT}',
             fontsize=7.5, color='grey', va='top', ha='left', linespacing=1.3)

    ax2 = ax1.twinx()
    ax2.set_ylabel('COP', fontsize=12, color='tab:green')

    color2 = 'tab:green'
    line2 = ax2.plot(k_values, cops_typical, color=color2, linewidth=2, linestyle='-',
                     alpha=0.5, label=f'COP at T$_o$ = 5°C (reference)')
    line3 = ax2.plot(k_values, cops_design, color=color2, linewidth=2, linestyle='--',
                     label=f'COP at T$_o$ = {t_outdoor}°C (design)')
    line4 = ax2.axhline(y=4.67, color='red', linestyle='--', linewidth=2,
                        label='Break-even COP = 4.67')
    ax2.tick_params(axis='y', labelcolor=color2)
    ax2.set_ylim([1.5, 7.0])

    # Mark current K on both COP curves
    ax2.plot(K_CURRENT, cops_design[idx_cur], 's', color=color2, markersize=8)
    ax2.annotate(f'COP={cops_design[idx_cur]:.2f}\n(at {t_outdoor}°C)',
                 xy=(K_CURRENT, cops_design[idx_cur]),
                 xytext=(6, -20), textcoords='offset points', fontsize=8, color=color2)
    ax2.plot(K_CURRENT, cops_typical[idx_cur], 'o', color=color2, markersize=8, alpha=0.5)

    # Find and mark break-even K for design temp
    k_breakeven = None
    valid_mask = ~np.isnan(cops_design)
    if np.any(valid_mask):
        valid_k = k_values[valid_mask]
        valid_cop = cops_design[valid_mask]
        if np.any(valid_cop > 4.67):
            idx = np.where(valid_cop > 4.67)[0][0]
            if idx > 0:
                k1, k2 = valid_k[idx-1], valid_k[idx]
                cop1, cop2 = valid_cop[idx-1], valid_cop[idx]
                k_breakeven = k1 + (4.67 - cop1) * (k2 - k1) / (cop2 - cop1)
                tf_be, _ = solve_for_flow_temp(q_target, k_breakeven, vf)
                ax1.axvline(x=k_breakeven, color='red', linewidth=1.2, linestyle=':', alpha=0.8)
                ax2.plot(k_breakeven, 4.67, 'o', color='red', markersize=10,
                         markeredgecolor='black', markeredgewidth=2)
                ax1.text(k_breakeven + 2, y_top,
                         f'Break-even\nK≈{k_breakeven:.0f}\n({k_breakeven/K_CURRENT:.1f}× current)',
                         fontsize=7.5, color='red', va='top', ha='left', linespacing=1.3)
        elif valid_cop[-1] < 4.67:
            # Break-even is beyond the plotted range — annotate with arrow
            ax2.annotate('Break-even K ≈ 265\n(3.73× current, off scale →)',
                         xy=(k_range[1], valid_cop[-1]),
                         xytext=(-20, 20), textcoords='offset points',
                         fontsize=9, color='red', ha='right',
                         arrowprops=dict(arrowstyle='->', color='red'))

    fig.suptitle(f'S3: Flow Temperature and COP vs Radiator Constant\n'
                 f'(Q = {q_target/1000:.2f} kW, V$_f$ = {vf*60:.0f} l/min)', fontsize=13, y=0.98)

    lines = line1 + line2 + line3 + [line4]
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='lower right', fontsize=10)

    plt.tight_layout()
    return fig, (ax1, ax2), k_breakeven


def plot_performance_vs_k(power_levels=[1960, 2335],
                          t_outdoors=[5, 5],
                          vf=VF_FIXED,
                          k_range=(30, 130), num_points=50):
    """
    Plot 2: For given power levels, show T_f and COP vs radiator constant K.
    
    Args:
        power_levels: List of power levels [W]
        t_outdoors: List of outdoor temperatures [°C] for each power level
        vf: Flow rate [l/s]
        k_range: (min, max) K values [W/K^n]
        num_points: Number of points to calculate
    
    Returns:
        fig, (ax1, ax2): Figure and axes
        k_required: Dict mapping power levels to required K values for COP=4.67
    """
    k_values = np.linspace(k_range[0], k_range[1], num_points)
    
    # Create figure with dual y-axes
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    colors = ['blue', 'green', 'red']
    k_required = {}
    
    # Plot flow temperature on bottom axis
    color1 = 'tab:blue'
    ax1.set_xlabel('Radiator Constant K (W/K$^{1.2}$)', fontsize=12)
    ax1.set_ylabel('Flow Temperature (°C)', fontsize=12, color=color1)
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.grid(True, alpha=0.3)
    
    # Create second y-axis on top for COP
    ax2 = ax1.twinx()
    ax2.spines['top'].set_position(('axes', 1.0))
    ax2.spines['top'].set_visible(True)
    ax2.xaxis.set_ticks_position('top')
    ax2.xaxis.set_label_position('top')
    ax2.set_ylabel('COP', fontsize=12, color='tab:green')
    ax2.set_ylim([1.5, 7.0])
    
    # Plot break-even lines
    ax2.axhline(y=4.67, color='red', linestyle='--', linewidth=2, 
                label='Break-even COP = 4.67', alpha=0.9)
    ax1.axhline(y=37.1, color='tab:blue', linestyle=':', linewidth=1.2,
                alpha=0.5, label='T$_f$ = 37.1°C (break-even)')

    # Vertical line at current K
    ax1.axvline(x=K_CURRENT, color='grey', linewidth=1.2, linestyle='-', alpha=0.8)
    current_k_annotation = (K_CURRENT, 'grey', f'Current\nK={K_CURRENT}')
    
    lines_temp = []
    lines_cop = []
    linestyles = ['-', '--']  # solid for S1, dashed for S2
    scenario_labels = ['S1: 1.96 kW\n(+log burner, 5°C)', 
                      'S2: 2.34 kW\n(continuous, 5°C)']
    vline_annotations = []  # collect (k_target, color, label) for drawing after loop

    for i, (q_target, t_out) in enumerate(zip(power_levels, t_outdoors)):
        print(f"Calculating performance vs K for Q = {q_target/1000:.2f} kW at T_o = {t_out}°C...")
        
        flow_temps = []
        cops = []
        
        for k in k_values:
            tf, tr = solve_for_flow_temp(q_target, k, vf)
            if tf is not None:
                flow_temps.append(tf)
                cop = cop_estimate(t_out, tf)  # Use specific outdoor temperature
                cops.append(cop)
            else:
                flow_temps.append(np.nan)
                cops.append(np.nan)
        
        flow_temps = np.array(flow_temps)
        cops = np.array(cops)
        
        label = f'Q = {q_target/1000:.2f} kW'
        
        # Plot on both axes — blue for flow temp, green for COP
        line_t = ax1.plot(k_values, flow_temps, color='tab:blue', linewidth=2, 
                         linestyle=linestyles[i], label=f'{scenario_labels[i]} — T$_f$', alpha=0.85)
        line_c = ax2.plot(k_values, cops, color='tab:green', linewidth=2, 
                         linestyle=linestyles[i], label=f'{scenario_labels[i]} — COP', alpha=0.85)
        
        lines_temp.extend(line_t)
        lines_cop.extend(line_c)
        
        # Find intersection with COP = 4.67
        valid_mask = ~np.isnan(cops)
        if np.any(valid_mask):
            valid_k = k_values[valid_mask]
            valid_cop = cops[valid_mask]
            
            # Find where COP crosses 4.67
            if np.any(valid_cop > 4.67):
                # Interpolate to find exact K where COP = 4.67
                idx = np.where(valid_cop > 4.67)[0][0]
                if idx > 0:
                    # Linear interpolation
                    k1, k2 = valid_k[idx-1], valid_k[idx]
                    cop1, cop2 = valid_cop[idx-1], valid_cop[idx]
                    k_target = k1 + (4.67 - cop1) * (k2 - k1) / (cop2 - cop1)
                    k_required[q_target] = k_target
                    
                    # Mark on both plots — blue dot on flow temp, green dot on COP
                    tf_target, _ = solve_for_flow_temp(q_target, k_target, vf)
                    if tf_target is not None:
                        ax1.plot(k_target, tf_target, 'o', color='tab:blue', 
                               markersize=10, markeredgecolor='black', markeredgewidth=2)
                        ax2.plot(k_target, 4.67, 'o', color='tab:green', 
                               markersize=10, markeredgecolor='black', markeredgewidth=2)
                        # Vertical line at break-even K — annotation deferred until after loop
                        ax1.axvline(x=k_target, color='grey', linewidth=0.9, linestyle=':', alpha=0.7)
                        vline_annotations.append((k_target, 'grey', scenario_labels[i]))

    # Draw vertical-line annotations now that ylim is finalised
    y_top = ax1.get_ylim()[0] + (ax1.get_ylim()[1] - ax1.get_ylim()[0]) * 0.97
    # Current K annotation
    k_ann, col, lbl = current_k_annotation
    ax1.text(k_ann + 0.8, y_top, lbl,
             fontsize=7.5, color=col, va='top', ha='left', linespacing=1.3)
    for k_ann, col, lbl in vline_annotations:
        ax1.text(k_ann + 0.8, y_top,
                 f'{lbl}\nK≈{k_ann:.0f}',
                 fontsize=7.5, color=col, va='top', ha='left', linespacing=1.3)
    
    # Title
    fig.suptitle(f'S1 & S2: Flow Temperature and COP vs Radiator Constant\n(V$_f$ = {vf*60:.0f} l/min, T$_o$ = 5°C)', 
                fontsize=13, y=0.98)
    
    # Combined legend: flow temp (blue) and COP (green) distinct by linestyle
    temp_legend = ax1.legend([l for l in lines_temp],
                             [l.get_label() for l in lines_temp],
                             loc='lower right', fontsize=9, title='Flow Temp (blue)')
    ax1.add_artist(temp_legend)
    ax2.legend([l for l in lines_cop] + [ax2.get_lines()[-1]],
               [l.get_label() for l in lines_cop] + ['Break-even COP = 4.67'],
               loc='upper right', fontsize=9, title='COP (green)')
    
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
    
    # Plot 2a: Performance vs K for S1 and S2 at typical winter temperature
    print("\n2. Generating performance vs K plot (S1 & S2)...")
    fig2, _, k_required = plot_performance_vs_k(power_levels=[1960, 2335],
                                                 t_outdoors=[5, 5],
                                                 k_range=(30, 130))
    fig2.savefig('assets/performance_vs_k.png', dpi=150, bbox_inches='tight')
    print("   Saved: assets/performance_vs_k.png")

    # Plot 2b: Performance vs K for S3 at design temperature (-2°C), wide K range
    print("\n3. Generating performance vs K plot (S3 design temp)...")
    fig3, _, k_be = plot_performance_vs_k_design_temp(q_target=3650, t_outdoor=-2,
                                                       k_range=(30, 300))
    fig3.savefig('assets/performance_vs_k_s3.png', dpi=150, bbox_inches='tight')
    print("   Saved: assets/performance_vs_k_s3.png")
    
    # Print required K values
    print("\n" + "=" * 60)
    print("REQUIRED RADIATOR CONSTANTS FOR COP = 4.67")
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
        print(f"To handle peak load of 3.12 kW at COP = 4.67:")
        print(f"  Required K ≈ {k_peak:.0f} W/K^{N_RAD}")
        print(f"  This is approximately {factor_peak:.1f}× current capacity")
        print("=" * 60)


if __name__ == '__main__':
    main()
