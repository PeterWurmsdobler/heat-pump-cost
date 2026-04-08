"""Simulate gas boiler space heating for a full 24-hour day.

Heating schedule (starting at 22:00):
  22:00 – 06:00  Heating OFF (house cools freely)
  06:00 – 09:00  Setpoint T_s = 19 °C  (full power until reached, then feed-forward)
  09:00 – 17:00  Setpoint T_s = 15 °C  (reduced / away setpoint)
  17:00 – 22:00  Setpoint T_s = 19 °C  (evening warm-up)

Model parameters (from April 2026 thermal identification):
  C    = 21.0 MJ/K    thermal capacity
  h    = 142.6 W/K    heat transfer coefficient
  Q_b  = 500 W        background heat (appliances / occupancy)
  τ    = C/h = 40.8 h time constant

Simulation conditions:
  T_o  = 5 °C         January 2026 average outdoor temperature
  Boiler efficiency η = 0.95 (condensing)
  Gas price = 5.93 p/kWh (Ofgem January 2026 price cap)
"""

from __future__ import annotations

from itertools import chain
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np

from heat_pump_cost.dynamic_thermal_model import DynamicThermalModel, ThermalSystemParameters
from heat_pump_cost.radiator_analysis import cop_estimate

# ---------------------------------------------------------------------------
# Simulation constants
# ---------------------------------------------------------------------------

GAS_PRICE_PER_KWH = 5.93 / 100.0   # £/kWh  (5.93 p/kWh)
BOILER_EFFICIENCY = 0.95             # condensing gas boiler
GAS_STANDING_CHARGE = 0.3509        # £/day

# ---------------------------------------------------------------------------
# Schedule / controller
# ---------------------------------------------------------------------------

# Heating schedule: (start_hour, end_hour, setpoint_°C)
# Indexed relative to a day that begins at 22:00 (t=0 → 22:00).
SCHEDULE = [
    (0,   8,  None),   # 22:00 – 06:00  OFF
    (8,  11,  19.0),   # 06:00 – 09:00  T_s = 19 °C
    (11, 19,  15.0),   # 09:00 – 17:00  T_s = 15 °C  (away)
    (19, 24,  19.0),   # 17:00 – 22:00  T_s = 19 °C
]

# Clock labels corresponding to the schedule boundaries (for axis ticks)
TICK_HOURS = [0, 8, 11, 19, 24]
TICK_LABELS = ["22:00", "06:00", "09:00", "17:00", "22:00"]


def _setpoint(t_hours: float) -> float | None:
    """Return the active setpoint [°C] at elapsed time *t_hours*, or None if off."""
    for start, end, setpoint in SCHEDULE:
        if start <= t_hours < end:
            return setpoint
    return SCHEDULE[-1][2]


def _controller(T_i: float, T_s: float | None, h: float, T_o: float, Q_b: float, Q_max: float, at_setpoint: bool) -> tuple[float, bool]:
    """Bang-bang + feed-forward boiler controller with hysteresis.

    - Heating OFF  → 0 W
    - T_i < T_s (initial warm-up)  → Q_max until setpoint reached
    - T_i ≥ T_s (first time)  → switch to feedforward, mark as at_setpoint
    - at_setpoint AND T_i < T_s - 0.5°C  → Q_max (re-engage full power)
    - at_setpoint AND T_i ≥ T_s - 0.5°C  → feedforward (gentle drop allowed)
    
    Returns:
        (Q_h, new_at_setpoint): Heating power [W] and updated setpoint state
    """
    if T_s is None:
        return 0.0, False
    
    # If not at setpoint yet, use bang-bang to reach it
    if not at_setpoint:
        if T_i >= T_s:
            # Just reached setpoint, switch to feedforward
            return max(0.0, h * (T_s - T_o) - Q_b), True
        else:
            # Still warming up
            return Q_max, False
    
    # Already at setpoint: use hysteresis to prevent frequent cycling
    if T_i < T_s - 0.5:
        # Temperature dropped too much, re-engage full power
        return Q_max, False  # Mark as not at setpoint anymore
    else:
        # Use feedforward (allows gentle drop below setpoint)
        return max(0.0, h * (T_s - T_o) - Q_b), True


# ---------------------------------------------------------------------------
# Core simulation
# ---------------------------------------------------------------------------


def simulate_gas_boiler(
    T_o: float = 5.0,
    Q_max: float = 50_000.0,
    T_i_0: float = 19.0,
    dt_s: float = 60.0,
) -> dict:
    """Simulate one day of gas boiler space heating.

    Uses a first-order Euler loop (dt=60 s ≪ τ=44 h) driven by the bang-bang
    plus feed-forward controller.  At each step it solves for the flow
    temperature T_f required to deliver the commanded power, then integrates:

        C · dT_i/dt = Q_r + Q_b − h · (T_i − T_o)

    Args:
        T_o: Constant outdoor temperature [°C].
        Q_max: Boiler maximum output [W].
        T_i_0: Indoor temperature at t=0 (22:00) [°C].
        dt_s: Euler time step [s].

    Returns:
        Dictionary with arrays:
          ``t_h``       – time in hours from 22:00
          ``T_i``       – indoor temperature [°C]
          ``T_s``       – setpoint temperature [°C or NaN when off]
          ``T_f``       – radiator flow temperature [°C]
          ``Q_h``       – commanded heating power [W]
          ``Q_r``       – actual radiator output [W]
          ``Q_b``       – background heat [W] (constant)
          ``Q_l``       – heat loss [W]
          ``cop``       – equivalent HP COP at each T_f
        and scalars:
          ``total_heat_kwh``  – total heat delivered to radiators [kWh]
          ``gas_kwh``         – gas consumed [kWh]
          ``cost_gbp``        – gas cost excluding standing charge [£]
    """
    params = ThermalSystemParameters(T_o=T_o)
    model = DynamicThermalModel(params)

    n_steps = int(round(24 * 3600 / dt_s)) + 1
    t_s_arr = np.arange(n_steps) * dt_s
    t_h_arr = t_s_arr / 3600.0

    T_i_arr = np.empty(n_steps)
    T_s_arr = np.full(n_steps, np.nan)
    T_f_arr = np.empty(n_steps)
    Q_h_arr = np.zeros(n_steps)
    Q_r_arr = np.zeros(n_steps)
    Q_l_arr = np.zeros(n_steps)
    cop_arr = np.full(n_steps, np.nan)

    T_i_arr[0] = T_i_0
    T_f_arr[0] = T_i_0

    T_i = T_i_0
    at_setpoint = False  # Track whether we've reached the current setpoint
    prev_setpoint = None  # Track setpoint changes
    
    for k in range(n_steps - 1):
        t_h = t_h_arr[k]
        T_s = _setpoint(t_h)
        
        # Reset at_setpoint flag if setpoint changed
        if T_s != prev_setpoint:
            at_setpoint = False
            prev_setpoint = T_s
        
        Q_h, at_setpoint = _controller(T_i, T_s, params.h, T_o, params.Q_b, Q_max, at_setpoint)

        # Solve for flow temperature and actual radiator output
        if Q_h > 50.0:
            T_f = model.solve_flow_temp(Q_h, T_i)
            if T_f is None:
                # Q_h exceeds radiator capacity; saturate at boiler max flow temperature
                T_f = min(T_i + 55.0, 80.0)
            T_r = model.solve_return_temp(T_f, T_i)
            Q_r = model.radiator_power(T_f, T_r, T_i) if T_r is not None else 0.0
        else:
            T_f = T_i
            Q_r = 0.0

        Q_l = params.h * (T_i - T_o)
        dT_dt = (Q_r + params.Q_b - Q_l) / params.C
        T_i = T_i + dT_dt * dt_s

        T_i_arr[k + 1] = T_i
        T_s_arr[k] = T_s if T_s is not None else np.nan
        T_f_arr[k] = T_f
        Q_h_arr[k] = Q_h
        Q_r_arr[k] = Q_r
        Q_l_arr[k] = Q_l
        cop_arr[k] = cop_estimate(T_o, T_f) if Q_h > 50.0 else np.nan

    # Fill last step
    T_s_arr[-1] = _setpoint(t_h_arr[-1])
    T_f_arr[-1] = T_f_arr[-2]
    Q_l_arr[-1] = params.h * (T_i_arr[-1] - T_o)
    cop_arr[-1] = cop_arr[-2]

    total_heat_kwh = float(np.sum(Q_r_arr) * dt_s / 3.6e6)
    gas_kwh = total_heat_kwh / BOILER_EFFICIENCY
    cost_gbp = gas_kwh * GAS_PRICE_PER_KWH

    return {
        "t_h": t_h_arr,
        "T_i": T_i_arr,
        "T_s": T_s_arr,
        "T_f": T_f_arr,
        "Q_h": Q_h_arr,
        "Q_r": Q_r_arr,
        "Q_b": params.Q_b,
        "Q_l": Q_l_arr,
        "cop": cop_arr,
        "total_heat_kwh": total_heat_kwh,
        "gas_kwh": gas_kwh,
        "cost_gbp": cost_gbp,
    }


# ---------------------------------------------------------------------------
# Heat pump variant cost calculation
# ---------------------------------------------------------------------------

ELECTRICITY_PRICE_PER_KWH = 27.69 / 100.0  # £/kWh  (27.69 p/kWh)
ELECTRICITY_STANDING_CHARGE = 0.5475       # £/day  (54.75 p/day)


def calculate_heat_pump_cost(result: dict) -> dict:
    """Calculate electricity consumption and cost for heat pump delivering same Q_r profile.
    
    Args:
        result: Dictionary returned by :func:`simulate_gas_boiler`, containing Q_r and cop arrays.
    
    Returns:
        Dictionary with electricity_kwh and cost_gbp.
    """
    Q_r = np.array(result["Q_r"])  # W
    cop = np.array(result["cop"])
    dt_s = 60.0  # timestep in seconds
    
    # Electricity consumption: P_elec = Q_r / COP at each timestep
    # Avoid division by zero (though COP should always be > 0)
    P_elec = np.where(cop > 0, Q_r / cop, 0.0)  # W
    
    # Total electricity in kWh
    total_elec_kwh = np.sum(P_elec * dt_s) / 3_600_000.0  # W⋅s → kWh
    
    # Cost (energy only, standing charge added separately in display)
    cost_gbp = total_elec_kwh * ELECTRICITY_PRICE_PER_KWH
    
    return {
        "electricity_kwh": total_elec_kwh,
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


def plot_gas_boiler(result: dict, output_path: Path, show: bool = False, dpi: int = 200) -> Path:
    """Produce the single-panel figure for the gas boiler simulation.

    T_i (indoor) and T_s (setpoint) on the left y-axis;
    Q_r (actual heat delivered to radiators) in kW on the right y-axis.

    Args:
        result: Dictionary returned by :func:`simulate_gas_boiler`.
        output_path: Destination PNG path.
        show: If True, call ``plt.show()`` after saving.
        dpi: Output resolution.

    Returns:
        The written ``output_path``.
    """
    t = result["t_h"]
    T_i = result["T_i"]
    T_s = result["T_s"]
    T_o = ThermalSystemParameters().T_o
    Q_r = result["Q_r"] / 1000.0   # W → kW
    cost = result["cost_gbp"]
    gas_kwh = result["gas_kwh"]
    heat_kwh = result["total_heat_kwh"]

    fig, ax = plt.subplots(figsize=(11, 5))

    # ── Left axis: temperatures ───────────────────────────────────────────
    l1, = ax.plot(t, T_i, color="#1f77b4", linewidth=2, label="T_i  (indoor)")
    l2, = ax.plot(t, T_s, color="#d62728", linewidth=1.5, linestyle="--",
                  drawstyle="steps-post", label="T_s  (setpoint)")
    l3 = ax.axhline(T_o, color="grey", linewidth=1, linestyle=":", label=f"T_o = {T_o:.0f} °C")
    ax.set_ylabel("Temperature (°C)", fontsize=11)
    ax.set_ylim(12, 22)
    ax.set_title(
        f"Gas Boiler Space Heating – January 2026 (T_o = {T_o:.0f} °C)",
        fontsize=11,
        fontweight="bold",
    )
    _apply_schedule_ticks(ax)
    ax.set_xlabel("Time of day", fontsize=11)

    # ── Right axis: radiator power actually delivered ─────────────────────
    axr = ax.twinx()
    l4, = axr.plot(t, Q_r, color="#ff7f0e", linewidth=2, drawstyle="steps-post",
                   label="Q_r  (heat delivered, kW)")
    axr.fill_between(t, Q_r, step="post", alpha=0.20, color="#ff7f0e")
    axr.set_ylabel("Heat delivered (kW)", fontsize=11, color="#ff7f0e")
    axr.tick_params(axis="y", labelcolor="#ff7f0e")
    axr.set_ylim(0, 9)

    # combined legend – bottom left where the graph is empty
    lines = [l1, l2, l3, l4]
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


def plot_heat_pump_cop(result: dict, output_path: Path, show: bool = False, dpi: int = 200) -> Path:
    """Produce figure showing flow temperature and COP for equivalent heat pump variant.

    T_f (flow temperature) on the left y-axis;
    COP (coefficient of performance) on the right y-axis.

    Args:
        result: Dictionary returned by :func:`simulate_gas_boiler`.
        output_path: Destination PNG path.
        show: If True, call ``plt.show()`` after saving.
        dpi: Output resolution.

    Returns:
        The written ``output_path``.
    """
    t = result["t_h"]
    T_f = result["T_f"]
    cop = result["cop"]
    T_o = ThermalSystemParameters().T_o
    
    # Calculate heat pump variant costs
    hp_result = calculate_heat_pump_cost(result)
    elec_kwh = hp_result["electricity_kwh"]
    cost_gbp = hp_result["cost_gbp"]
    heat_kwh = result["total_heat_kwh"]

    fig, ax = plt.subplots(figsize=(11, 5))

    # ── Left axis: flow temperature ───────────────────────────────────────
    l1, = ax.plot(t, T_f, color="#1f77b4", linewidth=2, label="T_f  (flow temperature)")
    l2 = ax.axhline(T_o, color="grey", linewidth=1, linestyle=":", label=f"T_o = {T_o:.0f} °C")
    ax.set_ylabel("Flow temperature (°C)", fontsize=11)
    ax.set_ylim(20, 80)
    ax.set_title(
        f"Equivalent Heat Pump Variant – January 2026 (T_o = {T_o:.0f} °C)",
        fontsize=11,
        fontweight="bold",
    )
    _apply_schedule_ticks(ax)
    ax.set_xlabel("Time of day", fontsize=11)

    # ── Right axis: COP ───────────────────────────────────────────────────
    axr = ax.twinx()
    l3, = axr.plot(t, cop, color="#2ca02c", linewidth=2, drawstyle="steps-post",
                   label="COP")
    axr.set_ylabel("COP", fontsize=11, color="#2ca02c")
    axr.tick_params(axis="y", labelcolor="#2ca02c")
    axr.set_ylim(0, 7)

    # combined legend – bottom right
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


def main(argv: Iterable[str] | None = None) -> int:
    """Run the gas boiler simulation and save a plot.

    Example usage::

        heat-pump-gas-boiler
        heat-pump-gas-boiler --outdoor-temp 0 --q-max 15000
        heat-pump-gas-boiler --output assets/boiler_jan.png --show
    """
    from argparse import ArgumentParser

    parser = ArgumentParser(
        description="Simulate one day of gas boiler space heating and estimate cost."
    )
    parser.add_argument(
        "--outdoor-temp", type=float, default=5.0,
        help="Constant outdoor temperature T_o [°C] (default: 5.0)",
    )
    parser.add_argument(
        "--q-max", type=float, default=50_000.0,
        help="Boiler commanded power [W] (default: 50000, actual delivery limited by radiator)",
    )
    parser.add_argument(
        "--output", default="assets/gas_boiler_simulation.png",
        help="Output PNG path (default: assets/gas_boiler_simulation.png)",
    )
    parser.add_argument("--show", action="store_true", help="Display plot interactively")
    parser.add_argument("--dpi", type=int, default=200, help="Plot DPI (default: 200)")
    args = parser.parse_args(args=list(argv) if argv is not None else None)

    project_root = Path(__file__).resolve().parents[2]
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = project_root / output_path

    print(f"Simulating gas boiler: T_o = {args.outdoor_temp} °C …")
    result = simulate_gas_boiler(T_o=args.outdoor_temp, Q_max=args.q_max)

    h = ThermalSystemParameters().h
    steady_kw = h * (19.0 - args.outdoor_temp) / 1000.0

    print()
    print("─" * 55)
    print(f"  Steady-state heat loss  h·ΔT = {steady_kw:.2f} kW")
    print(f"  Total heat delivered         = {result['total_heat_kwh']:.1f} kWh/day")
    print(f"  Gas consumed (η=0.95)        = {result['gas_kwh']:.1f} kWh/day")
    print(f"  Gas cost (5.93 p/kWh)        = £{result['cost_gbp']:.2f}/day")
    print(f"  + standing charge            = £{GAS_STANDING_CHARGE:.2f}/day")
    print(f"  Total                        = £{result['cost_gbp'] + GAS_STANDING_CHARGE:.2f}/day")
    print("─" * 55)
    print()

    output_path = plot_gas_boiler(result, output_path, show=args.show, dpi=args.dpi)
    print(f"Saved plot to {output_path}")
    
    # Also generate heat pump variant plot
    hp_output_path = output_path.parent / output_path.name.replace("gas_boiler", "heat_pump_cop")
    hp_result = calculate_heat_pump_cost(result)
    print()
    print("─" * 55)
    print("  Equivalent Heat Pump Variant (same Q_r profile):")
    print(f"  Total heat delivered         = {result['total_heat_kwh']:.1f} kWh/day")
    print(f"  Electricity consumed         = {hp_result['electricity_kwh']:.1f} kWh/day")
    print(f"  Avg. seasonal COP            = {result['total_heat_kwh'] / hp_result['electricity_kwh']:.2f}")
    print(f"  Elec. cost (27.69 p/kWh)     = £{hp_result['cost_gbp']:.2f}/day")
    print(f"  + standing charge            = £{ELECTRICITY_STANDING_CHARGE:.2f}/day")
    print(f"  Total                        = £{hp_result['cost_gbp'] + ELECTRICITY_STANDING_CHARGE:.2f}/day")
    print("─" * 55)
    print()
    
    hp_output_path = plot_heat_pump_cop(result, hp_output_path, show=args.show, dpi=args.dpi)
    print(f"Saved heat pump COP plot to {hp_output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
