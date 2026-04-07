"""
Dynamic thermal model for heat pump space heating system.

Solves the coupled differential equations:
- Q_h = V_f * ρ * c_p * (T_f - T_r)
- Q_r = K * ((T_f + T_r)/2 - T_i)^n
- Q_h = Q_r (heat balance in radiator circuit)
- Q_l = h * (T_i - T_o)
- C * dT_i/dt = Q_r - Q_l

with state variable T_i (indoor temperature) and solving for T_f (flow temperature)
given a control input at each timestep.
"""

from __future__ import annotations

from typing import Callable, Sequence
from dataclasses import dataclass

import numpy as np
from scipy.integrate import solve_ivp, odeint
from scipy.optimize import fsolve, brentq


@dataclass
class ThermalSystemParameters:
    """Parameters for the dynamic thermal model."""

    # Water properties
    rho: float = 1.0       # Water density [kg/l]
    cp: float = 4180.0     # Specific heat capacity of water [J/kg/K]

    # House thermal properties – identified from April 2026 decay/heating experiments
    # (Q_r = 4 kW for Period 3; h_sigma = 500 allowing data to constrain h freely)
    h: float = 142.6       # Heat Transfer Coefficient [W/K]
    C: float = 21.0e6      # Thermal capacity [J/K]  (21.0 MJ/K)
    Q_b: float = 500.0     # Background heat – appliances / occupancy [W]

    # Radiator properties
    K: float = 44.9        # Radiator constant [W/K^n]
    n: float = 1.2         # Radiator exponent

    # Flow rate
    V_f: float = 20.0 / 60.0  # Flow rate [l/s] (20 l/min)

    # Environmental – January 2026 average for simulations
    T_o: float = 5.0       # Outdoor temperature [°C]


class DynamicThermalModel:
    """Solver for the dynamic thermal system."""
    
    def __init__(self, params: ThermalSystemParameters | None = None):
        """Initialize the model with parameters."""
        self.params = params or ThermalSystemParameters()
    
    def radiator_power(self, T_f: float, T_r: float, T_i: float) -> float:
        """Calculate radiator heat output Q_r = K * ((T_f + T_r)/2 - T_i)^n."""
        T_mean = (T_f + T_r) / 2.0
        delta_T = T_mean - T_i
        if delta_T <= 0:
            return 0.0
        return self.params.K * (delta_T ** self.params.n)
    
    def flow_power(self, T_f: float, T_r: float) -> float:
        """Calculate power delivered by flow Q_h = V_f * ρ * c_p * (T_f - T_r)."""
        return self.params.V_f * self.params.rho * self.params.cp * (T_f - T_r)
    
    def heat_loss(self, T_i: float) -> float:
        """Calculate heat loss Q_l = h * (T_i - T_o)."""
        return self.params.h * (T_i - self.params.T_o)
    
    def solve_return_temp(self, T_f: float, T_i: float) -> float | None:
        """
        Solve for return temperature T_r given flow temperature T_f and indoor temperature T_i.
        
        Uses the heat balance: Q_h = Q_r
        V_f * ρ * c_p * (T_f - T_r) = K * ((T_f + T_r)/2 - T_i)^n
        
        Args:
            T_f: Flow temperature [°C]
            T_i: Indoor temperature [°C]
        
        Returns:
            Return temperature [°C], or None if no valid solution
        """
        if T_f <= T_i:
            return None
        
        def equation(T_r):
            Q_h = self.flow_power(T_f, T_r)
            Q_r = self.radiator_power(T_f, T_r, T_i)
            return Q_h - Q_r
        
        # Initial guess: some temperature drop
        T_r_guess = T_f - 10.0
        
        try:
            solution = fsolve(equation, T_r_guess, full_output=True)
            T_r = solution[0][0]
            info = solution[1]
            
            # Check convergence and physical plausibility
            if info['fvec'][0]**2 < 1e-6 and T_i < T_r < T_f:
                return T_r
            else:
                return None
        except Exception:
            return None
    
    def solve_flow_temp(self, Q_target: float, T_i: float, T_f_guess: float | None = None) -> float | None:
        """
        Solve for flow temperature T_f needed to deliver target heating power Q_target.
        
        Uses direct search with physically realistic bounds (20°C to 80°C).
        
        Args:
            Q_target: Target heating power [W]
            T_i: Indoor temperature [°C]
            T_f_guess: Initial guess for T_f [°C] (ignored, for compatibility)
        
        Returns:
            Flow temperature [°C], or None if no solution found
        """
        if Q_target <= 0:
            return None
        
        # Search for T_f that produces Q_target with realistic bounds (20-80°C)
        best_T_f = None
        best_error = float('inf')
        
        for T_f in np.linspace(T_i + 1.0, min(T_i + 65.0, 80.0), 300):
            T_r = self.solve_return_temp(T_f, T_i)
            if T_r is None or T_r >= T_f or T_r <= T_i:
                continue
            
            Q_r = self.radiator_power(T_f, T_r, T_i)
            error = abs(Q_r - Q_target)
            
            if error < best_error:
                best_error = error
                best_T_f = T_f
                
                # If close enough (within 1% or 50W), return immediately
                if error < max(Q_target * 0.01, 50.0):
                    return T_f
        
        # Return best match if within 2% tolerance
        if best_T_f is not None and best_error < max(Q_target * 0.02, 100.0):
            return best_T_f
        
        return None
    
    def _dT_i_dt(self, T_i: float, t: float, Q_control: Callable[[float], float]) -> float:
        """
        Compute dT_i/dt given current state and control input.
        
        Args:
            T_i: Indoor temperature [°C]
            t: Time [s]
            Q_control: Function that returns target heating power Q_h [W] at time t
        
        Returns:
            dT_i/dt [K/s]
        """
        Q_target = Q_control(t)
        
        # Solve for required flow temperature
        T_f = self.solve_flow_temp(Q_target, T_i)
        if T_f is None:
            # If no solution, assume heating is off
            T_r = T_i  # Return temp equals supply for no heating
            Q_r = 0.0
        else:
            T_r = self.solve_return_temp(T_f, T_i)
            if T_r is None:
                Q_r = 0.0
            else:
                Q_r = self.radiator_power(T_f, T_r, T_i)
        
        Q_l = self.heat_loss(T_i)
        dT_i_dt = (Q_r + self.params.Q_b - Q_l) / self.params.C

        return dT_i_dt
    
    def integrate(
        self,
        T_i_0: float,
        t_span: tuple[float, float],
        t_eval: Sequence[float] | None = None,
        Q_control: Callable[[float], float] | None = None,
        dense_output: bool = False,
        rtol: float = 1e-6,
        atol: float = 1e-8,
    ) -> dict:
        """
        Integrate the dynamic thermal model over time.
        
        Args:
            T_i_0: Initial indoor temperature [°C]
            t_span: (t_start, t_end) for integration [s]
            t_eval: Times at which to return solution [s]. If None, auto-generated.
            Q_control: Function Q_control(t) returning heating power [W]. 
                      If None, heating is off (Q = 0).
            dense_output: If True, return a callable for interpolation.
            rtol: Relative tolerance for ODE solver
            atol: Absolute tolerance for ODE solver
        
        Returns:
            Dictionary with keys:
            - 't': Time array [s]
            - 'T_i': Indoor temperature array [°C]
            - 'T_f': Flow temperature array [°C]
            - 'Q_r': Radiator power array [W]
            - 'Q_l': Heat loss array [W]
            - 'sol': ODE solution object (if dense_output=True)
        """
        if Q_control is None:
            Q_control = lambda t: 0.0
        
        if t_eval is None:
            t_eval = np.linspace(t_span[0], t_span[1], 1000)
        
        # Define the ODE function
        def ode_func(t, y):
            T_i = y[0]
            return [self._dT_i_dt(T_i, t, Q_control)]
        
        # Solve ODE
        sol = solve_ivp(
            ode_func,
            t_span,
            [T_i_0],
            t_eval=t_eval,
            dense_output=dense_output,
            rtol=rtol,
            atol=atol,
            method='RK45'
        )
        
        # Post-process: compute flow temperatures and powers at eval times
        T_i_vals = sol.y[0]
        T_f_vals = np.zeros_like(T_i_vals)
        Q_r_vals = np.zeros_like(T_i_vals)
        Q_l_vals = np.zeros_like(T_i_vals)
        
        for i, t in enumerate(sol.t):
            T_i = T_i_vals[i]
            Q_target = Q_control(t)
            
            # Solve for flow temperature
            T_f = self.solve_flow_temp(Q_target, T_i)
            if T_f is None:
                T_f = T_i
                Q_r = 0.0
            else:
                T_r = self.solve_return_temp(T_f, T_i)
                if T_r is None:
                    Q_r = 0.0
                else:
                    Q_r = self.radiator_power(T_f, T_r, T_i)
            
            T_f_vals[i] = T_f
            Q_r_vals[i] = Q_r
            Q_l_vals[i] = self.heat_loss(T_i)
        
        result = {
            't': sol.t,
            'T_i': T_i_vals,
            'T_f': T_f_vals,
            'Q_r': Q_r_vals,
            'Q_l': Q_l_vals,
        }
        
        if dense_output:
            result['sol'] = sol
        
        return result


if __name__ == '__main__':
    # Example: simple heating profile
    import matplotlib.pyplot as plt
    
    # Create model with default parameters
    model = DynamicThermalModel()
    
    # Define a simple heating control: 
    # Heat at 3 kW from t=0 to t=3600s (1 hour), then off
    def heating_control(t):
        if t < 3600:
            return 3000.0  # 3 kW
        else:
            return 0.0
    
    # Integrate over 2 hours
    result = model.integrate(
        T_i_0=19.0,
        t_span=(0, 7200),
        t_eval=np.linspace(0, 7200, 500),
        Q_control=heating_control
    )
    
    # Plot results
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    
    t_hours = result['t'] / 3600.0
    
    # Indoor and flow temperatures
    axes[0].plot(t_hours, result['T_i'], label='Indoor T_i', linewidth=2)
    axes[0].plot(t_hours, result['T_f'], label='Flow T_f', linewidth=2)
    axes[0].axhline(model.params.T_o, color='gray', linestyle='--', label=f'Outdoor T_o = {model.params.T_o}°C')
    axes[0].set_ylabel('Temperature (°C)')
    axes[0].set_title('Dynamic Thermal Model Example')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # Heat flow
    axes[1].plot(t_hours, result['Q_r'] / 1000.0, label='Radiator power Q_r', linewidth=2)
    axes[1].plot(t_hours, result['Q_l'] / 1000.0, label='Heat loss Q_l', linewidth=2)
    axes[1].set_ylabel('Power (kW)')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    # Control input
    Q_control_vals = np.array([heating_control(t) for t in result['t']])
    axes[2].plot(t_hours, Q_control_vals / 1000.0, label='Control input Q_h', linewidth=2, drawstyle='steps-post')
    axes[2].set_xlabel('Time (hours)')
    axes[2].set_ylabel('Power (kW)')
    axes[2].legend()
    axes[2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('dynamic_thermal_model_example.png', dpi=150)
    print("Plot saved to dynamic_thermal_model_example.png")
