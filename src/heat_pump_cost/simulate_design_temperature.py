"""Simulate smooth heat pump space heating at design outdoor temperature (-2 °C).

Four scenarios:
  1. Smooth heating, current radiators  (K = 71.2 W/K^1.2)
  2. Smooth heating, upgraded radiators (K = 93.5 W/K^1.2)
  3. Smooth heating with DHW + defrost interruptions, current radiators
  4. Smooth heating with DHW + defrost interruptions, upgraded radiators

DHW slots (space heating suspended, HP heats hot-water cylinder instead):
  04:00–04:40  Morning pre-heat    (t =  6.00–6.67 h from 22:00)
  07:00–07:20  Morning top-up      (t =  9.00–9.33 h from 22:00)
  15:00–15:40  Afternoon pre-heat  (t = 17.00–17.67 h from 22:00)
  18:00–18:20  Evening top-up      (t = 20.00–20.33 h from 22:00)

Defrost cycles:
  ~10 minutes per hour outside DHW slots → space heating available 50/60 ≈ 83.3 % of the time.

DHW energy budget:
  200 l heated from 10 °C to 60 °C: Q_dhw = 200 × 4.18 × 50 / 3600 ≈ 11.6 kWh/day
  HP flow temperature to DHW cylinder ≈ 55 °C; COP evaluated at T_o = -2 °C, T_f = 55 °C.
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import lsq_linear

from heat_pump_cost.dynamic_thermal_model import DynamicThermalModel, ThermalSystemParameters
from heat_pump_cost.radiator_analysis import cop_estimate
from heat_pump_cost.simulate_smooth_heat_pump import (
    ELECTRICITY_PRICE_PER_KWH,
    ELECTRICITY_STANDING_CHARGE,
    TICK_HOURS,
    TICK_LABELS,
    _apply_schedule_ticks,
    _get_setpoint,
)
from matplotlib.patches import Patch

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

T_DESIGN: float = -2.0        # Design outdoor temperature [°C]
K_CURRENT: float = 71.2       # Current radiator constant  [W/K^1.2]
K_UPGRADE: float = 93.5       # Upgraded radiator constant [W/K^1.2]

GAS_PRICE_PER_KWH: float = 5.93 / 100.0   # £/kWh
BOILER_EFFICIENCY: float = 0.95
GAS_STANDING_CHARGE: float = 0.3509        # £/day

# DHW
DHW_THERMAL_KWH: float = 11.6    # kWh thermal per day (200 l, 10 → 60 °C)
DHW_FLOW_TEMP: float = 55.0      # °C — HP flow temperature to DHW cylinder

# DHW slot boundaries in hours-since-22:00 coordinates
# 04:00 → t=6, 07:00 → t=9, 15:00 → t=17, 18:00 → t=20
DHW_SLOTS: list[tuple[float, float]] = [
    (6.0,  6.0 + 40.0 / 60.0),   # 04:00–04:40  morning pre-heat
    (9.0,  9.0 + 20.0 / 60.0),   # 07:00–07:20  morning top-up
    (17.0, 17.0 + 40.0 / 60.0),  # 15:00–15:40  afternoon pre-heat
    (20.0, 20.0 + 20.0 / 60.0),  # 18:00–18:20  evening top-up
]

# Defrost: discrete 10-minute interruption each hour outside DHW slots.
# Modelled as the LAST 10 minutes of each hour having zero space-heating availability.
DEFROST_MINUTES_PER_HOUR: int = 10


# ---------------------------------------------------------------------------
# Availability model
# ---------------------------------------------------------------------------

def _availability(t_hours: float, with_interruptions: bool) -> float:
    """Return 1.0 if space heating is available this time-step, else 0.0.

    Without interruptions: always 1.0.
    With interruptions:
      - 0.0 during DHW slots (HP busy producing hot water).
      - 0.0 during the last DEFROST_MINUTES_PER_HOUR minutes of each hour.
      - 1.0 otherwise.
    """
    if not with_interruptions:
        return 1.0
    for start, end in DHW_SLOTS:
        if start <= t_hours < end:
            return 0.0
    # Defrost: last DEFROST_MINUTES_PER_HOUR minutes of each hour
    if t_hours % 1.0 >= (60 - DEFROST_MINUTES_PER_HOUR) / 60.0:
        return 0.0
    return 1.0


# ---------------------------------------------------------------------------
# Feedforward heating plan
# ---------------------------------------------------------------------------

def _build_heating_plan(
    K: float,
    T_o: float = T_DESIGN,
    T_i_0: float = 19.0,
    dt_s: float = 60.0,
    with_interruptions: bool = False,
) -> np.ndarray:
    """Compute 24 hourly heating powers [W] for a periodic feedforward day.

    Solves a bounded least-squares problem:

        minimise  ||W(S @ Q_h - (T_target - T_free))||^2
        subject to  lb[i] <= Q_h[i] <= ub[i]

    A final row forces periodicity: T_i(24 h) = T_i(0) = 19 °C.

    Bounds (commanded power — availability mask is already in S):
        Setback hours (22:00-06:00, 09:00-17:00) : [1 500, 2 500] W  ≈ 2 kW
        Comfort hours (06:00-09:00, 17:00-22:00) : [3 500, 6 000] W  ≈ 4–5 kW

    The sensitivity matrix accounts for the availability at every minute so the
    same function serves both the smooth and the interrupted scenarios.
    """
    params = ThermalSystemParameters()
    params.T_o = T_o
    params.K = K
    h_tc = params.h
    C    = params.C
    Qb   = params.Q_b

    n_steps = int(24 * 3600.0 / dt_s)
    tau   = C / h_tc
    alpha = math.exp(-dt_s / tau)
    beta  = (1.0 - alpha) / h_tc   # ∂T_i / ∂(one W-step of Q_r)

    # Build sensitivity matrix S and free trajectory T_free.
    # T_i[k] = T_free[k] + S[k, :] @ Q_h
    # We carry n_steps + 1 rows so row n_steps gives T_i at end-of-day.
    S      = np.zeros((n_steps + 1, 24))
    T_free = np.zeros(n_steps + 1)
    T_cur  = float(T_i_0)
    s_cur  = np.zeros(24)

    for k in range(n_steps):
        T_free[k] = T_cur
        S[k, :]   = s_cur
        t_h   = k * dt_s / 3600.0
        hour  = int(t_h) % 24
        avail = _availability(t_h, with_interruptions)
        # Advance free state
        T_cur = alpha * T_cur + (1.0 - alpha) * (T_o + Qb / h_tc)
        # Advance sensitivity row
        s_cur = alpha * s_cur
        s_cur[hour] += avail * beta

    T_free[n_steps] = T_cur
    S[n_steps, :]   = s_cur

    # Target temperatures and weights
    T_target = np.zeros(n_steps + 1)
    W        = np.zeros(n_steps + 1)
    
    # Track comfort period start times to implement ramping weights
    comfort_starts = []  # (start_idx, end_idx) tuples
    in_comfort_now = False
    comfort_start_idx = 0
    
    for k in range(n_steps):
        t_h = k * dt_s / 3600.0
        T_sp, _ = _get_setpoint(t_h)
        T_target[k] = T_sp
        
        # Detect comfort period boundaries
        is_comfort = T_sp >= 19.0
        if is_comfort and not in_comfort_now:
            comfort_start_idx = k
            in_comfort_now = True
        elif not is_comfort and in_comfort_now:
            comfort_starts.append((comfort_start_idx, k))
            in_comfort_now = False
    
    # Close final comfort period if it extends to end of day
    if in_comfort_now:
        comfort_starts.append((comfort_start_idx, n_steps))
    
    # Apply weights: low during setback, ramping heavily during comfort
    for k in range(n_steps):
        t_h = k * dt_s / 3600.0
        T_sp, _ = _get_setpoint(t_h)
        
        if T_sp >= 19.0:
            # During comfort period: ramp weight from 50 at start to 500 at end
            # This forces optimizer to reach target early and maintain it
            for start_idx, end_idx in comfort_starts:
                if start_idx <= k < end_idx:
                    period_length = end_idx - start_idx
                    progress = (k - start_idx) / max(1, period_length - 1)
                    # Quadratic ramp: gentler increase, tolerates small deviations
                    # Weight still encourages reaching target but less aggressively
                    W[k] = 20.0 + 180.0 * (progress ** 2)
                    break
        else:
            # Setback periods: low weight
            W[k] = 5.0

    # Periodicity: T_i(24 h) = T_i(0) — extremely high weight
    T_target[n_steps] = T_i_0
    W[n_steps] = 10_000.0

    # Hour-by-hour bounds with pre-heating allowance
    lb = np.zeros(24)
    ub = np.zeros(24)
    for h_idx in range(24):
        T_sp, _ = _get_setpoint(h_idx + 0.5)
        # Check if we're in a comfort period or within 2h before one
        # Morning comfort: t=8-11 (06:00-09:00), pre-heat from t=6 (04:00)
        # Evening comfort: t=19-24 (17:00-22:00), pre-heat from t=17 (15:00)
        in_comfort = T_sp >= 19.0
        before_morning = 6 <= h_idx < 8
        before_evening = 17 <= h_idx < 19
        
        if in_comfort or before_morning or before_evening:
            # Comfort or pre-heat periods: moderate power, max 6 kW
            lb[h_idx] = 2_500.0
            ub[h_idx] = 6_000.0
        else:
            # Setback periods: allow slightly more than before
            lb[h_idx] = 1_800.0
            ub[h_idx] = 2_500.0

    WA = S * W[:, np.newaxis]
    Wb = W * (T_target - T_free)
    result = lsq_linear(WA, Wb, bounds=(lb, ub), verbose=0)
    return result.x


# ---------------------------------------------------------------------------
# Core simulation loop
# ---------------------------------------------------------------------------

def _simulate(
    K: float,
    T_o: float = T_DESIGN,
    with_interruptions: bool = False,
    T_i_0: float = 19.0,
    dt_s: float = 60.0,
    hourly_powers: np.ndarray | None = None,
) -> dict:
    """Simulate one 24-hour day using feedforward hourly power schedule.

    Args:
        K: Radiator constant [W/K^1.2].
        T_o: Outdoor temperature [°C].
        with_interruptions: If True, apply DHW slots and defrost availability.
        T_i_0: Initial indoor temperature [°C].
        dt_s: Time step [s].
        hourly_powers: Feedforward schedule (24,) [W]. Must be provided.

    Returns:
        Result dictionary with time-series arrays and energy/cost scalars.
    """
    if hourly_powers is None:
        raise ValueError("hourly_powers must be provided")
    params = ThermalSystemParameters()
    params.T_o = T_o
    params.K = K
    model = DynamicThermalModel(params)

    n_steps = int(24 * 3600.0 / dt_s)

    t_h_arr = np.zeros(n_steps)
    T_i_arr = np.zeros(n_steps)
    T_s_arr = np.zeros(n_steps)
    T_f_arr = np.full(n_steps, np.nan)
    Q_r_arr = np.zeros(n_steps)
    cop_arr = np.zeros(n_steps)

    T_i = T_i_0
    T_f_last: float = float(T_i_0) + 10.0
    cop_last: float = cop_estimate(T_o, float(T_i_0) + 10.0)

    for i in range(n_steps):
        t_h = i * dt_s / 3600.0
        t_h_arr[i] = t_h

        T_s, _ = _get_setpoint(t_h)
        T_s_arr[i] = T_s

        in_dhw = with_interruptions and any(s <= t_h < e for s, e in DHW_SLOTS)
        avail  = _availability(t_h, with_interruptions)

        # Feedforward: fixed hourly power plan
        hour = int(t_h) % 24
        Q_r  = hourly_powers[hour] * avail

        T_i_arr[i] = T_i
        Q_r_arr[i] = Q_r

        # T_f / COP: NaN during DHW (line gap), held during defrost, computed otherwise
        if in_dhw:
            T_f_arr[i] = np.nan
            cop_arr[i] = np.nan
        elif avail == 0.0:               # defrost minute — hold last values
            T_f_arr[i] = T_f_last
            cop_arr[i] = cop_last
        elif Q_r > 1.0:
            # Solve for T_f from Q_r
            T_f = model.solve_flow_temp(Q_r, T_i)
            if T_f is None:
                T_f = T_f_last
            c = cop_estimate(T_o, T_f)
            T_f_arr[i] = T_f
            cop_arr[i] = c
            T_f_last = T_f
            cop_last = c
        else:
            T_f_arr[i] = T_f_last
            cop_arr[i] = 0.0

        Q_l = params.h * (T_i - T_o)
        dT_i_dt = (Q_r + params.Q_b - Q_l) / params.C
        T_i += dT_i_dt * dt_s

    # Energy and cost
    total_heat_kwh = float(np.sum(Q_r_arr * dt_s) / 3_600_000.0)
    valid = (Q_r_arr > 0) & (cop_arr > 0) & ~np.isnan(cop_arr)
    P_elec = np.where(valid, Q_r_arr / cop_arr, 0.0)
    electricity_kwh = float(np.sum(P_elec * dt_s) / 3_600_000.0)
    scop = total_heat_kwh / electricity_kwh if electricity_kwh > 0 else 0.0
    cost_gbp = electricity_kwh * ELECTRICITY_PRICE_PER_KWH

    # Average power during night (t=0–8) and day-away (t=11–19) periods
    night_mask = t_h_arr < 8.0
    day_mask = (t_h_arr >= 11.0) & (t_h_arr < 19.0)
    avg_night_w = float(np.mean(Q_r_arr[night_mask])) if np.any(night_mask) else 0.0
    avg_day_w = float(np.mean(Q_r_arr[day_mask])) if np.any(day_mask) else 0.0

    return {
        "t_h": t_h_arr,
        "T_i": T_i_arr,
        "T_s": T_s_arr,
        "T_f": T_f_arr,
        "Q_r": Q_r_arr,
        "cop": cop_arr,
        "T_o": T_o,
        "K": K,
        "total_heat_kwh": total_heat_kwh,
        "electricity_kwh": electricity_kwh,
        "scop": scop,
        "cost_gbp": cost_gbp,
        "avg_night_w": avg_night_w,
        "avg_day_w": avg_day_w,
    }


# ---------------------------------------------------------------------------
# Plotting helpers
# ---------------------------------------------------------------------------

def _shade_dhw_slots(ax: plt.Axes) -> None:
    """Add light grey vertical bands marking DHW slots."""
    for start, end in DHW_SLOTS:
        ax.axvspan(start, end, alpha=0.12, color="purple",
                   label="DHW slot" if start == DHW_SLOTS[0][0] else None)


def _plot_heating_profile(
    result: dict,
    output_path: Path,
    title: str,
    with_interruptions: bool = False,
    show: bool = False,
    dpi: int = 200,
) -> Path:
    """Plot indoor temperature (left axis) and heating power (right axis)."""
    t = result["t_h"]
    T_i = result["T_i"]
    T_s = result["T_s"]
    Q_r = result["Q_r"] / 1000.0  # W → kW

    fig, ax = plt.subplots(figsize=(11, 5))

    l1, = ax.plot(t, T_i, color="#1f77b4", linewidth=2, label="T_i  (indoor)")
    l2, = ax.plot(t, T_s, color="#d62728", linewidth=1.5, linestyle="--",
                  drawstyle="steps-post", label="T_s  (setpoint)")
    ax.set_ylabel("Temperature (°C)", fontsize=11)
    ax.set_ylim(10, 22)
    ax.set_title(title, fontsize=11, fontweight="bold")
    _apply_schedule_ticks(ax)
    ax.set_xlabel("Time of day", fontsize=11)

    axr = ax.twinx()
    l3, = axr.plot(t, Q_r, color="#ff7f0e", linewidth=2, label="Q_r  (heat delivered, kW)")
    axr.fill_between(t, Q_r, alpha=0.20, color="#ff7f0e")
    axr.set_ylabel("Heat delivered (kW)", fontsize=11, color="#ff7f0e")
    axr.tick_params(axis="y", labelcolor="#ff7f0e")
    axr.set_ylim(0, 7)

    lines = [l1, l2, l3]
    if with_interruptions:
        _shade_dhw_slots(ax)
        lines.append(Patch(facecolor="purple", alpha=0.25, label="DHW slot"))
    ax.legend(lines, [l.get_label() for l in lines], loc="lower left", fontsize=9)

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
    if show:
        plt.show()
    else:
        plt.close(fig)
    return output_path


def _plot_cop_profile(
    result: dict,
    output_path: Path,
    title: str,
    with_interruptions: bool = False,
    show: bool = False,
    dpi: int = 200,
) -> Path:
    """Plot flow temperature (left axis) and COP (right axis)."""
    t = result["t_h"]
    T_f = result["T_f"]
    cop = result["cop"]

    spark_gap = ELECTRICITY_PRICE_PER_KWH / GAS_PRICE_PER_KWH

    fig, ax = plt.subplots(figsize=(11, 5))

    # Plot with antialiasing for smooth appearance
    l1, = ax.plot(t, T_f, color="#1f77b4", linewidth=1.5, label="T_f  (flow temperature)", antialiased=True)
    ax.set_ylabel("Flow temperature (°C)", fontsize=11)
    T_f_valid = T_f[~np.isnan(T_f)]
    T_f_min = float(T_f_valid.min()) if len(T_f_valid) else 20.0
    T_f_max = float(T_f_valid.max()) if len(T_f_valid) else 55.0
    T_f_pad = max(3.0, (T_f_max - T_f_min) * 0.15)
    ax.set_ylim(T_f_min - T_f_pad, T_f_max + T_f_pad)
    ax.set_title(title, fontsize=11, fontweight="bold")
    _apply_schedule_ticks(ax)
    ax.set_xlabel("Time of day", fontsize=11)

    axr = ax.twinx()
    l2, = axr.plot(t, cop, color="#2ca02c", linewidth=1.5, label="COP", antialiased=True)
    l3 = axr.axhline(spark_gap, color="red", linewidth=1.2, linestyle="--",
                     label=f"Spark gap = {spark_gap:.2f}")
    axr.set_ylabel("COP", fontsize=11, color="#2ca02c")
    axr.tick_params(axis="y", labelcolor="#2ca02c")
    cop_valid = cop[~np.isnan(cop) & (cop > 0)]
    cop_lo = float(cop_valid.min()) if len(cop_valid) else 2.0
    cop_hi = float(cop_valid.max()) if len(cop_valid) else 6.0
    # Round to nearest 0.5 for clean axis
    cop_lo_round = np.floor(cop_lo * 2) / 2 - 0.5
    cop_hi_round = np.ceil(cop_hi * 2) / 2 + 0.5
    axr.set_ylim(cop_lo_round, cop_hi_round)
    # Set y-ticks at 0.5 intervals
    cop_ticks = np.arange(cop_lo_round, cop_hi_round + 0.1, 0.5)
    axr.set_yticks(cop_ticks)

    lines = [l1, l2, l3]
    if with_interruptions:
        _shade_dhw_slots(ax)
        lines.append(Patch(facecolor="purple", alpha=0.25, label="DHW slot"))
    ax.legend(lines, [l.get_label() for l in lines], loc="upper right", fontsize=9)

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
    if show:
        plt.show()
    else:
        plt.close(fig)
    return output_path


# ---------------------------------------------------------------------------
# Gas baseline cost helper
# ---------------------------------------------------------------------------

def _gas_cost(total_heat_kwh: float) -> tuple[float, float]:
    """Return (gas_kwh, total_cost_gbp) for equivalent gas boiler."""
    gas_kwh = total_heat_kwh / BOILER_EFFICIENCY
    cost = gas_kwh * GAS_PRICE_PER_KWH + GAS_STANDING_CHARGE
    return gas_kwh, cost


# ---------------------------------------------------------------------------
# CLI / main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    """Run four design-temperature scenarios, print results, save plots."""
    from argparse import ArgumentParser

    parser = ArgumentParser(
        description=(
            "Simulate smooth heat pump operation at design temperature (-2 °C). "
            "Produces four scenarios: current/upgraded radiators × "
            "no interruptions/with DHW+defrost."
        )
    )
    parser.add_argument("--show", action="store_true", help="Display plots interactively")
    parser.add_argument("--dpi", type=int, default=200, help="Plot DPI (default: 200)")
    args = parser.parse_args(args=argv)

    project_root = Path(__file__).resolve().parents[2]
    assets = project_root / "assets"

    spark_gap = ELECTRICITY_PRICE_PER_KWH / GAS_PRICE_PER_KWH
    cop_dhw = cop_estimate(T_DESIGN, DHW_FLOW_TEMP)
    dhw_elec_kwh = DHW_THERMAL_KWH / cop_dhw
    dhw_cost_gbp = dhw_elec_kwh * ELECTRICITY_PRICE_PER_KWH

    print(f"\nDesign temperature:  T_o = {T_DESIGN:.0f} °C")
    print(f"Spark gap (Jan 2026): {spark_gap:.2f}  ({ELECTRICITY_PRICE_PER_KWH*100:.2f}p / {GAS_PRICE_PER_KWH*100:.2f}p)")
    print(f"DHW  COP at T_o={T_DESIGN:.0f}°C, T_f={DHW_FLOW_TEMP:.0f}°C: {cop_dhw:.2f}")
    print(f"DHW  electricity:  {dhw_elec_kwh:.2f} kWh/day  ({DHW_THERMAL_KWH:.1f} kWh thermal)")
    print(f"DHW  energy cost:  £{dhw_cost_gbp:.2f}/day")

    print(f"\n{'─'*66}")
    print(f"  Scenario 1 — smooth, current radiators (K = {K_CURRENT:.1f} W/K^1.2)")
    print(f"{'─'*66}")
    Q_h1 = _build_heating_plan(K=K_CURRENT, T_o=T_DESIGN, with_interruptions=False)
    r1 = _simulate(K=K_CURRENT, T_o=T_DESIGN, with_interruptions=False, hourly_powers=Q_h1)
    gas_kwh1, gas_cost1 = _gas_cost(r1["total_heat_kwh"])
    print(f"  Night avg heating power:  {r1['avg_night_w']:.0f} W")
    print(f"  Day  avg heating power:   {r1['avg_day_w']:.0f} W")
    print(f"  Heat delivered:           {r1['total_heat_kwh']:.1f} kWh/day")
    print(f"  Gas equivalent:           {gas_kwh1:.1f} kWh/day → £{gas_cost1:.2f}/day (incl. SC)")
    print(f"  HP electricity:           {r1['electricity_kwh']:.1f} kWh/day")
    print(f"  SCOP:                     {r1['scop']:.2f}  (break-even spark gap ≈ {r1['scop']:.2f})")
    print(f"  HP energy cost:           £{r1['cost_gbp']:.2f}/day  (vs gas £{gas_cost1:.2f}/day)")

    _plot_heating_profile(
        r1,
        assets / "design_heating_profile.png",
        f"Design-temperature heating profile – T_o = {T_DESIGN:.0f} °C, "
        f"K = {K_CURRENT:.1f} W/K^1.2",
        with_interruptions=False,
        show=args.show,
        dpi=args.dpi,
    )
    print(f"  Saved: assets/design_heating_profile.png")

    _plot_cop_profile(
        r1,
        assets / "design_flow_temperature_cop.png",
        f"Flow temperature & COP – T_o = {T_DESIGN:.0f} °C, "
        f"current radiators (K = {K_CURRENT:.1f} W/K^1.2)",
        with_interruptions=False,
        show=args.show,
        dpi=args.dpi,
    )
    print(f"  Saved: assets/design_flow_temperature_cop.png")

    # ── Scenario 2: smooth, upgraded radiators ────────────────────────────
    print(f"\n{'─'*66}")
    print(f"  Scenario 2 — smooth, upgraded radiators (K = {K_UPGRADE:.1f} W/K^1.2)")
    print(f"{'─'*66}")
    Q_h2 = _build_heating_plan(K=K_UPGRADE, T_o=T_DESIGN, with_interruptions=False)
    r2 = _simulate(K=K_UPGRADE, T_o=T_DESIGN, with_interruptions=False, hourly_powers=Q_h2)
    gas_kwh2, gas_cost2 = _gas_cost(r2["total_heat_kwh"])
    print(f"  Night avg heating power:  {r2['avg_night_w']:.0f} W")
    print(f"  Day  avg heating power:   {r2['avg_day_w']:.0f} W")
    print(f"  Heat delivered:           {r2['total_heat_kwh']:.1f} kWh/day")
    print(f"  Gas equivalent:           {gas_kwh2:.1f} kWh/day → £{gas_cost2:.2f}/day (incl. SC)")
    print(f"  HP electricity:           {r2['electricity_kwh']:.1f} kWh/day")
    print(f"  SCOP:                     {r2['scop']:.2f}  (break-even spark gap ≈ {r2['scop']:.2f})")
    print(f"  HP energy cost:           £{r2['cost_gbp']:.2f}/day  (vs gas £{gas_cost2:.2f}/day)")

    _plot_cop_profile(
        r2,
        assets / "design_flow_temperature_cop_upgrade.png",
        f"Flow temperature & COP – T_o = {T_DESIGN:.0f} °C, "
        f"upgraded radiators (K = {K_UPGRADE:.1f} W/K^1.2)",
        with_interruptions=False,
        show=args.show,
        dpi=args.dpi,
    )
    print(f"  Saved: assets/design_flow_temperature_cop_upgrade.png")

    # ── Scenario 3: with interruptions, current radiators ─────────────────
    print(f"\n{'─'*66}")
    print(f"  Scenario 3 — with DHW+defrost, current radiators (K = {K_CURRENT:.1f} W/K^1.2)")
    print(f"{'─'*66}")
    Q_h3 = _build_heating_plan(K=K_CURRENT, with_interruptions=True)
    r3 = _simulate(K=K_CURRENT, with_interruptions=True, hourly_powers=Q_h3)
    gas_kwh3, gas_cost3 = _gas_cost(r3["total_heat_kwh"])
    total_elec3 = r3["electricity_kwh"] + dhw_elec_kwh
    total_cost3 = total_elec3 * ELECTRICITY_PRICE_PER_KWH
    combined_heat3 = r3["total_heat_kwh"] + DHW_THERMAL_KWH
    combined_scop3 = combined_heat3 / total_elec3
    print(f"  Night avg heating power:  {r3['avg_night_w']:.0f} W")
    print(f"  Day  avg heating power:   {r3['avg_day_w']:.0f} W")
    print(f"  Space heat:               {r3['total_heat_kwh']:.1f} kWh/day")
    print(f"  Gas equivalent:           {gas_kwh3:.1f} kWh/day → £{gas_cost3:.2f}/day (incl. SC)")
    print(f"  HP space electricity:     {r3['electricity_kwh']:.1f} kWh/day  (SCOP {r3['scop']:.2f})")
    print(f"  HP DHW  electricity:      {dhw_elec_kwh:.2f} kWh/day  (COP {cop_dhw:.2f})")
    print(f"  HP total electricity:     {total_elec3:.1f} kWh/day  (combined SCOP {combined_scop3:.2f})")
    print(f"  HP energy cost:           £{total_cost3:.2f}/day  (vs gas £{gas_cost3:.2f}/day)")
    print(f"  Break-even spark gap:     ≈ {combined_scop3:.2f}")

    _plot_heating_profile(
        r3,
        assets / "design_heating_profile_with_gaps.png",
        f"Design-temperature heating profile with interruptions – T_o = {T_DESIGN:.0f} °C, "
        f"K = {K_CURRENT:.1f} W/K^1.2",
        with_interruptions=True,
        show=args.show,
        dpi=args.dpi,
    )
    print(f"  Saved: assets/design_heating_profile_with_gaps.png")

    _plot_cop_profile(
        r3,
        assets / "design_flow_temperature_cop_gaps.png",
        f"Flow temperature & COP with interruptions – T_o = {T_DESIGN:.0f} °C, "
        f"current radiators (K = {K_CURRENT:.1f} W/K^1.2)",
        with_interruptions=True,
        show=args.show,
        dpi=args.dpi,
    )
    print(f"  Saved: assets/design_flow_temperature_cop_gaps.png")

    # ── Scenario 4: with interruptions, upgraded radiators ────────────────
    print(f"\n{'─'*66}")
    print(f"  Scenario 4 — with DHW+defrost, upgraded radiators (K = {K_UPGRADE:.1f} W/K^1.2)")
    print(f"{'─'*66}")
    Q_h4 = _build_heating_plan(K=K_UPGRADE, with_interruptions=True)
    r4 = _simulate(K=K_UPGRADE, with_interruptions=True, hourly_powers=Q_h4)
    gas_kwh4, gas_cost4 = _gas_cost(r4["total_heat_kwh"])
    total_elec4 = r4["electricity_kwh"] + dhw_elec_kwh
    total_cost4 = total_elec4 * ELECTRICITY_PRICE_PER_KWH
    combined_heat4 = r4["total_heat_kwh"] + DHW_THERMAL_KWH
    combined_scop4 = combined_heat4 / total_elec4
    print(f"  Night avg heating power:  {r4['avg_night_w']:.0f} W")
    print(f"  Day  avg heating power:   {r4['avg_day_w']:.0f} W")
    print(f"  Space heat:               {r4['total_heat_kwh']:.1f} kWh/day")
    print(f"  Gas equivalent:           {gas_kwh4:.1f} kWh/day → £{gas_cost4:.2f}/day (incl. SC)")
    print(f"  HP space electricity:     {r4['electricity_kwh']:.1f} kWh/day  (SCOP {r4['scop']:.2f})")
    print(f"  HP DHW  electricity:      {dhw_elec_kwh:.2f} kWh/day  (COP {cop_dhw:.2f})")
    print(f"  HP total electricity:     {total_elec4:.1f} kWh/day  (combined SCOP {combined_scop4:.2f})")
    print(f"  HP energy cost:           £{total_cost4:.2f}/day  (vs gas £{gas_cost4:.2f}/day)")
    print(f"  Break-even spark gap:     ≈ {combined_scop4:.2f}")

    _plot_cop_profile(
        r4,
        assets / "design_flow_temperature_cop_gaps_upgrade.png",
        f"Flow temperature & COP with interruptions – T_o = {T_DESIGN:.0f} °C, "
        f"upgraded radiators (K = {K_UPGRADE:.1f} W/K^1.2)",
        with_interruptions=True,
        show=args.show,
        dpi=args.dpi,
    )
    print(f"  Saved: assets/design_flow_temperature_cop_gaps_upgrade.png")

    # ── Conclusion summary ─────────────────────────────────────────────────
    UPGRADE_COST_GBP = 2000.0
    design_days_per_year = 10
    daily_saving = total_cost3 - total_cost4
    days_to_break_even = UPGRADE_COST_GBP / daily_saving if daily_saving > 0 else float("inf")
    years_to_break_even = days_to_break_even / design_days_per_year

    print(f"\n{'─'*66}")
    print(f"  Conclusion")
    print(f"{'─'*66}")
    print(f"  With DHW+defrost, current radiators:  £{total_cost3:.2f}/day  (SCOP {combined_scop3:.2f})")
    print(f"  With DHW+defrost, upgraded radiators: £{total_cost4:.2f}/day  (SCOP {combined_scop4:.2f})")
    print(f"  Daily saving from upgrade:            £{daily_saving:.2f}/day")
    print(f"  Upgrade cost: £{UPGRADE_COST_GBP:.0f}")
    print(f"  Design-temp days to break even:       {days_to_break_even:.0f} days")
    print(f"  Years to break even ({design_days_per_year} days/year):      {years_to_break_even:.0f} years")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
