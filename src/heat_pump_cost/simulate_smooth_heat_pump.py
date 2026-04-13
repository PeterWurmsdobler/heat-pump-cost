"""Simulate smooth heat pump operation optimized for COP.

Strategy:
  - Continuous operation with varying power levels (not on/off cycling)
  - Proportional + feed-forward control: setback periods naturally track ~17°C at whatever T_o requires
  - 3-hour predictive pre-heat before comfort periods
  - Target maximum flow temperature ~45°C to keep COP high (4.0-5.4)
  
Heating schedule:
  22:00 – 06:00  Maintain ~17°C (setback)
  06:00 – 09:00  Achieve 19°C comfort (morning)
  09:00 – 17:00  Maintain ~17°C (setback)
  17:00 – 22:00  Achieve 19°C comfort (evening)

Controller approach:
  - Feed-forward: h*(T_sp - T_o) provides steady-state power automatically
  - Proportional feedback: corrects temperature error
  - 1-hour lookahead: gentle pre-heating before comfort transitions
  - Flow temperature limiting to maximize COP
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import fsolve

from heat_pump_cost.dynamic_thermal_model import DynamicThermalModel, ThermalSystemParameters
from heat_pump_cost.radiator_analysis import cop_estimate

# ---------------------------------------------------------------------------
# Simulation constants
# ---------------------------------------------------------------------------

ELECTRICITY_PRICE_PER_KWH = 27.69 / 100.0  # £/kWh  (27.69 p/kWh)
ELECTRICITY_STANDING_CHARGE = 0.5475       # £/day  (54.75 p/day)

# Target maximum flow temperature to maintain high COP
T_FLOW_MAX = 45.0  # °C - keeps COP around 4.5

# Heating schedule: (start_hour, end_hour, target_temp_°C, minimum_power_W)
# Indexed relative to a day that begins at 22:00 (t=0 → 22:00).
COMFORT_SCHEDULE = [
    (0,   8,  17.0, None),   # 22:00 – 06:00  Night setback: maintain ~17°C
    (8,  11,  19.0, None),   # 06:00 – 09:00  Morning comfort: achieve 19°C
    (11, 19,  17.0, None),   # 09:00 – 17:00  Day setback: maintain ~17°C
    (19, 24,  19.0, None),   # 17:00 – 22:00  Evening comfort: achieve 19°C
]

# Time axis ticks for plotting
TICK_HOURS = [0, 8, 11, 19, 24]
TICK_LABELS = ["22:00", "06:00", "09:00", "17:00", "22:00"]


def _get_setpoint(
    t_hours: float,
    schedule: list[tuple[float, float, float, float | None]] | None = None,
) -> tuple[float, float | None]:
    """Get the desired setpoint and minimum power at time t_hours.

    Args:
        t_hours: Current time in hours (0 = 22:00).
        schedule: Optional comfort schedule to use instead of the default COMFORT_SCHEDULE.

    Returns:
        (setpoint, min_power): target temperature and minimum power (None = no minimum)
    """
    sched = schedule if schedule is not None else COMFORT_SCHEDULE
    for start_h, end_h, T_sp, Q_min in sched:
        if start_h <= t_hours < end_h:
            return T_sp, Q_min
    last = sched[-1]
    return last[2], last[3]


def _smooth_controller(
    t_hours: float,
    T_i: float,
    h: float,
    T_o: float,
    model: DynamicThermalModel,
    schedule: list[tuple[float, float, float, float | None]] | None = None,
    K_p: float = 400.0,
) -> tuple[float, float]:
    """Smooth predictive controller that maximizes COP.
    
    Strategy:
    1. Determine current and upcoming setpoints
    2. Calculate required power with lookahead
    3. Add proportional feedback term
    4. Limit power to keep T_f ≤ T_FLOW_MAX
    
    Args:
        t_hours: Current time in hours (0 = 22:00)
        T_i: Current indoor temperature
        h: Heat transfer coefficient
        T_o: Outdoor temperature
        model: Dynamic thermal model for solving flow temperature
        
    Returns:
        (Q_r, T_f): Commanded heat power and resulting flow temperature
    """
    T_sp, Q_min = _get_setpoint(t_hours, schedule)

    # Look ahead to see if we need to pre-heat for upcoming comfort period
    lookahead_hours = 3.0  # Start pre-heating 3 hours before comfort period boundary
    t_future = t_hours + lookahead_hours
    if t_future >= 24:
        t_future -= 24
    T_sp_future, _ = _get_setpoint(t_future, schedule)
    
    # Estimate heat loss at current indoor temp
    Q_loss_now = h * (T_i - T_o)
    
    # Feed-forward: power to maintain current setpoint
    Q_ff = h * (T_sp - T_o)
    
    # Proportional feedback: error correction
    error = T_sp - T_i
    Q_fb = K_p * error
    
    # Predictive term: if future setpoint is higher, start ramping now
    if T_sp_future > T_sp:
        # Need to pre-heat - estimate required power for smooth ramp
        temp_deficit = T_sp_future - T_i
        ramp_time_s = lookahead_hours * 3600
        # Power needed to achieve target: heat loss + capacity change
        C = model.params.C
        Q_ramp = (C * temp_deficit / ramp_time_s) + h * (T_sp_future - T_o)
        Q_predictive = max(0, Q_ramp - Q_ff)
    else:
        Q_predictive = 0
    
    # Total commanded power
    Q_r = max(0, Q_ff + Q_fb + Q_predictive)
    
    # Apply minimum power floor for continuous operation
    if Q_min is not None:
        Q_r = max(Q_r, Q_min)
    
    # Limit power to keep flow temperature reasonable
    # Solve for maximum power that gives T_f = T_FLOW_MAX
    try:
        T_f_max = T_FLOW_MAX
        T_r_candidate = model.solve_return_temp(Q_r, T_f_max, T_i)
        if T_r_candidate is None:
            # Can't achieve this power with T_f_max, use it anyway
            T_f = T_f_max
            # Solve for actual return temp
            T_r_test = model.solve_return_temp(Q_r, T_f, T_i)
            if T_r_test is None:
                # Radiators saturated, limit power
                Q_max = model.params.K * (T_f_max - T_i) ** 1.2
                Q_r = min(Q_r, Q_max)
                T_f = T_f_max
        else:
            # Check if we need to limit power
            Q_max = model.params.V_f * model.params.rho * model.params.c_p * (T_f_max - T_r_candidate)
            if Q_r > Q_max:
                Q_r = Q_max
                T_f = T_f_max
            else:
                # Power is within limit, solve for actual flow temp
                T_f_solved = model.solve_flow_temp(Q_r, T_i)
                if T_f_solved is None:
                    # Very low power - flow temp close to indoor temp
                    T_f = T_i + 1.0
                else:
                    T_f = T_f_solved
    except Exception:
        # Fallback: solve normally or use low-power approximation
        if Q_r < 100:  # Very low power
            T_f = T_i + 1.0
        else:
            T_f_solved = model.solve_flow_temp(Q_r, T_i)
            if T_f_solved is None:
                # Estimate based on radiator power: Q_r = K*(T_m - T_i)^n
                # Solve for mean temp, assume small ΔT across radiator
                T_mean = T_i + (Q_r / model.params.K) ** (1.0 / 1.2)
                T_f = T_mean + 2.0  # Rough approximation
            else:
                T_f = T_f_solved
    
    return Q_r, T_f


def simulate_smooth_heat_pump(
    T_o: float = 5.0,
    T_i_0: float = 19.0,
    dt_s: float = 60.0,
    K: float | None = None,
) -> dict:
    """Simulate one day (24h) of smooth heat pump operation.
    
    Args:
        T_o: Constant outdoor temperature [°C]
        T_i_0: Initial indoor temperature [°C]
        dt_s: Time step [seconds]
        K: Radiator constant [W/K^1.2]; if None, uses ThermalSystemParameters default (71.2)
        
    Returns:
        Dictionary with arrays: t_h, T_i, T_s, T_f, Q_r, Q_l, cop,
        and scalars: total_heat_kwh, electricity_kwh, cost_gbp
    """
    params = ThermalSystemParameters()
    params.T_o = T_o
    if K is not None:
        params.K = K
    model = DynamicThermalModel(params)
    
    # Simulation duration
    duration_s = 24 * 3600.0
    n_steps = int(duration_s / dt_s)
    
    # Initialize arrays
    t_h_arr = np.zeros(n_steps)
    T_i_arr = np.zeros(n_steps)
    T_s_arr = np.zeros(n_steps)
    T_f_arr = np.zeros(n_steps)
    Q_r_arr = np.zeros(n_steps)
    Q_l_arr = np.zeros(n_steps)
    cop_arr = np.zeros(n_steps)
    
    # Initial conditions
    T_i = T_i_0
    
    # Simulate
    for i in range(n_steps):
        t_s = i * dt_s
        t_h = t_s / 3600.0
        t_h_arr[i] = t_h
        
        T_s, _ = _get_setpoint(t_h)
        T_s_arr[i] = T_s
        
        # Smooth controller
        Q_r, T_f = _smooth_controller(t_h, T_i, params.h, T_o, model)
        
        Q_r_arr[i] = Q_r
        T_f_arr[i] = T_f
        T_i_arr[i] = T_i
        
        # Heat loss
        Q_l = params.h * (T_i - T_o)
        Q_l_arr[i] = Q_l
        
        # COP
        cop = cop_estimate(T_o, T_f) if Q_r > 0 else 0
        cop_arr[i] = cop
        
        # Integrate temperature
        dT_i_dt = (Q_r + params.Q_b - Q_l) / params.C
        T_i = T_i + dT_i_dt * dt_s
    
    # Calculate energy and cost
    total_heat_kwh = np.sum(Q_r_arr * dt_s) / 3_600_000.0
    # Avoid division by zero - only calculate electric power when heating
    P_elec = np.zeros_like(Q_r_arr)
    heating_mask = Q_r_arr > 0
    P_elec[heating_mask] = Q_r_arr[heating_mask] / cop_arr[heating_mask]
    electricity_kwh = np.sum(P_elec * dt_s) / 3_600_000.0
    cost_gbp = electricity_kwh * ELECTRICITY_PRICE_PER_KWH
    
    return {
        "t_h": t_h_arr,
        "T_i": T_i_arr,
        "T_s": T_s_arr,
        "T_f": T_f_arr,
        "Q_r": Q_r_arr,
        "Q_l": Q_l_arr,
        "cop": cop_arr,
        "total_heat_kwh": total_heat_kwh,
        "electricity_kwh": electricity_kwh,
        "cost_gbp": cost_gbp,
    }


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------


def _apply_schedule_ticks(ax: plt.Axes) -> None:
    ax.set_xticks(TICK_HOURS)
    ax.set_xticklabels(TICK_LABELS)
    ax.set_xlim(0, 24)
    ax.grid(True, alpha=0.3)


def plot_smooth_heat_pump_operation(
    result: dict,
    output_path: Path,
    show: bool = False,
    dpi: int = 200,
) -> Path:
    """Plot indoor temperature, setpoint, and heat power."""
    t = result["t_h"]
    T_i = result["T_i"]
    T_s = result["T_s"]
    T_o = ThermalSystemParameters().T_o
    Q_r = result["Q_r"] / 1000.0  # W → kW
    
    fig, ax = plt.subplots(figsize=(11, 5))
    
    # Left axis: temperatures
    l1, = ax.plot(t, T_i, color="#1f77b4", linewidth=2, label="T_i  (indoor)")
    l2, = ax.plot(t, T_s, color="#d62728", linewidth=1.5, linestyle="--",
                  drawstyle="steps-post", label="T_s  (setpoint)")
    ax.set_ylabel("Temperature (°C)", fontsize=11)
    ax.set_ylim(12, 22)
    ax.set_title(
        f"Smooth Heat Pump Operation – January 2026 (T_o = {T_o:.0f} °C)",
        fontsize=11,
        fontweight="bold",
    )
    _apply_schedule_ticks(ax)
    ax.set_xlabel("Time of day", fontsize=11)
    
    # Right axis: heat power
    axr = ax.twinx()
    l3, = axr.plot(t, Q_r, color="#ff7f0e", linewidth=2,
                   label="Q_r  (heat delivered, kW)")
    axr.fill_between(t, Q_r, alpha=0.20, color="#ff7f0e")
    axr.set_ylabel("Heat delivered (kW)", fontsize=11, color="#ff7f0e")
    axr.tick_params(axis="y", labelcolor="#ff7f0e")
    axr.set_ylim(0, 4)
    
    lines = [l1, l2, l3]
    labels = [l.get_label() for l in lines]
    ax.legend(lines, labels, loc="lower left", fontsize=9)
    
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
    if show:
        plt.show()
    else:
        plt.close(fig)
    return output_path


def plot_smooth_heat_pump_cop(
    result: dict,
    output_path: Path,
    show: bool = False,
    dpi: int = 200,
) -> Path:
    """Plot flow temperature and COP for smooth operation."""
    t = result["t_h"]
    T_f = result["T_f"]
    cop = result["cop"]
    T_o = ThermalSystemParameters().T_o
    
    fig, ax = plt.subplots(figsize=(11, 5))
    
    # Left axis: flow temperature
    l1, = ax.plot(t, T_f, color="#1f77b4", linewidth=1.5, label="T_f  (flow temperature)", antialiased=True)
    l2 = ax.axhline(T_FLOW_MAX, color="red", linewidth=1, linestyle="--", alpha=0.5,
                    label=f"Target max T_f = {T_FLOW_MAX:.0f} °C")
    ax.set_ylabel("Flow temperature (°C)", fontsize=11)
    T_f_valid = np.asarray(T_f)
    T_f_valid = T_f_valid[~np.isnan(T_f_valid)] if np.any(np.isnan(T_f_valid)) else T_f_valid
    T_f_pad = max(3.0, (T_f_valid.max() - T_f_valid.min()) * 0.15)
    ax.set_ylim(T_f_valid.min() - T_f_pad, T_f_valid.max() + T_f_pad)
    ax.set_title(
        f"Smooth Heat Pump COP – January 2026 (T_o = {T_o:.0f} °C)",
        fontsize=11,
        fontweight="bold",
    )
    _apply_schedule_ticks(ax)
    ax.set_xlabel("Time of day", fontsize=11)
    
    # Right axis: COP
    axr = ax.twinx()
    l3, = axr.plot(t, cop, color="#2ca02c", linewidth=1.5, label="COP", antialiased=True)
    axr.set_ylabel("COP", fontsize=11, color="#2ca02c")
    axr.tick_params(axis="y", labelcolor="#2ca02c")
    cop_arr = np.asarray(cop)
    cop_valid = cop_arr[~np.isnan(cop_arr) & (cop_arr > 0)] if len(cop_arr) else np.array([])
    if len(cop_valid):
        cop_lo = float(cop_valid.min())
        cop_hi = float(cop_valid.max())
        # Round to nearest 0.5 for clean axis
        cop_lo_round = np.floor(cop_lo * 2) / 2 - 0.5
        cop_hi_round = np.ceil(cop_hi * 2) / 2 + 0.5
        axr.set_ylim(cop_lo_round, cop_hi_round)
        # Set y-ticks at 0.5 intervals
        cop_ticks = np.arange(cop_lo_round, cop_hi_round + 0.1, 0.5)
        axr.set_yticks(cop_ticks)
    else:
        axr.set_ylim(2, 7)
    
    lines = [l1, l2, l3]
    labels = [l.get_label() for l in lines]
    ax.legend(lines, labels, loc="lower right", fontsize=9)
    
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
    if show:
        plt.show()
    else:
        plt.close(fig)
    return output_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Run the smooth heat pump simulation and save plots."""
    from argparse import ArgumentParser

    parser = ArgumentParser(
        description="Simulate one day of smooth heat pump operation optimized for COP."
    )
    parser.add_argument(
        "--outdoor-temp", type=float, default=5.0,
        help="Constant outdoor temperature T_o [°C] (default: 5.0)",
    )
    parser.add_argument(
        "--output", default="assets/smooth_heat_pump_operation.png",
        help="Output PNG path for operation plot",
    )
    parser.add_argument("--show", action="store_true", help="Display plots interactively")
    parser.add_argument("--dpi", type=int, default=200, help="Plot DPI (default: 200)")
    args = parser.parse_args(args=argv)

    project_root = Path(__file__).resolve().parents[2]
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = project_root / output_path

    print(f"Simulating smooth heat pump: T_o = {args.outdoor_temp} °C …")
    result = simulate_smooth_heat_pump(T_o=args.outdoor_temp)

    h = ThermalSystemParameters().h
    steady_kw = h * (19.0 - args.outdoor_temp) / 1000.0

    print()
    print("─" * 60)
    print(f"  Steady-state heat loss  h·ΔT = {steady_kw:.2f} kW")
    print(f"  Total heat delivered         = {result['total_heat_kwh']:.1f} kWh/day")
    print(f"  Electricity consumed         = {result['electricity_kwh']:.1f} kWh/day")
    print(f"  Avg. seasonal COP            = {result['total_heat_kwh'] / result['electricity_kwh']:.2f}")
    print(f"  Elec. cost (27.69 p/kWh)     = £{result['cost_gbp']:.2f}/day")
    print(f"  + standing charge            = £{ELECTRICITY_STANDING_CHARGE:.2f}/day")
    print(f"  Total cost                   = £{result['cost_gbp'] + ELECTRICITY_STANDING_CHARGE:.2f}/day")
    print("─" * 60)
    print()

    # Plot operation
    output_path = plot_smooth_heat_pump_operation(result, output_path, show=args.show, dpi=args.dpi)
    print(f"Saved operation plot to {output_path}")
    
    # Plot COP
    cop_output_path = output_path.parent / output_path.name.replace("operation", "cop")
    cop_output_path = plot_smooth_heat_pump_cop(result, cop_output_path, show=args.show, dpi=args.dpi)
    print(f"Saved COP plot to {cop_output_path}")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
