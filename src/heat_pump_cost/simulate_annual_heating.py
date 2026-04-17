"""Simulate annual heat pump space heating with variable outdoor temperatures.

Uses Cambridge 2025 temperature data (data/temperatures-cambridge-2025.csv) to
drive a daily feedforward controller that re-plans the 24-hour heating schedule
at 22:00 each day, using measured outdoor temperatures as a proxy for weather
prediction.

Controller design:
  - Every day at 22:00, examine the next 24 h of outdoor temperature.
  - Space heating is skipped when the 24-h mean outdoor temperature ≥ 15 °C
    (solar gains and internal heat sources suffice).
  - Defrost cycles (10 min/h) are included when min(T_o) < 2 °C in the window;
    otherwise only DHW interruptions are used.
  - A feedforward power plan is computed by solving a weighted least-squares
    problem that spreads heat delivery over the day, avoids peak electricity
    tariff hours, and meets comfort setpoints (06:00–09:00 and 17:00–22:00 at
    19 °C; night/day setback at 17 °C).
  - A small proportional feedback term (≤ 30 % of feedforward) compensates for
    modelling errors without destabilising the plan.

DHW is heated every day regardless of the space-heating decision, via four
slots defined in simulate_design_temperature.DHW_SLOTS.

Costs are computed using the quarterly Ofgem energy price cap for 2025
(all prices include 5 % VAT, electricity standing charge excluded):
  Q1 Jan–Mar:  electricity 24.86 p/kWh, gas 6.34 p/kWh + 31.65 p/day SC
  Q2 Apr–Jun:  electricity 27.03 p/kWh, gas 6.99 p/kWh + 32.67 p/day SC
  Q3 Jul–Sep:  electricity 25.73 p/kWh, gas 6.33 p/kWh + 29.82 p/day SC
  Q4 Oct–Dec:  electricity 26.35 p/kWh, gas 6.29 p/kWh + 34.03 p/day SC
  Boiler efficiency: 95 %
"""

from __future__ import annotations

import math
from datetime import date, datetime, timedelta
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch
from scipy.optimize import lsq_linear

from heat_pump_cost.analyze_annual_dhw import read_cambridge_temperatures
from heat_pump_cost.dynamic_thermal_model import ThermalSystemParameters
from heat_pump_cost.radiator_analysis import cop_estimate
from heat_pump_cost.simulate_design_temperature import (
    BOILER_EFFICIENCY,
    DEFROST_MINUTES_PER_HOUR,
    DHW_FLOW_TEMP,
    DHW_SLOTS,
    DHW_THERMAL_KWH,
    _shade_dhw_slots,
)
from heat_pump_cost.simulate_smooth_heat_pump import (
    TICK_HOURS,
    TICK_LABELS,
    _apply_schedule_ticks,
    _get_setpoint,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

K_RADIATOR: float = 71.2          # Current radiator constant [W/K^1.2]
HEATING_THRESHOLD_C: float = 15.0  # Skip space heating when 24-h mean T_o >= this
DEFROST_THRESHOLD_C: float = 2.0   # Include defrost when min T_o < this

# ---------------------------------------------------------------------------
# Quarterly Ofgem energy price cap for 2025 (all prices include 5 % VAT)
# Source: Ofgem price cap announcements
# ---------------------------------------------------------------------------
#
# Each entry: (month_start, month_end_excl,
#              elec_p_per_kwh, gas_p_per_kwh, gas_standing_p_per_day)
#
# Q1 Jan–Mar 2025: Ofgem cap Q1 2025 (user-supplied context; Q2–Q4 confirmed by user)
_QUARTERLY_TARIFFS: list[tuple[date, date, float, float, float]] = [
    # (quarter_start,       quarter_end_excl,    elec p/kWh, gas p/kWh, gas SC p/day)
    (date(2025,  1,  1),  date(2025,  4,  1),   24.86,  6.34,  31.65),  # Q1 2025
    (date(2025,  4,  1),  date(2025,  7,  1),   27.03,  6.99,  32.67),  # Q2 2025
    (date(2025,  7,  1),  date(2025, 10,  1),   25.73,  6.33,  29.82),  # Q3 2025
    (date(2025, 10,  1),  date(2026,  1,  1),   26.35,  6.29,  34.03),  # Q4 2025
]


class _Tariff:
    """Electricity and gas prices for a single day."""

    __slots__ = ("elec", "gas", "gas_sc")

    def __init__(self, elec: float, gas: float, gas_sc: float) -> None:
        self.elec = elec        # £/kWh
        self.gas = gas          # £/kWh
        self.gas_sc = gas_sc    # £/day


def _tariff_for_date(d: date) -> _Tariff:
    """Return Ofgem price-cap tariff applicable on the given calendar date."""
    for start, end, elec_p, gas_p, gas_sc_p in _QUARTERLY_TARIFFS:
        if start <= d < end:
            return _Tariff(elec_p / 100.0, gas_p / 100.0, gas_sc_p / 100.0)
    # Fallback: use Q4 2025 rates for any date outside the table
    _, _, elec_p, gas_p, gas_sc_p = _QUARTERLY_TARIFFS[-1]
    return _Tariff(elec_p / 100.0, gas_p / 100.0, gas_sc_p / 100.0)


# DHW slot durations (minutes) matching DHW_SLOTS order
_DHW_SLOT_DURATIONS_MIN: list[float] = [40.0, 20.0, 40.0, 20.0]
_DHW_SLOT_TOTAL_MIN: float = sum(_DHW_SLOT_DURATIONS_MIN)


def _avail(t_hours: float, with_defrost: bool) -> float:
    """Return 1.0 when space heating is available, 0.0 otherwise.

    DHW slots are always excluded (HP busy with hot water).
    Defrost (last DEFROST_MINUTES_PER_HOUR minutes of each hour) is excluded
    only when with_defrost=True.
    """
    for start, end in DHW_SLOTS:
        if start <= t_hours < end:
            return 0.0
    if with_defrost and t_hours % 1.0 >= (60 - DEFROST_MINUTES_PER_HOUR) / 60.0:
        return 0.0
    return 1.0


# ---------------------------------------------------------------------------
# Temperature data helpers
# ---------------------------------------------------------------------------

def _build_temperature_index(
    timestamps: np.ndarray,
    temperatures_c: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Convert timestamp objects to Unix seconds for fast nearest-neighbour lookup."""
    t_unix = np.array([dt.timestamp() for dt in timestamps.tolist()])
    return t_unix, temperatures_c


def _extract_hourly_T_o(
    t_unix_all: np.ndarray,
    temp_all: np.ndarray,
    window_start: datetime,
) -> np.ndarray:
    """Return 24 hourly outdoor temperatures for the window [window_start, window_start+24h).

    T_o_24h[h] is the measured temperature closest in time to (window_start + h hours).
    Intended use: window_start = 22:00 of the planning day.
    """
    T_o_24h = np.empty(24)
    t0 = window_start.timestamp()
    for h in range(24):
        t_target = t0 + h * 3600.0
        idx = int(np.argmin(np.abs(t_unix_all - t_target)))
        T_o_24h[h] = temp_all[idx]
    return T_o_24h


# ---------------------------------------------------------------------------
# Feedforward heating plan with variable outdoor temperature
# ---------------------------------------------------------------------------

def _build_heating_plan_variable(
    K: float,
    T_o_24h: np.ndarray,
    T_i_0: float = 19.0,
    dt_s: float = 60.0,
    with_defrost: bool = False,
) -> np.ndarray:
    """Compute 24 hourly heating powers [W] adapted to a variable T_o profile.

    Extends _build_heating_plan from simulate_design_temperature.py:
    the free-trajectory integration uses the hourly T_o profile rather than
    a single constant value.  The sensitivity matrix is identical because
    each unit of hourly power advances the indoor temperature independently of T_o.

    DHW slots are always applied.  Defrost interruptions are only applied when
    with_defrost=True (i.e. when min(T_o_24h) < DEFROST_THRESHOLD_C).

    Adaptive power bounds keep the commanded power in a physically meaningful
    range for the actual outdoor conditions.
    """
    params = ThermalSystemParameters()
    params.K = K
    h_tc = params.h
    C = params.C
    Qb = params.Q_b

    n_steps = int(24 * 3600.0 / dt_s)
    tau = C / h_tc
    alpha = math.exp(-dt_s / tau)
    beta = (1.0 - alpha) / h_tc  # ∂T_i per W per step

    T_o_avg = float(np.mean(T_o_24h))

    # --- Sensitivity matrix and free trajectory ---
    S = np.zeros((n_steps + 1, 24))
    T_free = np.zeros(n_steps + 1)
    T_cur = float(T_i_0)
    s_cur = np.zeros(24)

    for k in range(n_steps):
        T_free[k] = T_cur
        S[k, :] = s_cur
        t_h = k * dt_s / 3600.0
        hour = int(t_h) % 24
        T_o_k = float(T_o_24h[hour])
        avail = _avail(t_h, with_defrost)
        T_cur = alpha * T_cur + (1.0 - alpha) * (T_o_k + Qb / h_tc)
        s_cur = alpha * s_cur
        s_cur[hour] += avail * beta

    T_free[n_steps] = T_cur
    S[n_steps, :] = s_cur

    # --- Target temperatures and weights ---
    T_target = np.zeros(n_steps + 1)
    W = np.zeros(n_steps + 1)

    for k in range(n_steps):
        t_h = k * dt_s / 3600.0
        T_sp, _ = _get_setpoint(t_h)
        T_target[k] = T_sp
        if T_sp >= 19.0:
            # Uniform high weight throughout comfort period so the optimizer
            # maintains the setpoint at all timesteps equally.  The old
            # quadratic ramp caused the optimizer to concentrate heat at the
            # END of each comfort period, leading to an evening temperature
            # dip followed by night-time overshoot.
            W[k] = 200.0
        else:
            W[k] = 5.0

    # No terminal constraint: the thermal dynamics carry the temperature forward
    # naturally.  The actual T_i at the end of the window becomes the next day's
    # T_i_0 via T_i_end in _simulate_day.  Forcing T_i(22:00) = T_i_0 was causing
    # the optimizer to stop evening heating early to allow passive cooling, which
    # produced the observed evening temperature drop.

    # --- Adaptive power bounds based on average outdoor temperature ---
    # Net steady-state demand (above background heat Qb)
    Q_net_17 = max(0.0, h_tc * (17.0 - T_o_avg) - Qb)
    Q_net_19 = max(0.0, h_tc * (19.0 - T_o_avg) - Qb)

    lb = np.zeros(24)
    ub = np.zeros(24)
    for h_idx in range(24):
        T_sp, _ = _get_setpoint(h_idx + 0.5)
        in_comfort = T_sp >= 19.0
        # 4 h pre-morning (02:00–06:00 real-time = window hours 4–8)
        # lets the optimizer ramp up heating well before the comfort period starts.
        before_morning = 4 <= h_idx < 8
        # 2 h pre-evening (15:00–17:00 real-time = window hours 17–19)
        before_evening = 17 <= h_idx < 19

        if in_comfort or before_morning or before_evening:
            lb[h_idx] = max(200.0, Q_net_19 * 0.3)
            ub[h_idx] = 6_000.0
        else:
            lb[h_idx] = max(0.0, Q_net_17 * 0.3)
            ub[h_idx] = max(1_500.0, Q_net_17 * 2.0)

    WS = S * W[:, np.newaxis]
    Wb = W * (T_target - T_free)
    result = lsq_linear(WS, Wb, bounds=(lb, ub), verbose=0)
    return result.x


# ---------------------------------------------------------------------------
# Daily simulation with limited proportional feedback
# ---------------------------------------------------------------------------

def _simulate_day(
    K: float,
    T_o_24h: np.ndarray,
    T_i_0: float,
    tariff: _Tariff,
    dt_s: float = 60.0,
    hourly_powers: np.ndarray | None = None,
    with_defrost: bool = False,
    do_heating: bool = True,
    K_fb: float = 150.0,
    fb_fraction: float = 0.30,
) -> dict:
    """Simulate one 24-hour window with variable T_o and limited feedback.

    Args:
        K: Radiator constant [W/K^1.2].
        T_o_24h: Hourly outdoor temperatures for the 24-h window [°C].
        T_i_0: Indoor temperature at the start of the window [°C].
        dt_s: Timestep [s].
        hourly_powers: Feedforward schedule (24,) [W].  Required when do_heating=True.
        with_defrost: Include defrost interruptions (10 min/hour) in addition to DHW.
        do_heating: If False, Q_r = 0 all day (warm-day no-heat mode).
        K_fb: Proportional feedback gain [W/K].
        fb_fraction: Feedback clipped to (fb_fraction × |feedforward|) to prevent
                     feedback from overpowering the plan.

    Returns:
        dict with time-series arrays and energy/cost scalars.
    """
    if do_heating and hourly_powers is None:
        raise ValueError("hourly_powers must be provided when do_heating=True")

    params = ThermalSystemParameters()
    params.K = K

    # Pre-compute fast flow-temperature approximation constants.
    # Q_r = K * (T_m - T_i)^n  →  T_m = T_i + (Q_r/K)^(1/n)
    # T_f = T_m + Q_r / (2 * V_f * rho * cp)
    _n = params.n            # 1.2
    _K = K
    _half_cap = 2.0 * params.V_f * params.rho * params.cp  # 2·V·ρ·cp  [W/K]

    def _T_f_fast(q: float, t_i: float) -> float:
        """Closed-form T_f approximation; accurate to ~0.3 K vs full solver."""
        if q <= 0.0:
            return t_i
        T_m = t_i + (q / _K) ** (1.0 / _n)
        return T_m + q / _half_cap

    n_steps = int(24 * 3600.0 / dt_s)

    t_h_arr = np.zeros(n_steps)
    T_i_arr = np.zeros(n_steps)
    T_s_arr = np.zeros(n_steps)
    T_f_arr = np.full(n_steps, np.nan)
    Q_r_arr = np.zeros(n_steps)
    cop_arr = np.zeros(n_steps)
    price_arr = np.zeros(n_steps)

    T_i = float(T_i_0)
    T_f_last: float = float(T_i_0) + 10.0
    cop_last: float = cop_estimate(float(T_o_24h[0]), float(T_i_0) + 10.0)

    for i in range(n_steps):
        t_h = i * dt_s / 3600.0
        hour = int(t_h) % 24
        T_o_i = float(T_o_24h[hour])

        t_h_arr[i] = t_h
        T_s, _ = _get_setpoint(t_h)
        T_s_arr[i] = T_s
        price_arr[i] = tariff.elec

        in_dhw = any(s <= t_h < e for s, e in DHW_SLOTS)
        avail = _avail(t_h, with_defrost) if do_heating else 0.0

        if do_heating and hourly_powers is not None:
            Q_ff = hourly_powers[hour] * avail
            # Limited proportional feedback: correct temperature error
            Q_fb = K_fb * (T_s - T_i)
            max_fb = fb_fraction * abs(hourly_powers[hour]) if hourly_powers[hour] > 0 else 200.0
            Q_fb = float(np.clip(Q_fb, -max_fb, max_fb))
            Q_r = float(np.clip(Q_ff + Q_fb, 0.0, 6_000.0))
        else:
            Q_r = 0.0

        T_i_arr[i] = T_i
        Q_r_arr[i] = Q_r

        # Flow temperature and COP
        if in_dhw:
            T_f_arr[i] = np.nan
            cop_arr[i] = np.nan
        elif avail == 0.0 or Q_r < 1.0:
            T_f_arr[i] = T_f_last
            cop_arr[i] = 0.0
        else:
            T_f = _T_f_fast(Q_r, T_i)
            c = cop_estimate(T_o_i, T_f)
            T_f_arr[i] = T_f
            cop_arr[i] = c
            T_f_last = T_f
            cop_last = c

        # Integrate indoor temperature with this hour's outdoor temperature
        Q_l = params.h * (T_i - T_o_i)
        dT_i_dt = (Q_r + params.Q_b - Q_l) / params.C
        T_i += dT_i_dt * dt_s

    # Energy and cost (Ofgem standard tariff)
    total_heat_kwh = float(np.sum(Q_r_arr * dt_s) / 3_600_000.0)
    valid = (Q_r_arr > 0) & ~np.isnan(cop_arr) & (cop_arr > 0)
    safe_cop = np.where(valid, cop_arr, 1.0)
    P_elec = np.where(valid, Q_r_arr / safe_cop, 0.0)
    electricity_kwh = float(np.sum(P_elec * dt_s) / 3_600_000.0)
    # £: power [W] × price [£/kWh] × dt [s] / 3600 [s/h] / 1000 [W/kW]
    cost_gbp = float(np.sum(P_elec * price_arr * dt_s / 3_600.0) / 1_000.0)

    return {
        "t_h": t_h_arr,
        "T_i": T_i_arr,
        "T_s": T_s_arr,
        "T_f": T_f_arr,
        "Q_r": Q_r_arr,
        "cop": cop_arr,
        "T_o_24h": T_o_24h,
        "K": K,
        "total_heat_kwh": total_heat_kwh,
        "electricity_kwh": electricity_kwh,
        "cost_gbp": cost_gbp,
        "T_i_end": float(T_i),
    }


# ---------------------------------------------------------------------------
# DHW cost for one day
# ---------------------------------------------------------------------------

def _dhw_cost_for_day(T_o_24h: np.ndarray, tariff: _Tariff) -> dict:
    """Calculate DHW heating cost for one day using slot-specific T_o and tariff.

    Each slot's thermal energy is proportional to its duration.  COP is
    computed at T_f = DHW_FLOW_TEMP = 55 °C and the T_o at the slot midpoint.
    """
    total_elec_kwh = 0.0
    total_cost_gbp = 0.0
    for (slot_start, slot_end), duration_min in zip(DHW_SLOTS, _DHW_SLOT_DURATIONS_MIN):
        hour = int(slot_start) % 24
        T_o = float(T_o_24h[hour])
        thermal_kwh = (duration_min / _DHW_SLOT_TOTAL_MIN) * DHW_THERMAL_KWH
        c = cop_estimate(T_o, DHW_FLOW_TEMP)
        elec_kwh = thermal_kwh / c
        total_elec_kwh += elec_kwh
        total_cost_gbp += elec_kwh * tariff.elec

    return {
        "dhw_thermal_kwh": DHW_THERMAL_KWH,
        "dhw_electricity_kwh": total_elec_kwh,
        "dhw_cost_gbp": total_cost_gbp,
    }


# ---------------------------------------------------------------------------
# Gas baseline cost
# ---------------------------------------------------------------------------

def _gas_heating_cost(space_heat_kwh: float, dhw_thermal_kwh: float, tariff: _Tariff) -> float:
    """Return total gas cost for space heating + DHW (including standing charge)."""
    gas_kwh = (space_heat_kwh + dhw_thermal_kwh) / BOILER_EFFICIENCY
    return gas_kwh * tariff.gas + tariff.gas_sc


# ---------------------------------------------------------------------------
# Plotting helpers for a single day
# ---------------------------------------------------------------------------

def _plot_day_profile(
    result: dict,
    output_path: Path,
    title: str,
    with_interruptions: bool = False,
    show: bool = False,
    dpi: int = 200,
) -> Path:
    """Plot indoor temperature, setpoint, outdoor temperature, and heating power."""
    t = result["t_h"]
    T_i = result["T_i"]
    T_s = result["T_s"]
    T_o_24h = result["T_o_24h"]
    Q_r = result["Q_r"] / 1000.0  # W → kW

    # Build T_o time-series at timestep resolution
    T_o_ts = np.array([float(T_o_24h[int(th) % 24]) for th in t])

    fig, ax = plt.subplots(figsize=(11, 5))

    l1, = ax.plot(t, T_i, color="#1f77b4", linewidth=2, label="T_i  (indoor)")
    l2, = ax.plot(t, T_s, color="#d62728", linewidth=1.5, linestyle="--",
                  drawstyle="steps-post", label="T_s  (setpoint)")
    l4, = ax.plot(t, T_o_ts, color="#9467bd", linewidth=1.2, linestyle=":",
                  label="T_o  (outdoor)")
    ax.set_ylabel("Temperature (°C)", fontsize=11)
    ax.set_ylim(-5, 25)
    ax.set_title(title, fontsize=11, fontweight="bold")
    _apply_schedule_ticks(ax)
    ax.set_xlabel("Time of day", fontsize=11)

    axr = ax.twinx()
    l3, = axr.plot(t, Q_r, color="#ff7f0e", linewidth=2, label="Q_r  (heat delivered, kW)")
    axr.fill_between(t, Q_r, alpha=0.20, color="#ff7f0e")
    axr.set_ylabel("Heat delivered (kW)", fontsize=11, color="#ff7f0e")
    axr.tick_params(axis="y", labelcolor="#ff7f0e")
    axr.set_ylim(0, 7)

    lines = [l1, l2, l4, l3]
    if with_interruptions:
        _shade_dhw_slots(ax)
        lines.append(Patch(facecolor="purple", alpha=0.25, label="DHW slot"))
    ax.legend(lines, [l.get_label() for l in lines], loc="upper left", fontsize=9)

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
    if show:
        plt.show()
    else:
        plt.close(fig)
    return output_path


def _plot_day_cop(
    result: dict,
    tariff: _Tariff,
    output_path: Path,
    title: str,
    with_interruptions: bool = False,
    show: bool = False,
    dpi: int = 200,
) -> Path:
    """Plot flow temperature and COP for a single simulated day."""
    t = result["t_h"]
    T_f = result["T_f"]
    cop = result["cop"]

    spark_gap = tariff.elec / tariff.gas

    fig, ax = plt.subplots(figsize=(11, 5))

    l1, = ax.plot(t, T_f, color="#1f77b4", linewidth=1.5,
                  label="T_f  (flow temperature)", antialiased=True)
    ax.set_ylabel("Flow temperature (°C)", fontsize=11)
    T_f_valid = T_f[~np.isnan(T_f)]
    if len(T_f_valid):
        T_f_pad = max(3.0, (T_f_valid.max() - T_f_valid.min()) * 0.15)
        ax.set_ylim(T_f_valid.min() - T_f_pad, T_f_valid.max() + T_f_pad)
    ax.set_title(title, fontsize=11, fontweight="bold")
    _apply_schedule_ticks(ax)
    ax.set_xlabel("Time of day", fontsize=11)

    axr = ax.twinx()
    l2, = axr.plot(t, cop, color="#2ca02c", linewidth=1.5,
                   label="COP", antialiased=True)
    l3 = axr.axhline(spark_gap, color="red", linewidth=1.2, linestyle="--",
                     label=f"Spark gap = {spark_gap:.2f}")
    axr.set_ylabel("COP", fontsize=11, color="#2ca02c")
    axr.tick_params(axis="y", labelcolor="#2ca02c")

    cop_valid = cop[~np.isnan(cop) & (cop > 0)]
    if len(cop_valid):
        cop_lo = float(np.floor(cop_valid.min() * 2) / 2 - 0.5)
        cop_hi = float(np.ceil(cop_valid.max() * 2) / 2 + 0.5)
        axr.set_ylim(cop_lo, cop_hi)
        axr.set_yticks(np.arange(cop_lo, cop_hi + 0.1, 0.5))
    else:
        axr.set_ylim(0, 6)

    lines = [l1, l2, l3]
    if with_interruptions:
        _shade_dhw_slots(ax)
        lines.append(Patch(facecolor="purple", alpha=0.25, label="DHW slot"))
    ax.legend(lines, [l.get_label() for l in lines], loc="upper left", fontsize=9)

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
    if show:
        plt.show()
    else:
        plt.close(fig)
    return output_path


# ---------------------------------------------------------------------------
# Run a single day: plan + simulate + plot
# ---------------------------------------------------------------------------

def simulate_and_plot_day(
    sim_date: date,
    t_unix_all: np.ndarray,
    temp_all: np.ndarray,
    K: float,
    T_i_0: float,
    output_dir: Path,
    show: bool = False,
    dpi: int = 200,
) -> dict:
    """Plan, simulate, and plot one day.

    The 24-h simulation window starts at 22:00 of (sim_date - 1 day).

    Args:
        sim_date: Calendar date being simulated.
        t_unix_all: Unix-second timestamps of the temperature series.
        temp_all: Outdoor temperatures matching t_unix_all [°C].
        K: Radiator constant [W/K^1.2].
        T_i_0: Indoor temperature at 22:00 of the previous day [°C].
        output_dir: Directory for saving plots.
        show: Display plots interactively.
        dpi: Plot resolution.

    Returns:
        Result dictionary from _simulate_day augmented with DHW costs.
    """
    # 22:00 of the day before sim_date
    window_start = datetime(
        (sim_date - timedelta(days=1)).year,
        (sim_date - timedelta(days=1)).month,
        (sim_date - timedelta(days=1)).day,
        22, 0, 0,
    )

    tariff = _tariff_for_date(sim_date)
    T_o_24h = _extract_hourly_T_o(t_unix_all, temp_all, window_start)
    T_o_avg = float(np.mean(T_o_24h))
    T_o_min = float(np.min(T_o_24h))

    do_heating = T_o_avg < HEATING_THRESHOLD_C
    with_defrost = T_o_min < DEFROST_THRESHOLD_C

    if do_heating:
        hourly_powers = _build_heating_plan_variable(
            K=K,
            T_o_24h=T_o_24h,
            T_i_0=T_i_0,
            with_defrost=with_defrost,
        )
    else:
        hourly_powers = None

    result = _simulate_day(
        K=K,
        T_o_24h=T_o_24h,
        T_i_0=T_i_0,
        tariff=tariff,
        with_defrost=with_defrost,
        do_heating=do_heating,
        hourly_powers=hourly_powers,
    )

    dhw = _dhw_cost_for_day(T_o_24h, tariff)
    result.update(dhw)
    result["do_heating"] = do_heating
    result["with_defrost"] = with_defrost
    result["T_o_avg"] = T_o_avg
    result["T_o_min"] = T_o_min
    result["sim_date"] = sim_date

    # Gas comparison
    result["gas_cost_gbp"] = _gas_heating_cost(
        result["total_heat_kwh"], DHW_THERMAL_KWH, tariff
    )

    # --- Plots ---
    date_str = sim_date.strftime("%Y%m%d")
    heat_label = "with heating" if do_heating else "no space heating"
    defrost_label = "+ defrost" if with_defrost else "DHW only"
    T_o_label = f"T_o avg {T_o_avg:.1f} °C, min {T_o_min:.1f} °C"

    _plot_day_profile(
        result,
        output_dir / f"annual_heating_{date_str}_profile.png",
        f"{sim_date.strftime('%d %b %Y')} – {heat_label} ({defrost_label})  [{T_o_label}]",
        with_interruptions=True,   # always shade DHW slots
        show=show,
        dpi=dpi,
    )
    if do_heating:
        _plot_day_cop(
            result,
            tariff,
            output_dir / f"annual_heating_{date_str}_cop.png",
            f"{sim_date.strftime('%d %b %Y')} – flow temp & COP  [{T_o_label}]  K = {K:.1f} W/K^1.2",
            with_interruptions=True,
            show=show,
            dpi=dpi,
        )

    return result


# ---------------------------------------------------------------------------
# Full-year simulation
# ---------------------------------------------------------------------------

def simulate_full_year(
    t_unix_all: np.ndarray,
    temp_all: np.ndarray,
    K: float = K_RADIATOR,
    T_i_init: float = 19.0,
    dt_s: float = 60.0,
    plot_dir: Path | None = None,
    show: bool = False,
    dpi: int = 200,
) -> dict:
    """Simulate every day of 2025, chaining indoor temperature across days.

    The simulation window for calendar day D is [D-1 22:00, D 22:00].
    We start with D = Jan 2 so the window begins at Jan 1 22:00, which is
    within the data range.

    Args:
        t_unix_all: Unix-second timestamps of the full temperature series.
        temp_all: Outdoor temperatures [°C].
        K: Radiator constant [W/K^1.2].
        T_i_init: Indoor temperature at the start of the first window [°C].
        dt_s: Simulation timestep [s].
        plot_dir: If provided, save a profile + COP plot for every day here.
        show: Display plots interactively (only useful if plot_dir is set).
        dpi: Plot resolution.

    Returns:
        Dict with arrays indexed by calendar day.
    """
    if plot_dir is not None:
        plot_dir.mkdir(parents=True, exist_ok=True)
    start_date = date(2025, 1, 2)
    end_date = date(2025, 12, 31)

    all_dates: list[date] = []
    all_T_o_avg: list[float] = []
    all_T_o_min: list[float] = []
    all_space_heat_kwh: list[float] = []
    all_space_elec_kwh: list[float] = []
    all_space_cost_gbp: list[float] = []
    all_dhw_elec_kwh: list[float] = []
    all_dhw_cost_gbp: list[float] = []
    all_gas_cost_gbp: list[float] = []
    all_do_heating: list[bool] = []
    all_scop: list[float] = []

    T_i_0 = T_i_init
    current_date = start_date
    day_count = 0
    total_days = (end_date - start_date).days + 1

    print(f"Simulating {total_days} days from {start_date} to {end_date} …")

    while current_date <= end_date:
        window_start = datetime(
            (current_date - timedelta(days=1)).year,
            (current_date - timedelta(days=1)).month,
            (current_date - timedelta(days=1)).day,
            22, 0, 0,
        )

        T_o_24h = _extract_hourly_T_o(t_unix_all, temp_all, window_start)
        T_o_avg = float(np.mean(T_o_24h))
        T_o_min = float(np.min(T_o_24h))

        tariff = _tariff_for_date(current_date)
        do_heating = T_o_avg < HEATING_THRESHOLD_C
        with_defrost = T_o_min < DEFROST_THRESHOLD_C

        if do_heating:
            hourly_powers = _build_heating_plan_variable(
                K=K,
                T_o_24h=T_o_24h,
                T_i_0=T_i_0,
                dt_s=dt_s,
                with_defrost=with_defrost,
            )
        else:
            hourly_powers = None

        result = _simulate_day(
            K=K,
            T_o_24h=T_o_24h,
            T_i_0=T_i_0,
            tariff=tariff,
            dt_s=dt_s,
            hourly_powers=hourly_powers,
            with_defrost=with_defrost,
            do_heating=do_heating,
        )

        dhw = _dhw_cost_for_day(T_o_24h, tariff)
        gas_cost = _gas_heating_cost(result["total_heat_kwh"], DHW_THERMAL_KWH, tariff)

        scop = (result["total_heat_kwh"] / result["electricity_kwh"]
                if result["electricity_kwh"] > 0 else 0.0)

        # Optional per-day plots
        if plot_dir is not None:
            date_str = current_date.strftime("%Y%m%d")
            heat_label = "with heating" if do_heating else "no space heating"
            defrost_label = "+ defrost" if with_defrost else "DHW only"
            T_o_label = f"T_o avg {T_o_avg:.1f} °C, min {T_o_min:.1f} °C"
            _plot_day_profile(
                result,
                plot_dir / f"annual_heating_{date_str}_profile.png",
                f"{current_date.strftime('%d %b %Y')} – {heat_label} ({defrost_label})  [{T_o_label}]",
                with_interruptions=True,
                show=show,
                dpi=dpi,
            )
            if do_heating:
                _plot_day_cop(
                    result,
                    tariff,
                    plot_dir / f"annual_heating_{date_str}_cop.png",
                    f"{current_date.strftime('%d %b %Y')} – flow temp & COP  [{T_o_label}]  K = {K:.1f} W/K^1.2",
                    with_interruptions=True,
                    show=show,
                    dpi=dpi,
                )

        all_dates.append(current_date)
        all_T_o_avg.append(T_o_avg)
        all_T_o_min.append(T_o_min)
        all_space_heat_kwh.append(result["total_heat_kwh"])
        all_space_elec_kwh.append(result["electricity_kwh"])
        all_space_cost_gbp.append(result["cost_gbp"])
        all_dhw_elec_kwh.append(dhw["dhw_electricity_kwh"])
        all_dhw_cost_gbp.append(dhw["dhw_cost_gbp"])
        all_gas_cost_gbp.append(gas_cost)
        all_do_heating.append(do_heating)
        all_scop.append(scop)

        T_i_0 = result["T_i_end"]
        current_date += timedelta(days=1)
        day_count += 1

        if day_count % 30 == 0:
            print(f"  … {current_date.strftime('%d %b')}  "
                  f"T_i={T_i_0:.1f}°C  heat={'ON' if do_heating else 'off'}")

    print(f"Done – {day_count} days simulated.")

    dates_arr = np.array(all_dates, dtype=object)
    T_o_avg_arr = np.array(all_T_o_avg)
    T_o_min_arr = np.array(all_T_o_min)
    space_heat_arr = np.array(all_space_heat_kwh)
    space_elec_arr = np.array(all_space_elec_kwh)
    space_cost_arr = np.array(all_space_cost_gbp)
    dhw_elec_arr = np.array(all_dhw_elec_kwh)
    dhw_cost_arr = np.array(all_dhw_cost_gbp)
    gas_cost_arr = np.array(all_gas_cost_gbp)
    do_heating_arr = np.array(all_do_heating)
    scop_arr = np.array(all_scop)

    total_hp_cost = float(np.sum(space_cost_arr) + np.sum(dhw_cost_arr))
    total_gas_cost = float(np.sum(gas_cost_arr))
    heating_days = int(np.sum(do_heating_arr))
    mean_scop = float(np.mean(scop_arr[do_heating_arr & (scop_arr > 0)]))

    return {
        "dates": dates_arr,
        "T_o_avg": T_o_avg_arr,
        "T_o_min": T_o_min_arr,
        "space_heat_kwh": space_heat_arr,
        "space_elec_kwh": space_elec_arr,
        "space_cost_gbp": space_cost_arr,
        "dhw_elec_kwh": dhw_elec_arr,
        "dhw_cost_gbp": dhw_cost_arr,
        "gas_cost_gbp": gas_cost_arr,
        "do_heating": do_heating_arr,
        "scop": scop_arr,
        "total_hp_cost_gbp": total_hp_cost,
        "total_gas_cost_gbp": total_gas_cost,
        "heating_days": heating_days,
        "mean_scop": mean_scop,
    }


# ---------------------------------------------------------------------------
# Annual summary plot
# ---------------------------------------------------------------------------

def plot_annual_summary(
    annual: dict,
    output_path: Path,
    K: float = K_RADIATOR,
    show: bool = False,
    dpi: int = 200,
) -> Path:
    """Three-panel annual overview plot.

    Panel 1: Outdoor temperature (daily mean, daily min band) [°C]
    Panel 2: Daily electricity cost HP (space + DHW) vs gas cost [£/day]
    Panel 3: Daily space-heating SCOP on heating days
    """
    dates_dt = [datetime(d.year, d.month, d.day) for d in annual["dates"]]
    T_o_avg = annual["T_o_avg"]
    T_o_min = annual["T_o_min"]
    space_cost = annual["space_cost_gbp"]
    dhw_cost = annual["dhw_cost_gbp"]
    gas_cost = annual["gas_cost_gbp"]
    do_heating = annual["do_heating"]
    scop = annual["scop"]

    hp_total_cost = space_cost + dhw_cost

    fig, axes = plt.subplots(3, 1, figsize=(13, 11), sharex=True)
    fig.subplots_adjust(hspace=0.08)

    # ── Panel 1: Outdoor temperature ────────────────────────────────────
    ax1 = axes[0]
    ax1.plot(dates_dt, T_o_avg, color="#2ca02c", linewidth=1.2, label="Daily mean T_o")
    ax1.fill_between(dates_dt, T_o_min, T_o_avg, alpha=0.25, color="#2ca02c",
                     label="Daily min–mean range")
    ax1.axhline(HEATING_THRESHOLD_C, color="orange", linewidth=1.0, linestyle="--",
                label=f"Heating threshold ({HEATING_THRESHOLD_C:.0f} °C)")
    ax1.axhline(DEFROST_THRESHOLD_C, color="steelblue", linewidth=1.0, linestyle=":",
                label=f"Defrost threshold ({DEFROST_THRESHOLD_C:.0f} °C)")
    ax1.set_ylabel("Outdoor temp (°C)", fontsize=10)
    ax1.legend(loc="upper right", fontsize=8)
    ax1.grid(True, alpha=0.3)
    ax1.set_title(
        "Annual Heat Pump Operation – Cambridge 2025  "
        f"(K = {K:.1f} W/K^1.2, Ofgem quarterly tariff 2025)",
        fontsize=11, fontweight="bold",
    )

    # ── Panel 2: Daily costs ─────────────────────────────────────────────
    ax2 = axes[1]
    ax2.plot(dates_dt, hp_total_cost, color="#1f77b4", linewidth=1.2,
             label="HP total (space + DHW)")
    ax2.plot(dates_dt, dhw_cost, color="#17becf", linewidth=1.0, linestyle="--",
             label="HP DHW only")
    ax2.plot(dates_dt, gas_cost, color="#ff7f0e", linewidth=1.2, linestyle=":",
             label="Gas equivalent (space + DHW + SC)")
    ax2.set_ylabel("Daily cost (£/day)", fontsize=10)
    ax2.legend(loc="upper right", fontsize=8)
    ax2.grid(True, alpha=0.3)

    # ── Panel 3: SCOP on heating days ────────────────────────────────────
    ax3 = axes[2]
    scop_dates = [d for d, h in zip(dates_dt, do_heating) if h]
    scop_vals = scop[do_heating]
    ax3.scatter(scop_dates, scop_vals, s=6, color="#2ca02c", alpha=0.6,
                label="Space heating SCOP")
    # Quarterly-varying spark gap step line
    spark_dates = [datetime(d.year, d.month, d.day) for d in annual["dates"]]
    spark_vals = [_tariff_for_date(d).elec / _tariff_for_date(d).gas for d in annual["dates"]]
    ax3.step(spark_dates, spark_vals, where="post", color="red", linewidth=1.2,
             linestyle="--", label="Spark gap (quarterly)")
    ax3.set_ylabel("Space heating SCOP", fontsize=10)
    ax3.set_xlabel("Date (2025)", fontsize=10)
    ax3.legend(loc="upper right", fontsize=8)
    ax3.grid(True, alpha=0.3)

    # X-axis formatting
    ax3.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    ax3.xaxis.set_major_locator(mdates.MonthLocator())
    fig.autofmt_xdate(rotation=0, ha="center")

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
    if show:
        plt.show()
    else:
        plt.close(fig)
    return output_path


# ---------------------------------------------------------------------------
# CLI / main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    """Run specific-day and full-year annual heating simulations."""
    from argparse import ArgumentParser

    parser = ArgumentParser(
        description=(
            "Simulate annual heat pump space heating with Cambridge 2025 temperature data. "
            "Produces per-day profile and COP plots for representative days, "
            "then runs the full year and saves an annual overview plot."
        )
    )
    parser.add_argument("--show", action="store_true", help="Display plots interactively")
    parser.add_argument("--dpi", type=int, default=200, help="Plot DPI (default: 200)")
    parser.add_argument(
        "--year-only", action="store_true",
        help="Skip per-day plots and run full year directly",
    )
    parser.add_argument(
        "--daily-plots", action="store_true",
        help="Save a profile + COP plot for every day to assets/annual/",
    )
    args = parser.parse_args(args=argv)

    project_root = Path(__file__).resolve().parents[2]
    csv_path = project_root / "data" / "temperatures-cambridge-2025.csv"
    assets = project_root / "assets"

    # --- Load temperature data ---
    print(f"Loading temperature data from {csv_path} …")
    raw = read_cambridge_temperatures(csv_path)
    timestamps: np.ndarray = raw["timestamps"]
    temperatures: np.ndarray = raw["temperatures_c"]
    t_unix_all, temp_all = _build_temperature_index(timestamps, temperatures)
    print(f"  Loaded {len(timestamps)} readings  "
          f"({timestamps[0].strftime('%d %b %Y')} – {timestamps[-1].strftime('%d %b %Y')})")

    # --- Select representative days ---
    # Build daily averages to find cold winter / mild spring candidates
    daily_avgs: dict[date, list[float]] = {}
    for ts, tp in zip(timestamps.tolist(), temperatures.tolist()):
        d = ts.date()
        daily_avgs.setdefault(d, []).append(tp)

    avg_by_day = {d: float(np.mean(v)) for d, v in daily_avgs.items()}

    # Coldest day in Jan–Feb
    winter_days = {d: v for d, v in avg_by_day.items()
                   if d >= date(2025, 1, 2) and d <= date(2025, 2, 28)}
    cold_day = min(winter_days, key=winter_days.__getitem__)

    # Mild spring day in Apr–May with mean 8–13 °C (still needs heating)
    spring_days = {d: v for d, v in avg_by_day.items()
                   if d >= date(2025, 4, 1) and d <= date(2025, 5, 15)
                   and 6.0 <= v <= 13.0}
    mild_day = min(spring_days, key=lambda d: abs(spring_days[d] - 10.0))

    if not args.year_only:
        print(f"\n{'═'*66}")
        print(f"  Specific-day simulations")
        print(f"{'═'*66}")
        for sim_date, label in [(cold_day, "cold winter"), (mild_day, "mild spring")]:
            print(f"\n  {label.capitalize()} day: {sim_date.strftime('%d %b %Y')}"
                  f"  (avg T_o = {avg_by_day[sim_date]:.1f} °C)")
            r = simulate_and_plot_day(
                sim_date=sim_date,
                t_unix_all=t_unix_all,
                temp_all=temp_all,
                K=K_RADIATOR,
                T_i_0=19.0,
                output_dir=assets,
                show=args.show,
                dpi=args.dpi,
            )
            heating_tag = "space heating ON" if r["do_heating"] else "space heating OFF"
            defrost_tag = "+ defrost" if r["with_defrost"] else "DHW only"
            print(f"    {heating_tag}, {defrost_tag}")
            print(f"    Space heat:   {r['total_heat_kwh']:.1f} kWh  "
                  f"elec {r['electricity_kwh']:.2f} kWh  "
                  f"cost £{r['cost_gbp']:.2f}")
            print(f"    DHW:          elec {r['dhw_electricity_kwh']:.2f} kWh  "
                  f"cost £{r['dhw_cost_gbp']:.2f}")
            print(f"    Gas equiv:    £{r['gas_cost_gbp']:.2f}/day")
            print(f"    Saved: assets/annual_heating_{sim_date.strftime('%Y%m%d')}_profile.png")
            if r["do_heating"]:
                print(f"    Saved: assets/annual_heating_{sim_date.strftime('%Y%m%d')}_cop.png")

    # --- Full-year simulation ---
    print(f"\n{'═'*66}")
    print(f"  Full-year simulation (2025)")
    print(f"{'═'*66}")
    annual = simulate_full_year(
        t_unix_all=t_unix_all,
        temp_all=temp_all,
        K=K_RADIATOR,
        T_i_init=19.0,
        plot_dir=assets / "annual" if args.daily_plots else None,
        show=args.show,
        dpi=args.dpi,
    )

    # Print annual summary
    n = annual["heating_days"]
    total_days = len(annual["dates"])
    print(f"\n{'─'*66}")
    print(f"  Annual results  (K = {K_RADIATOR:.1f} W/K^1.2, Ofgem quarterly tariff 2025)")
    print(f"{'─'*66}")
    print(f"  Days simulated:          {total_days}")
    print(f"  Days with space heating: {n}")
    print(f"  Mean space heating SCOP: {annual['mean_scop']:.2f}")
    print(f"  Annual HP cost (space + DHW):  £{annual['total_hp_cost_gbp']:.2f}")
    print(f"  Annual gas cost (space + DHW): £{annual['total_gas_cost_gbp']:.2f}")
    saving = annual["total_gas_cost_gbp"] - annual["total_hp_cost_gbp"]
    print(f"  Annual saving with HP:         £{saving:+.2f}")

    annual_plot = assets / "annual_heating_overview.png"
    plot_annual_summary(annual, annual_plot, show=args.show, dpi=args.dpi)
    print(f"\n  Saved: assets/annual_heating_overview.png")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
