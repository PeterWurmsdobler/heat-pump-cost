"""
Simulate gas boiler heating with modulating controller following the profile:
- Off 22h to 6h (house cools via: C*dT_i/dt = -h*(T_i - T_o))
- Setpoint 19°C from 6h to 9h (full power up to setpoint, then feed-forward)
- Setpoint 15°C from 9h to 17h (full power up to setpoint, then feed-forward)
- Setpoint 19°C from 17h to 22h (full power up to setpoint, then feed-forward)

Start at 22h with T_i = 19°C, run for 24 hours.

Model integrates piecewise from initial conditions using corrected parameters:
  C = 54.9 MJ/K (from April 4, 2026 fitted decay curve with FIXED T0=T_o)
  h = 244 W/K (from building thermal model)
  τ = C/h = 62.50 h (time constant, fitted correctly)
  T_o = 7°C (April outdoor temperature during measurement)

CRITICAL FIX: The thermal capacity C was corrected from 2.01 MJ/K to 54.9 MJ/K
by properly constraining the curve fit to T0 = T_o. The original fit allowed T0
to float to 19.6°C (intermediate value in the measurement window), leading to
a 27× underestimation of the house's actual thermal mass.
"""

import numpy as np
import matplotlib.pyplot as plt
from heat_pump_cost.dynamic_thermal_model import DynamicThermalModel, ThermalSystemParameters


def get_heating_mode(t):
    """
    Determine heating mode and setpoint at time t.
    
    Args:
        t: Current time [s] (0 = 22h starting day)
    
    Returns:
        Tuple of (heating_on, setpoint_temp) where:
          heating_on: bool, True if heating should be active
          setpoint_temp: float, target temperature [°C]
    """
    # Define schedule (times in seconds from 22h start)
    t_6h = 8 * 3600      # 28800 s
    t_9h = 11 * 3600     # 39600 s
    t_17h = 19 * 3600    # 68400 s
    t_22h = 24 * 3600    # 86400 s
    
    if t < t_6h or t >= t_22h:
        # 22h to 6h: heating OFF
        return False, None
    elif t_6h <= t < t_9h:
        # 6h to 9h: T_s = 19°C
        return True, 19.0
    elif t_9h <= t < t_17h:
        # 9h to 17h: T_s = 15°C
        return True, 15.0
    else:  # t_17h <= t < t_22h
        # 17h to 22h: T_s = 19°C
        return True, 19.0


def modulating_controller(t, T_i, T_s, T_o=7.0, h=244.0, Q_max=6000.0):
    """
    Modulating controller: full power until setpoint, then feed-forward to maintain.
    
    Args:
        t: Current time [s] (unused, for consistency)
        T_i: Current indoor temperature [°C]
        T_s: Setpoint temperature [°C] (or None if heating off)
        T_o: Outdoor temperature [°C]
        h: Heat transfer coefficient [W/K]
        Q_max: Maximum heating power [W]
    
    Returns:
        Heating power [W]
    """
    if T_s is None:
        # Heating is off
        return 0.0
    
    # Modulating control: full power until setpoint, then feed-forward to maintain
    if T_i < T_s:
        # Below setpoint: apply full power
        return Q_max
    else:
        # At or above setpoint: apply feed-forward power to maintain
        # Q_h = h * (T_s - T_o)
        Q_ff = h * (T_s - T_o)
        return max(0.0, Q_ff)  # Ensure non-negative


def simulate_gas_boiler():
    """
    Simulate a full day of gas boiler operation with modulating control.
    
    Integrates the differential equation piecewise from initial conditions:
      dT_i/dt = (Q_r - Q_l) / C
    
    where:
      Q_r = radiator power (depends on T_f, T_r, T_i)
      Q_l = heat loss = h * (T_i - T_o)
      C = thermal capacity = 2.01 MJ/K
      h = heat transfer coefficient = 244 W/K
      T_o = outdoor temperature = 7°C (April conditions from measurement)
    """
    
    # Create model with parameters from fitted April 4, 2026 data
    model = DynamicThermalModel()
    
    # Use the corrected parameters from the model
    # T_o = 7°C (April measurement conditions)
    # C = 54.9 MJ/K (corrected via proper curve fitting with fixed T0)
    # h = 244 W/K
    T_o = model.params.T_o  # Outdoor temperature [°C]
    
    # Radiators with K=44.9 can deliver max ~6 kW at 80°C flow
    Q_boiler_max = 6000.0  # Realistic max for these radiators [W]
    
    # Start conditions
    T_i_0 = 19.0  # Initial indoor temperature at 22h [°C]
    t_start = 0.0
    t_end = 24 * 3600  # 24 hours in seconds
    dt = 120  # Integration step: 2 minutes
    
    # Time array
    t_eval = np.arange(t_start, t_end + dt, dt)
    
    # Storage for results
    T_i_vals = [T_i_0]
    T_f_vals = []
    Q_r_vals = []
    Q_l_vals = []
    Q_h_vals = []
    t_vals = [t_start]
    
    # Integrate step by step from initial condition
    T_i_current = T_i_0
    failed_solves = 0
    successful_solves = 0
    
    for i in range(1, len(t_eval)):
        t_prev = t_vals[-1]
        t_curr = t_eval[i]
        dt_step = t_curr - t_prev
        
        # Step 1: Determine heating mode and setpoint at current time
        heating_on, T_s = get_heating_mode(t_curr)
        
        # Step 2: Compute heating power from controller
        Q_h = modulating_controller(t_curr, T_i_current, T_s, T_o=T_o, 
                                     h=model.params.h, Q_max=Q_boiler_max)
        Q_h_vals.append(Q_h)
        
        # Step 3: Compute radiator output Q_r and flow temperature T_f
        if Q_h > 100.0:  # Only attempt solver if heating power is significant
            # Solve for flow temperature needed to deliver Q_h
            T_f = model.solve_flow_temp(Q_h, T_i_current, T_f_guess=T_i_current + 20.0)
            if T_f is None or T_f < T_i_current or T_f > 150.0:
                # If no valid solution, treat as zero radiator power
                T_f = T_i_current
                Q_r = 0.0
                failed_solves += 1
            else:
                # Solve for return temperature from Q_h = Q_r balance
                T_r = model.solve_return_temp(T_f, T_i_current)
                if T_r is None or T_r < T_i_current or T_r >= T_f:
                    Q_r = 0.0
                    failed_solves += 1
                else:
                    Q_r = model.radiator_power(T_f, T_r, T_i_current)
                    successful_solves += 1
        else:
            T_f = T_i_current
            Q_r = 0.0
        
        T_f_vals.append(T_f)
        Q_r_vals.append(Q_r)
        
        # Step 4: Compute heat loss (always present)
        Q_l = model.params.h * (T_i_current - T_o)
        Q_l_vals.append(Q_l)
        
        # Step 5: Integrate ODE forward: dT_i/dt = (Q_r - Q_l) / C
        dT_i_dt = (Q_r - Q_l) / model.params.C
        T_i_next = T_i_current + dT_i_dt * dt_step
        
        # Store results
        T_i_vals.append(T_i_next)
        t_vals.append(t_curr)
        T_i_current = T_i_next
    
    # Convert to arrays and time to hours for plotting
    t_vals = np.array(t_vals)
    T_i_vals = np.array(T_i_vals)
    T_f_vals = np.array(T_f_vals)
    Q_r_vals = np.array(Q_r_vals)
    Q_l_vals = np.array(Q_l_vals)
    Q_h_vals = np.array(Q_h_vals)
    t_hours = t_vals / 3600.0
    
    # Get setpoint array for plotting
    T_s_vals = np.array([get_heating_mode(t)[1] for t in t_vals])
    
    # Create plots
    fig, axes = plt.subplots(4, 1, figsize=(14, 12))
    
    # Plot 1: Indoor temperature and setpoint
    axes[0].plot(t_hours, T_i_vals, 'b-', linewidth=2.5, label='Indoor temperature T_i')
    # Plot setpoint as a step function
    setpoint_t = [0, 8, 8, 9, 9, 17, 17, 24]
    setpoint_T = [np.nan, np.nan, 19, 19, 15, 15, 19, 19]
    axes[0].plot(setpoint_t, setpoint_T, 'r--', linewidth=2, label='Setpoint T_s', alpha=0.7)
    axes[0].axhline(T_o, color='gray', linestyle=':', linewidth=1.5, label=f'Outdoor T_o = {T_o}°C')
    axes[0].set_ylabel('Temperature (°C)', fontsize=11)
    axes[0].set_title('Modulating Gas Boiler Space Heating Profile (22h start, T_i(0) = 19°C)', 
                     fontsize=13, fontweight='bold')
    axes[0].legend(fontsize=10, loc='best')
    axes[0].grid(True, alpha=0.3)
    axes[0].set_xlim(0, 24)
    
    # Plot 2: Flow temperature
    axes[1].plot(t_hours[1:], T_f_vals, 'orange', linewidth=2, label='Flow temperature T_f')
    axes[1].set_ylabel('Temperature (°C)', fontsize=11)
    axes[1].legend(fontsize=10)
    axes[1].grid(True, alpha=0.3)
    axes[1].set_xlim(0, 24)
    
    # Plot 3: Power balance
    axes[2].plot(t_hours[1:], Q_r_vals / 1000.0, 'g-', linewidth=2.5, label='Radiator power Q_r')
    axes[2].plot(t_hours[1:], Q_l_vals / 1000.0, 'purple', linewidth=2, label='Heat loss Q_l')
    axes[2].plot(t_hours[1:], Q_h_vals / 1000.0, 'r--', linewidth=2, label='Control input Q_h', 
                alpha=0.7, drawstyle='steps-pre')
    axes[2].set_ylabel('Power (kW)', fontsize=11)
    axes[2].legend(fontsize=10)
    axes[2].grid(True, alpha=0.3)
    axes[2].set_xlim(0, 24)
    
    # Plot 4: Control input (heating on/off + level)
    axes[3].plot(t_hours[1:], Q_h_vals / 1000.0, 'b-', linewidth=2, label='Heating power Q_h', 
                drawstyle='steps-pre')
    axes[3].fill_between(t_hours[1:], 0, Q_h_vals / 1000.0, alpha=0.3, step='pre')
    axes[3].set_xlabel('Time (hours from 22:00)', fontsize=11)
    axes[3].set_ylabel('Power (kW)', fontsize=11)
    axes[3].set_ylim(0, 7)
    axes[3].legend(fontsize=10)
    axes[3].grid(True, alpha=0.3)
    axes[3].set_xlim(0, 24)
    
    # Add time labels at top
    time_labels = ['22:00', '06:00', '09:00', '17:00', '22:00']
    time_positions = [0, 8, 11, 19, 24]
    for ax in axes:
        ax.set_xticks(time_positions)
        ax.set_xticklabels(time_labels)
    
    plt.tight_layout()
    plt.savefig('gas_boiler_simulation.png', dpi=150, bbox_inches='tight')
    print("Plot saved to gas_boiler_simulation.png")
    
    # Print summary statistics
    print("\n" + "="*60)
    print("GAS BOILER SIMULATION SUMMARY")
    print("="*60)
    print(f"Starting time: 22:00, Initial T_i = {T_i_0}°C")
    print(f"Simulation duration: 24 hours")
    print(f"Outdoor temperature: {T_o}°C (constant, from April measurement)")
    print(f"Thermal capacity: C = {model.params.C/1e6:.2f} MJ/K (from fitted decay model)")
    print(f"Heat transfer coeff: h = {model.params.h} W/K")
    print(f"Time constant: τ = C/h = {model.params.C/model.params.h/3600:.3f} h")
    print(f"Radiator constant: K = {model.params.K} W/K^{model.params.n}")
    print(f"Maximum boiler power: {Q_boiler_max/1000:.1f} kW (limited by radiator capacity)")
    print(f"\nTemperature statistics:")
    print(f"  T_i min: {T_i_vals.min():.2f}°C, max: {T_i_vals.max():.2f}°C, final: {T_i_vals[-1]:.2f}°C")
    print(f"  T_f min: {T_f_vals.min():.2f}°C, max: {T_f_vals.max():.2f}°C")
    print(f"\nEnergy statistics:")
    print(f"  Total heat delivered (Q_r): {np.sum(Q_r_vals[1:]) * dt / 3.6e6:.2f} kWh")
    print(f"  Total heat loss (Q_l): {np.sum(Q_l_vals[1:]) * dt / 3.6e6:.2f} kWh")
    print(f"  Peak radiator power: {Q_r_vals.max() / 1000:.2f} kW")
    print(f"  Peak flow temperature: {T_f_vals.max():.2f}°C")
    print(f"\nSolver statistics:")
    print(f"  Successful flow temp solves: {successful_solves}")
    print(f"  Failed flow temp solves: {failed_solves}")
    print("="*60 + "\n")
    
    return {
        't': t_vals,
        'T_i': T_i_vals,
        'T_f': T_f_vals,
        'Q_r': Q_r_vals,
        'Q_l': Q_l_vals,
        'Q_h': Q_h_vals,
    }


def get_setpoint(t, t_6h=28800, t_9h=39600, t_17h=68400, t_22h=86400):
    """Legacy function for setpoint. Returns None for plotting compatibility."""
    heating_on, T_s = get_heating_mode(t)
    return T_s
    
    return {
        't': t_vals,
        'T_i': T_i_vals,
        'T_f': T_f_vals,
        'Q_r': Q_r_vals,
        'Q_l': Q_l_vals,
        'Q_h': Q_h_vals,
    }


if __name__ == '__main__':
    result = simulate_gas_boiler()
