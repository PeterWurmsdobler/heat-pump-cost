"""Simulate heat pump operation optimized for dynamic electricity tariffs.

Octopus Energy Cosy tariff structure:
  - Cosy rate (22:00–00:00, 04:00–07:00, 13:00–16:00): 14.53 p/kWh (cheap)
  - Peak rate (16:00–19:00): 51.68 p/kWh (expensive)
  - Day rate (all other times): 33.28 p/kWh (standard)

Optimization strategy:
  - Pre-heat aggressively during cheap periods with higher flow temps (up to 55°C)
    to maximize thermal energy stored in building mass
  - Minimize heating during peak period (16:00–19:00)
  - Maintain moderate flow temps (≤45°C) during normal periods for high COP
  - Use house thermal mass as "battery" to shift heating load to cheap periods
  - Maintain comfort constraints (17–20°C acceptable range)
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from heat_pump_cost.dynamic_thermal_model import DynamicThermalModel, ThermalSystemParameters
from heat_pump_cost.radiator_analysis import cop_estimate

# ---------------------------------------------------------------------------
# Octopus Cosy tariff structure
# ---------------------------------------------------------------------------

ELECTRICITY_STANDING_CHARGE = 0.5475  # £/day  (54.75 p/day)

# Tariff periods: (start_hour, end_hour, price_p_per_kwh)
# Hours from midnight (00:00 = 0)
TARIFF_SCHEDULE = [
    (0.0,  4.0,  33.28),  # 00:00–04:00  Day rate
    (4.0,  7.0,  14.53),  # 04:00–07:00  Cosy rate (cheap)
    (7.0, 13.0,  33.28),  # 07:00–13:00  Day rate
    (13.0, 16.0, 14.53),  # 13:00–16:00  Cosy rate (cheap)
    (16.0, 19.0, 51.68),  # 16:00–19:00  Peak rate (expensive)
    (19.0, 22.0, 33.28),  # 19:00–22:00  Day rate
    (22.0, 24.0, 14.53),  # 22:00–00:00  Cosy rate (cheap)
]

# Comfort schedule: (start_hour, end_hour, min_temp, max_temp)
# Hours from midnight
COMFORT_SCHEDULE = [
    (0.0,  6.0,  17.0, 20.0),   # 00:00–06:00  Night: 17-20°C acceptable
    (6.0,  9.0,  18.5, 20.0),   # 06:00–09:00  Morning: prefer 19°C
    (9.0, 17.0,  17.0, 20.0),   # 09:00–17:00  Day: 17-20°C acceptable
    (17.0, 22.0, 18.5, 20.0),   # 17:00–22:00  Evening: prefer 19°C
    (22.0, 24.0, 17.0, 20.0),   # 22:00–00:00  Night: 17-20°C acceptable
]

# Time axis ticks for plotting
TICK_HOURS = [0, 4, 7, 13, 16, 19, 22, 24]
TICK_LABELS = ["00:00", "04:00", "07:00", "13:00", "16:00", "19:00", "22:00", "00:00"]

# Target maximum flow temperature - varies by tariff period
T_FLOW_MAX_CHEAP = 55.0   # °C - higher during cheap periods to store more energy
T_FLOW_MAX_NORMAL = 45.0  # °C - maintain high COP during normal/peak periods

# Cheap rate threshold for aggressive heating
CHEAP_RATE_THRESHOLD = 0.20  # £/kWh - rates below this are "cheap"


def get_electricity_price(t_hours: float) -> float:
    """Get electricity price in £/kWh at time t_hours (from midnight)."""
    # Normalize to 0-24 range
    t_h = t_hours % 24
    
    for start_h, end_h, price_p in TARIFF_SCHEDULE:
        if start_h <= t_h < end_h:
            return price_p / 100.0  # Convert pence to pounds
    
    # Fallback to day rate
    return 33.28 / 100.0


def is_cheap_period(t_hours: float) -> bool:
    """Check if current time is in a cheap tariff period."""
    price = get_electricity_price(t_hours)
    return price < CHEAP_RATE_THRESHOLD


def get_comfort_bounds(t_hours: float) -> tuple[float, float]:
    """Get acceptable temperature range at time t_hours (from midnight)."""
    t_h = t_hours % 24
    
    for start_h, end_h, T_min, T_max in COMFORT_SCHEDULE:
        if start_h <= t_h < end_h:
            return T_min, T_max
    
    # Fallback
    return 17.0, 20.0


def _tariff_optimized_controller(
    t_hours: float,
    T_i: float,
    h: float,
    T_o: float,
    model: DynamicThermalModel,
    lookahead_hours: float = 4.0,
) -> tuple[float, float]:
    """Cost-optimized controller that exploits cheap electricity periods.
    
    Strategy:
    1. During cheap periods: heat aggressively with higher flow temps (up to 55°C)
       to maximize thermal energy stored in building mass
    2. During expensive periods: minimize heating, rely on stored thermal energy
    3. Maintain comfort bounds at all times
    4. Use different flow temp limits: 55°C cheap, 45°C normal/peak
    
    Args:
        t_hours: Current time in hours (from midnight 00:00)
        T_i: Current indoor temperature
        h: Heat transfer coefficient
        T_o: Outdoor temperature
        model: Dynamic thermal model
        lookahead_hours: Hours to look ahead for optimization
        
    Returns:
        (Q_r, T_f): Commanded heat power and resulting flow temperature
    """
    T_min, T_max = get_comfort_bounds(t_hours)
    current_price = get_electricity_price(t_hours)
    in_cheap_period = is_cheap_period(t_hours)
    
    # Look ahead to find cheap and expensive periods
    t_sample_points = np.linspace(t_hours, t_hours + lookahead_hours, 20)
    future_prices = [get_electricity_price(t) for t in t_sample_points]
    avg_future_price = np.mean(future_prices)
    min_future_price = np.min(future_prices)
    
    # Determine if we're in a cheap period relative to near future
    is_cheap_now = in_cheap_period or (current_price < avg_future_price * 0.9)
    is_expensive_now = current_price > avg_future_price * 1.3
    
    # Set flow temperature limit based on tariff period
    T_flow_max = T_FLOW_MAX_CHEAP if in_cheap_period else T_FLOW_MAX_NORMAL
    
    # Base heat loss at current temp
    Q_loss = h * (T_i - T_o)
    
    # Determine target temperature based on tariff
    if is_cheap_now:
        # Cheap period: aim for upper comfort bound to store thermal energy
        T_target = T_max
    elif is_expensive_now:
        # Expensive period: aim for lower comfort bound to minimize heating
        T_target = T_min
    else:
        # Normal period: aim for middle of comfort range
        T_target = (T_min + T_max) / 2
    
    # Feed-forward + proportional control
    K_p = 500.0  # W/K
    Q_ff = h * (T_target - T_o)
    Q_fb = K_p * (T_target - T_i)
    Q_r = max(0, Q_ff + Q_fb)
    
    # During expensive periods, cap power aggressively if above minimum temp
    if is_expensive_now and T_i >= T_min:
        # Only provide heat loss compensation, no pre-heating
        Q_r = min(Q_r, Q_loss * 1.1)
    
    # Minimum baseline to prevent excessive cooling
    Q_min = 500.0  # W
    if T_i < T_min + 0.5:
        # Temperature approaching lower bound, ensure minimum heating
        Q_r = max(Q_r, Q_min)
    
    # Solve for flow temperature with limiting
    try:
        if Q_r < 100:  # Very low power
            T_f = T_i + 1.0
        else:
            T_f_solved = model.solve_flow_temp(Q_r, T_i)
            if T_f_solved is None or T_f_solved > T_flow_max:
                # Limit to T_flow_max (varies by tariff period)
                Q_max = model.params.K * (T_flow_max - T_i) ** 1.2
                Q_r = min(Q_r, Q_max)
                T_f = T_flow_max
            else:
                T_f = T_f_solved
    except Exception:
        # Fallback
        if Q_r < 100:
            T_f = T_i + 1.0
        else:
            T_mean = T_i + (Q_r / model.params.K) ** (1.0 / 1.2)
            T_f = min(T_mean + 2.0, T_flow_max)
    
    return Q_r, T_f


def simulate_tariff_optimized(
    T_o: float = 5.0,
    T_i_0: float = 19.0,
    dt_s: float = 60.0,
) -> dict:
    """Simulate one day (24h) of tariff-optimized heat pump operation.
    
    Args:
        T_o: Constant outdoor temperature [°C]
        T_i_0: Initial indoor temperature [°C]
        dt_s: Time step [seconds]
        
    Returns:
        Dictionary with arrays and scalars
    """
    params = ThermalSystemParameters()
    params.T_o = T_o
    model = DynamicThermalModel(params)
    
    # Simulation duration
    duration_s = 24 * 3600.0
    n_steps = int(duration_s / dt_s)
    
    # Initialize arrays
    t_h_arr = np.zeros(n_steps)
    T_i_arr = np.zeros(n_steps)
    T_min_arr = np.zeros(n_steps)
    T_max_arr = np.zeros(n_steps)
    T_f_arr = np.zeros(n_steps)
    Q_r_arr = np.zeros(n_steps)
    Q_l_arr = np.zeros(n_steps)
    cop_arr = np.zeros(n_steps)
    price_arr = np.zeros(n_steps)
    
    # Initial conditions
    T_i = T_i_0
    
    # Simulate
    for i in range(n_steps):
        t_s = i * dt_s
        t_h = t_s / 3600.0
        t_h_arr[i] = t_h
        
        T_min, T_max = get_comfort_bounds(t_h)
        T_min_arr[i] = T_min
        T_max_arr[i] = T_max
        
        price = get_electricity_price(t_h)
        price_arr[i] = price
        
        # Tariff-optimized controller
        Q_r, T_f = _tariff_optimized_controller(t_h, T_i, params.h, T_o, model)
        
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
    
    # Calculate energy and cost with time-varying tariff
    total_heat_kwh = np.sum(Q_r_arr * dt_s) / 3_600_000.0
    P_elec = np.zeros_like(Q_r_arr)
    heating_mask = Q_r_arr > 0
    P_elec[heating_mask] = Q_r_arr[heating_mask] / cop_arr[heating_mask]
    
    # Cost per timestep
    energy_per_step_kwh = (P_elec * dt_s) / 3_600_000.0
    cost_per_step = energy_per_step_kwh * price_arr
    total_cost_gbp = np.sum(cost_per_step)
    
    electricity_kwh = np.sum(energy_per_step_kwh)
    
    return {
        "t_h": t_h_arr,
        "T_i": T_i_arr,
        "T_min": T_min_arr,
        "T_max": T_max_arr,
        "T_f": T_f_arr,
        "Q_r": Q_r_arr,
        "Q_l": Q_l_arr,
        "cop": cop_arr,
        "price": price_arr,
        "total_heat_kwh": total_heat_kwh,
        "electricity_kwh": electricity_kwh,
        "cost_gbp": total_cost_gbp,
    }


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------


def _apply_schedule_ticks(ax: plt.Axes) -> None:
    ax.set_xticks(TICK_HOURS)
    ax.set_xticklabels(TICK_LABELS)
    ax.set_xlim(0, 24)
    ax.grid(True, alpha=0.3)


def plot_tariff_structure(
    output_path: Path,
    show: bool = False,
    dpi: int = 200,
) -> Path:
    """Plot the Octopus Cosy tariff structure over one day."""
    t_h = np.linspace(0, 24, 1440)  # Minute resolution
    prices = np.array([get_electricity_price(t) * 100 for t in t_h])  # Convert to pence
    
    fig, ax = plt.subplots(figsize=(11, 4))
    
    # Fill area with Octopus purple color
    ax.fill_between(t_h, prices, alpha=0.3, color="#842E7B", label="Electricity price")
    ax.plot(t_h, prices, color="#842E7B", linewidth=2, drawstyle="steps-post")
    
    ax.set_ylabel("Electricity price (p/kWh)", fontsize=11)
    ax.set_ylim(0, 60)
    ax.set_title(
        "Octopus Energy Cosy Tariff",
        fontsize=11,
        fontweight="bold",
    )
    _apply_schedule_ticks(ax)
    ax.set_xlabel("Time of day", fontsize=11)
    
    # Add annotations for rate periods
    ax.text(2, 55, "Day\n33.28p", ha="center", va="top", fontsize=8, color="#842E7B")
    ax.text(5.5, 10, "Cosy\n14.53p", ha="center", va="bottom", fontsize=8, color="#842E7B", weight="bold")
    ax.text(10, 38, "Day", ha="center", va="bottom", fontsize=8, color="#842E7B")
    ax.text(14.5, 10, "Cosy\n14.53p", ha="center", va="bottom", fontsize=8, color="#842E7B", weight="bold")
    ax.text(17.5, 56, "Peak\n51.68p", ha="center", va="bottom", fontsize=8, color="red", weight="bold")
    ax.text(20.5, 38, "Day", ha="center", va="bottom", fontsize=8, color="#842E7B")
    ax.text(23, 10, "Cosy\n14.53p", ha="center", va="bottom", fontsize=8, color="#842E7B", weight="bold")
    
    ax.legend(loc="upper left", fontsize=9)
    
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
    if show:
        plt.show()
    else:
        plt.close(fig)
    return output_path


def plot_tariff_optimized_operation(
    result: dict,
    output_path: Path,
    show: bool = False,
    dpi: int = 200,
) -> Path:
    """Plot indoor temperature and heat power for tariff-optimized operation."""
    t = result["t_h"]
    T_i = result["T_i"]
    T_min = result["T_min"]
    T_max = result["T_max"]
    T_o = ThermalSystemParameters().T_o
    Q_r = result["Q_r"] / 1000.0  # W → kW
    
    fig, ax = plt.subplots(figsize=(11, 5))
    
    # Left axis: temperatures with comfort bounds
    ax.fill_between(t, T_min, T_max, alpha=0.15, color="green", label="Comfort range")
    l1, = ax.plot(t, T_i, color="#1f77b4", linewidth=2, label="T_i  (indoor)")
    l2 = ax.axhline(T_o, color="grey", linewidth=1, linestyle=":", label=f"T_o = {T_o:.0f} °C")
    ax.set_ylabel("Temperature (°C)", fontsize=11)
    ax.set_ylim(T_o, 22)
    ax.set_title(
        f"Tariff-Optimized Heat Pump – January 2026 (T_o = {T_o:.0f} °C)",
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


def plot_tariff_optimized_cop(
    result: dict,
    output_path: Path,
    show: bool = False,
    dpi: int = 200,
) -> Path:
    """Plot flow temperature and COP for tariff-optimized operation."""
    t = result["t_h"]
    T_f = result["T_f"]
    cop = result["cop"]
    T_o = ThermalSystemParameters().T_o
    
    fig, ax = plt.subplots(figsize=(11, 5))
    
    # Left axis: flow temperature
    l1, = ax.plot(t, T_f, color="#1f77b4", linewidth=2, label="T_f  (flow temperature)")
    l2 = ax.axhline(T_o, color="grey", linewidth=1, linestyle=":", label=f"T_o = {T_o:.0f} °C")
    l3 = ax.axhline(T_FLOW_MAX_CHEAP, color="orange", linewidth=1, linestyle="--", alpha=0.5,
                    label=f"Max T_f (cheap) = {T_FLOW_MAX_CHEAP:.0f} °C")
    l3b = ax.axhline(T_FLOW_MAX_NORMAL, color="red", linewidth=1, linestyle="--", alpha=0.5,
                    label=f"Max T_f (normal) = {T_FLOW_MAX_NORMAL:.0f} °C")
    ax.set_ylabel("Flow temperature (°C)", fontsize=11)
    ax.set_ylim(20, 80)
    ax.set_title(
        f"Tariff-Optimized COP – January 2026 (T_o = {T_o:.0f} °C)",
        fontsize=11,
        fontweight="bold",
    )
    _apply_schedule_ticks(ax)
    ax.set_xlabel("Time of day", fontsize=11)
    
    # Right axis: COP
    axr = ax.twinx()
    l4, = axr.plot(t, cop, color="#2ca02c", linewidth=2, label="COP")
    axr.set_ylabel("COP", fontsize=11, color="#2ca02c")
    axr.tick_params(axis="y", labelcolor="#2ca02c")
    axr.set_ylim(2, 7)
    
    lines = [l1, l2, l3, l3b, l4]
    labels = [l.get_label() for l in lines]
    ax.legend(lines, labels, loc="lower right", fontsize=8)
    
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
    """Run the tariff-optimized heat pump simulation and save plots."""
    from argparse import ArgumentParser

    parser = ArgumentParser(
        description="Simulate one day of tariff-optimized heat pump operation (Octopus Cosy)."
    )
    parser.add_argument(
        "--outdoor-temp", type=float, default=5.0,
        help="Constant outdoor temperature T_o [°C] (default: 5.0)",
    )
    parser.add_argument(
        "--output", default="assets/tariff_optimized_operation.png",
        help="Output PNG path for operation plot",
    )
    parser.add_argument("--show", action="store_true", help="Display plots interactively")
    parser.add_argument("--dpi", type=int, default=200, help="Plot DPI (default: 200)")
    args = parser.parse_args(args=argv)

    project_root = Path(__file__).resolve().parents[2]
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = project_root / output_path

    # Plot tariff structure first
    tariff_plot_path = output_path.parent / "octopus_cosy_tariff.png"
    print("Generating Octopus Cosy tariff visualization...")
    plot_tariff_structure(tariff_plot_path, show=args.show, dpi=args.dpi)
    print(f"Saved tariff plot to {tariff_plot_path}")
    print()

    print(f"Simulating tariff-optimized heat pump: T_o = {args.outdoor_temp} °C …")
    result = simulate_tariff_optimized(T_o=args.outdoor_temp)

    h = ThermalSystemParameters().h
    steady_kw = h * (19.0 - args.outdoor_temp) / 1000.0

    # Calculate flat-rate cost for comparison
    flat_rate = 27.69 / 100.0
    flat_rate_cost = result["electricity_kwh"] * flat_rate

    print()
    print("─" * 60)
    print(f"  Steady-state heat loss  h·ΔT = {steady_kw:.2f} kW")
    print(f"  Total heat delivered         = {result['total_heat_kwh']:.1f} kWh/day")
    print(f"  Electricity consumed         = {result['electricity_kwh']:.1f} kWh/day")
    print(f"  Avg. seasonal COP            = {result['total_heat_kwh'] / result['electricity_kwh']:.2f}")
    print(f"  Tariff-optimized cost        = £{result['cost_gbp']:.2f}/day")
    print(f"  + standing charge            = £{ELECTRICITY_STANDING_CHARGE:.2f}/day")
    print(f"  Total cost (Octopus Cosy)    = £{result['cost_gbp'] + ELECTRICITY_STANDING_CHARGE:.2f}/day")
    print(f"  (vs flat 27.69p rate         = £{flat_rate_cost + ELECTRICITY_STANDING_CHARGE:.2f}/day)")
    print("─" * 60)
    print()

    # Plot operation
    output_path = plot_tariff_optimized_operation(result, output_path, show=args.show, dpi=args.dpi)
    print(f"Saved operation plot to {output_path}")
    
    # Plot COP
    cop_output_path = output_path.parent / output_path.name.replace("operation", "cop")
    cop_output_path = plot_tariff_optimized_cop(result, cop_output_path, show=args.show, dpi=args.dpi)
    print(f"Saved COP plot to {cop_output_path}")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
