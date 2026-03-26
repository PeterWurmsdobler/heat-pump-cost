"""
Quantitative model for heat pump operation in steady state.

This module solves the coupled heat flow equations for a simple lumped-mass
model of a house to show the relationship between flow temperature, flow rate,
and heating power delivery.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import fsolve
from mpl_toolkits.mplot3d import Axes3D


# Physical constants
RHO = 1.0  # Water density [kg/l]
CP = 4180.0  # Specific heat capacity of water [J/kg/K]

# House thermal properties
HTC = 244.0  # Heat Transfer Coefficient [W/K]
TI = 18.0  # Indoor temperature [°C] (January 2026 average)
TO = 5.0  # Outdoor temperature [°C] (January 2026 average)

# Radiator properties
# Empirically calibrated from January 2026 actual operation:
# - Average heating power: 2.0 kW at Ti=18°C, To=5°C
# - Observed mean radiator temp: ~47.5°C
# - This includes all radiators + pipework heat distribution
K_RAD = 34.6  # Empirical radiator constant [W/K^n]
N_RAD = 1.2  # Radiator exponent

# Target heating power (actual average from January 2026)
Q_TARGET = 2000.0  # [W] = 2.0 kW average space heating from radiators


def radiator_power(tf, tr, ti=TI):
    """
    Calculate radiator heat output.
    
    Qr = K * ((Tf + Tr)/2 - Ti)^n
    
    Args:
        tf: Flow temperature [°C]
        tr: Return temperature [°C]
        ti: Indoor temperature [°C]
    
    Returns:
        Radiator power output [W]
    """
    t_mean = (tf + tr) / 2.0
    delta_t = t_mean - ti
    
    # Handle negative temperature differences (shouldn't happen in normal operation)
    if delta_t <= 0:
        return 0.0
    
    return K_RAD * (delta_t ** N_RAD)


def flow_power(vf, tf, tr):
    """
    Calculate power delivered by flow.
    
    Qh = Vf * rho * cp * (Tf - Tr)
    
    Args:
        vf: Flow rate [l/s]
        tf: Flow temperature [°C]
        tr: Return temperature [°C]
    
    Returns:
        Flow power [W]
    """
    return vf * RHO * CP * (tf - tr)


def solve_return_temp(vf, tf, ti=TI):
    """
    Solve for return temperature given flow rate and flow temperature.
    
    In steady state, Qh = Qr:
    Vf * rho * cp * (Tf - Tr) = K * ((Tf + Tr)/2 - Ti)^n
    
    Args:
        vf: Flow rate [l/s]
        tf: Flow temperature [°C]
        ti: Indoor temperature [°C]
    
    Returns:
        Return temperature [°C], or None if no solution exists
    """
    if vf <= 0:
        return None
    
    def equation(tr):
        """Equation to solve: Qh - Qr = 0"""
        qh = flow_power(vf, tf, tr)
        qr = radiator_power(tf, tr, ti)
        return qh - qr
    
    # Initial guess: assume some temperature drop
    tr_guess = tf - 10.0
    
    try:
        # Solve the equation
        solution = fsolve(equation, tr_guess, full_output=True)
        tr = solution[0][0]
        info = solution[1]
        
        # Check if solution converged and is physical
        if info['fvec'][0]**2 < 1e-6 and ti < tr < tf:
            return tr
        else:
            return None
    except:
        return None


def calculate_heating_power(vf, tf, ti=TI):
    """
    Calculate total heating power for given flow rate and flow temperature.
    
    Args:
        vf: Flow rate [l/s]
        tf: Flow temperature [°C]
        ti: Indoor temperature [°C]
    
    Returns:
        Heating power [W], or NaN if no valid solution exists
    """
    tr = solve_return_temp(vf, tf, ti)
    
    if tr is None:
        return np.nan
    
    # Calculate power from flow equation (should equal radiator power)
    q = flow_power(vf, tf, tr)
    
    return q


def create_3d_plot(vf_range=(0.01, 20.0/60.0), tf_range=(35.0, 70.0), num_points=50):
    """
    Create a 3D surface plot of heating power Q as a function of Vf and Tf.
    
    Args:
        vf_range: Tuple of (min, max) flow rates [l/s]
        tf_range: Tuple of (min, max) flow temperatures [°C]
        num_points: Number of grid points in each dimension
    
    Returns:
        fig, ax: Matplotlib figure and axes objects
    """
    # Create grid
    vf_values = np.linspace(vf_range[0], vf_range[1], num_points)
    tf_values = np.linspace(tf_range[0], tf_range[1], num_points)
    
    VF, TF = np.meshgrid(vf_values, tf_values)
    Q = np.zeros_like(VF)
    
    # Calculate Q for each grid point
    print("Calculating heating power grid...")
    for i in range(len(tf_values)):
        for j in range(len(vf_values)):
            Q[i, j] = calculate_heating_power(vf_values[j], tf_values[i])
    
    # Convert to kW for plotting
    Q_kw = Q / 1000.0
    
    # Convert x-axis to l/min for display
    VF_min = VF * 60.0
    
    # Create 3D plot
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # Plot surface (using l/min for display)
    surf = ax.plot_surface(VF_min, TF, Q_kw, cmap='viridis', alpha=0.8, edgecolor='none')
    
    # Add contour lines at base
    contours = ax.contour(VF_min, TF, Q_kw, levels=10, cmap='viridis', linestyles='solid', 
                          offset=0, zdir='z')
    
    # Mark the target power level
    target_kw = Q_TARGET / 1000.0
    ax.contour(VF_min, TF, Q_kw, levels=[target_kw], colors='red', linewidths=2, 
               linestyles='solid', offset=0, zdir='z')
    
    # Labels and title
    ax.set_xlabel('Flow Rate (l/min)', fontsize=12)
    ax.set_ylabel('Flow Temperature (°C)', fontsize=12)
    ax.set_zlabel('Heating Power (kW)', fontsize=12)
    ax.set_title('Steady State Heating Power vs Flow Rate and Temperature', fontsize=14)
    
    # Add colorbar
    fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5, label='Heating Power (kW)')
    
    # Set viewing angle
    ax.view_init(elev=20, azim=45)
    
    return fig, ax


def create_contour_plot(target_power=Q_TARGET, vf_range=(0.01, 20.0/60.0), 
                       tf_range=(35.0, 70.0), num_points=100):
    """
    Create a 2D contour plot showing Tf vs Vf for constant heating power.
    
    Args:
        target_power: Target heating power [W]
        vf_range: Tuple of (min, max) flow rates [l/s]
        tf_range: Tuple of (min, max) flow temperatures [°C]
        num_points: Number of grid points in each dimension
    
    Returns:
        fig, ax: Matplotlib figure and axes objects
    """
    # Create grid
    vf_values = np.linspace(vf_range[0], vf_range[1], num_points)
    tf_values = np.linspace(tf_range[0], tf_range[1], num_points)
    
    VF, TF = np.meshgrid(vf_values, tf_values)
    Q = np.zeros_like(VF)
    
    # Calculate Q for each grid point
    print(f"Calculating contour for Q = {target_power/1000:.2f} kW...")
    for i in range(len(tf_values)):
        for j in range(len(vf_values)):
            Q[i, j] = calculate_heating_power(vf_values[j], tf_values[i])
    
    # Convert to kW
    Q_kw = Q / 1000.0
    target_kw = target_power / 1000.0
    
    # Convert x-axis to l/min for display
    VF_min = VF * 60.0
    
    # Create 2D plot
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Plot filled contours
    contourf = ax.contourf(VF_min, TF, Q_kw, levels=20, cmap='viridis', alpha=0.6)
    
    # Plot contour lines
    contours = ax.contour(VF_min, TF, Q_kw, levels=10, colors='black', alpha=0.3, linewidths=0.5)
    ax.clabel(contours, inline=True, fontsize=8, fmt='%.1f kW')
    
    # Highlight the target power contour
    target_contour = ax.contour(VF_min, TF, Q_kw, levels=[target_kw], colors='red', 
                                linewidths=3, linestyles='solid')
    ax.clabel(target_contour, inline=True, fontsize=10, fmt=f'{target_kw:.1f} kW')
    
    # Labels and title
    ax.set_xlabel('Flow Rate (l/min)', fontsize=12)
    ax.set_ylabel('Flow Temperature (°C)', fontsize=12)
    ax.set_title(f'Flow Temperature vs Flow Rate\n(Red line shows Q = {target_kw:.1f} kW)', 
                 fontsize=14)
    ax.grid(True, alpha=0.3)
    
    # Add colorbar
    cbar = fig.colorbar(contourf, ax=ax, label='Heating Power (kW)')
    
    return fig, ax


def extract_target_curve(target_power=Q_TARGET, vf_range=(0.01, 20.0/60.0), 
                        tf_range=(35.0, 70.0), num_points=100):
    """
    Extract the curve Tf(Vf) for a specific target power.
    
    Args:
        target_power: Target heating power [W]
        vf_range: Tuple of (min, max) flow rates [l/s]
        tf_range: Tuple of (min, max) flow temperatures [°C]
        num_points: Number of points to sample
    
    Returns:
        vf_curve, tf_curve: Arrays of flow rates and corresponding flow temperatures
    """
    vf_values = np.linspace(vf_range[0], vf_range[1], num_points)
    tf_curve = []
    vf_curve = []
    
    print(f"Extracting Tf(Vf) curve for Q = {target_power/1000:.2f} kW...")
    
    for vf in vf_values:
        # For this flow rate, find the flow temperature that gives target power
        def objective(tf):
            q = calculate_heating_power(vf, tf)
            if np.isnan(q):
                return 1e9
            return abs(q - target_power)
        
        from scipy.optimize import minimize_scalar
        
        result = minimize_scalar(objective, bounds=tf_range, method='bounded')
        
        if result.fun < 100:  # Within 100W of target
            tf_solution = result.x
            vf_curve.append(vf)
            tf_curve.append(tf_solution)
    
    return np.array(vf_curve), np.array(tf_curve)


def plot_target_curve(target_power=Q_TARGET, vf_range=(0.01, 20.0/60.0), tf_range=(35.0, 70.0)):
    """
    Create a simple 2D plot showing Tf as a function of Vf for target power.
    
    Args:
        target_power: Target heating power [W]
        vf_range: Tuple of (min, max) flow rates [l/s]
        tf_range: Tuple of (min, max) flow temperatures [°C]
    
    Returns:
        fig, ax: Matplotlib figure and axes objects
    """
    vf_curve, tf_curve = extract_target_curve(target_power, vf_range, tf_range)
    
    target_kw = target_power / 1000.0
    
    # Convert to l/min for display
    vf_curve_min = vf_curve * 60.0
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.plot(vf_curve_min, tf_curve, 'b-', linewidth=2, label=f'Q = {target_kw:.1f} kW')
    ax.scatter(vf_curve_min, tf_curve, c='blue', s=20, alpha=0.5)
    
    ax.set_xlabel('Flow Rate (l/min)', fontsize=12)
    ax.set_ylabel('Flow Temperature (°C)', fontsize=12)
    ax.set_title(f'Required Flow Temperature vs Flow Rate for Q = {target_kw:.1f} kW', 
                 fontsize=14)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=11)
    
    # Add some annotations for key points
    if len(vf_curve_min) > 0:
        # Annotate first point (low flow rate, high temp)
        ax.annotate(f'Low flow: {vf_curve_min[0]:.1f} l/min, {tf_curve[0]:.1f}°C',
                   xy=(vf_curve_min[0], tf_curve[0]),
                   xytext=(vf_curve_min[0] + 2, tf_curve[0] + 3),
                   arrowprops=dict(arrowstyle='->', color='red'),
                   fontsize=9, color='red')
        
        # Annotate last point (high flow rate, low temp)
        ax.annotate(f'High flow: {vf_curve_min[-1]:.1f} l/min, {tf_curve[-1]:.1f}°C',
                   xy=(vf_curve_min[-1], tf_curve[-1]),
                   xytext=(vf_curve_min[-1] - 2, tf_curve[-1] + 3),
                   arrowprops=dict(arrowstyle='->', color='red'),
                   fontsize=9, color='red')
    
    return fig, ax


def run_operations_analysis(output_dir='assets'):
    """
    Run the complete operations analysis and save plots.
    
    Args:
        output_dir: Directory to save output plots
    """
    import os
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    print("="*70)
    print("Heat Pump Operations Analysis")
    print("="*70)
    print(f"\nPhysical Constants:")
    print(f"  Water density (rho): {RHO} kg/l")
    print(f"  Specific heat (cp): {CP} J/kg/K")
    print(f"\nHouse Properties:")
    print(f"  Heat Transfer Coefficient (h): {HTC} W/K")
    print(f"  Indoor temperature (Ti): {TI}°C")
    print(f"  Outdoor temperature (To): {TO}°C")
    print(f"  Required heating power: {Q_TARGET/1000:.2f} kW")
    print(f"\nRadiator Properties:")
    print(f"  Radiator constant (K): {K_RAD} W/K^{N_RAD}")
    print(f"  Radiator exponent (n): {N_RAD}")
    print("="*70)
    
    # Create 3D plot
    print("\n1. Creating 3D surface plot...")
    fig_3d, ax_3d = create_3d_plot()
    output_path_3d = os.path.join(output_dir, 'operations_3d_surface.png')
    fig_3d.savefig(output_path_3d, dpi=150, bbox_inches='tight')
    print(f"   Saved: {output_path_3d}")
    
    # Create contour plot
    print("\n2. Creating contour plot...")
    fig_contour, ax_contour = create_contour_plot()
    output_path_contour = os.path.join(output_dir, 'operations_contour.png')
    fig_contour.savefig(output_path_contour, dpi=150, bbox_inches='tight')
    print(f"   Saved: {output_path_contour}")
    
    # Create target curve plot
    print("\n3. Creating Tf(Vf) curve plot...")
    fig_curve, ax_curve = plot_target_curve()
    output_path_curve = os.path.join(output_dir, 'operations_tf_vs_vf.png')
    fig_curve.savefig(output_path_curve, dpi=150, bbox_inches='tight')
    print(f"   Saved: {output_path_curve}")
    
    print("\n" + "="*70)
    print("Analysis complete!")
    print("="*70)
    
    # Show plots
    plt.show()


if __name__ == '__main__':
    run_operations_analysis()
