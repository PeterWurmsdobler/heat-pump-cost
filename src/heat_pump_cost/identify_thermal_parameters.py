"""Thermal parameter identification for the dynamic house model.

Fits the first-order model:

    C * dT_i/dt = -h * (T_i - T_o(t)) + Q_b + Q_r

to temperature data recorded in three experimental conditions, yielding
estimates of the thermal capacity C, the heat transfer coefficient (HTC) h,
and the background heat source Q_b.

The three conditions used are:

    Period 1 – temperatures-1, 01:00–06:00 Apr 4  : T_o=7°C, heating off (Q_r=0)
    Period 2 – temperatures-2, 22:45 Apr5–04:20 Apr6: T_o=3°C, heating off (Q_r=0)
    Period 3 – temperatures-2, 06:30–08:15 Apr 6   : T_o ramps 3→7°C, heating on (Q_r~6 kW)

Periods 1 and 2 are passive cooling experiments; the exponential decay shape
constrains the time constant τ = C/h and the asymptote constrains Q_b.
Period 3 is a forced-heating experiment that validates the estimated C.

Estimation is performed via MAP (maximum a posteriori): minimise the sum of
mean squared residuals across all three periods, plus soft Gaussian priors on
h and Q_b.  Optimisation uses multi-start L-BFGS-B with log(C) as the
decision variable so C remains positive across all scales.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable, Sequence

import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import minimize

from heat_pump_cost.plot_temperatures import read_temperature_csv

# ---------------------------------------------------------------------------
# Default segment configuration
# ---------------------------------------------------------------------------

#: Path to the first temperature CSV  (Apr 4 cooling period).
CSV_1 = Path("data/temperatures-1.csv")

#: Path to the second temperature CSV (Apr 5–6 cooling + heating periods).
CSV_2 = Path("data/temperatures-2.csv")

#: Three experimental periods: (csv, start, end, label, T_o_spec, Q_r_W)
#: T_o_spec is either a float (constant) or a tuple (T_start, T_end) where
#: T_o ramps linearly from T_start to T_end over the duration of the segment.
DEFAULT_SEGMENTS_SPEC = [
    (
        CSV_1,
        datetime(2026, 4, 4, 1, 0, 0),
        datetime(2026, 4, 4, 6, 0, 0),
        "Period 1 – Cooling (T_o=7°C)",
        7.0,          # constant outdoor temperature [°C]
        0.0,          # Q_r: heating off [W]
    ),
    (
        CSV_2,
        datetime(2026, 4, 5, 22, 45, 0),
        datetime(2026, 4, 6, 4, 20, 0),
        "Period 2 – Cooling (T_o=3°C)",
        3.0,          # constant outdoor temperature [°C]
        0.0,          # Q_r: heating off [W]
    ),
    (
        CSV_2,
        datetime(2026, 4, 6, 6, 30, 0),
        datetime(2026, 4, 6, 8, 15, 0),
        "Period 3 – Heating on (T_o 3→7°C)",
        (3.0, 7.0),   # T_o ramps linearly from 3°C to 7°C
        4000.0,       # Q_r: full heating power [W]
    ),
]

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class ExperimentSegment:
    """One experimental time window with known external conditions.

    Attributes:
        name: Short label used in plot titles.
        timestamps: Sequence of datetime objects, one per measurement.
        temperatures: Measured indoor temperatures [°C].
        T_o: Outdoor temperature – either a scalar constant [°C] or a
            callable ``T_o(t_seconds: float) -> float`` where ``t_seconds`` is
            elapsed time since ``timestamps[0]``.
        Q_r: Radiator heat input for this segment [W].
    """

    name: str
    timestamps: list[datetime]
    temperatures: list[float]
    T_o: float | Callable[[float], float]
    Q_r: float


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------


def _linear_T_o(T_start: float, T_end: float, duration_s: float) -> Callable[[float], float]:
    """Return a callable that linearly ramps T_o from *T_start* to *T_end*.

    Args:
        T_start: Outdoor temperature at t=0 [°C].
        T_end: Outdoor temperature at t=duration_s [°C].
        duration_s: Total duration of the ramp [s].

    Returns:
        Callable ``T_o(t_seconds) -> float`` clamped to [T_start, T_end].
    """
    def _ramp(t: float) -> float:
        fraction = min(max(t / duration_s, 0.0), 1.0)
        return T_start + (T_end - T_start) * fraction

    return _ramp


def load_segment(
    csv_path: Path,
    start: datetime,
    end: datetime,
    name: str,
    T_o: float | Callable[[float], float],
    Q_r: float,
) -> ExperimentSegment:
    """Load a time window from a CSV file into an ExperimentSegment.

    Args:
        csv_path: Path to a temperature CSV (datetime, temperature columns).
        start: Inclusive start datetime.
        end: Inclusive end datetime.
        name: Descriptive label for this segment.
        T_o: Outdoor temperature – constant float or callable.
        Q_r: Radiator power during this segment [W].

    Raises:
        ValueError: If no data points fall within [start, end].
    """
    timestamps_all, temperatures_all = read_temperature_csv(csv_path)
    pairs = [
        (ts, T)
        for ts, T in zip(timestamps_all, temperatures_all)
        if start <= ts <= end
    ]
    if not pairs:
        raise ValueError(
            f"No data found between {start} and {end} in {csv_path}"
        )
    timestamps, temperatures = map(list, zip(*pairs))
    return ExperimentSegment(
        name=name,
        timestamps=timestamps,
        temperatures=temperatures,
        T_o=T_o,
        Q_r=Q_r,
    )


def load_default_segments(project_root: Path) -> list[ExperimentSegment]:
    """Build the three default ExperimentSegments from the standard CSV files.

    Args:
        project_root: Absolute path to the repository root.

    Returns:
        Three ExperimentSegment objects, one per experimental period.
    """
    segments: list[ExperimentSegment] = []
    for csv_rel, start, end, label, T_o_spec, Q_r_W in DEFAULT_SEGMENTS_SPEC:
        csv_path = project_root / csv_rel

        if isinstance(T_o_spec, tuple):
            T_start, T_end = T_o_spec
            duration_s = (end - start).total_seconds()
            T_o: float | Callable[[float], float] = _linear_T_o(T_start, T_end, duration_s)
        else:
            T_o = float(T_o_spec)

        segments.append(load_segment(csv_path, start, end, label, T_o, Q_r_W))

    return segments


# ---------------------------------------------------------------------------
# ODE simulation
# ---------------------------------------------------------------------------


def simulate_segment(
    segment: ExperimentSegment,
    C: float,
    h: float,
    Q_b: float,
) -> list[float]:
    """Integrate the thermal ODE for one segment.

    Solves ``C * dT_i/dt = -h*(T_i - T_o(t)) + Q_b + Q_r`` from the
    measured initial temperature and returns predicted T_i at each sample
    timestamp.

    Args:
        segment: Experimental segment with timestamps, temperatures and inputs.
        C: Thermal capacity [J/K].
        h: Heat transfer coefficient [W/K].
        Q_b: Background heat source [W].

    Returns:
        List of predicted indoor temperatures aligned with segment.timestamps.
    """
    t_meas = np.array(
        [(ts - segment.timestamps[0]).total_seconds() for ts in segment.timestamps],
        dtype=float,
    )
    T0 = float(segment.temperatures[0])
    Q_r = segment.Q_r

    if callable(segment.T_o):
        T_o_func: Callable[[float], float] = segment.T_o
    else:
        _T_o_const = float(segment.T_o)

        def T_o_func(t: float) -> float:  # noqa: F811 – intentional rebind
            return _T_o_const

    def rhs(_t: float, Ti: list[float]) -> list[float]:
        return [(-h * (Ti[0] - T_o_func(_t)) + Q_b + Q_r) / C]

    sol = solve_ivp(
        rhs,
        t_span=(0.0, float(t_meas[-1])),
        y0=[T0],
        t_eval=t_meas,
        method="RK45",
        rtol=1e-6,
        atol=1e-8,
        max_step=30.0,
    )
    if not sol.success:
        return [float("nan")] * len(t_meas)
    return sol.y[0].tolist()


# ---------------------------------------------------------------------------
# Parameter estimation
# ---------------------------------------------------------------------------


def _objective(
    params: Sequence[float],
    segments: Sequence[ExperimentSegment],
    h_prior: float,
    h_sigma: float,
    Q_b_prior: float,
    Q_b_sigma: float,
) -> float:
    """Negative log-posterior: sum of per-segment MSE plus Gaussian priors.

    Args:
        params: [log(C), h, Q_b] – log-scale C keeps the parameter positive.
        segments: Experimental segments to fit.
        h_prior: Prior mean for h [W/K].
        h_sigma: Prior standard deviation for h [W/K].
        Q_b_prior: Prior mean for Q_b [W].
        Q_b_sigma: Prior standard deviation for Q_b [W].

    Returns:
        Scalar cost (lower is better).
    """
    log_C, h, Q_b = params
    C = float(np.exp(log_C))
    if h <= 0 or Q_b < 0:
        return 1e12

    total = 0.0
    for seg in segments:
        predicted = simulate_segment(seg, C, h, Q_b)
        if any(np.isnan(p) for p in predicted):
            return 1e12
        residuals = np.array(predicted) - np.array(seg.temperatures)
        total += float(np.mean(residuals**2))

    # Soft Gaussian priors on h and Q_b
    total += ((h - h_prior) / h_sigma) ** 2
    total += ((Q_b - Q_b_prior) / Q_b_sigma) ** 2
    return total


def identify_parameters(
    segments: Sequence[ExperimentSegment],
    h_prior: float = 188.0,
    h_sigma: float = 500.0,
    Q_b_prior: float = 500.0,
    Q_b_sigma: float = 300.0,
) -> dict[str, float]:
    """Estimate C, h, and Q_b from the experimental segments.

    Performs MAP estimation: minimises the sum of mean squared residuals
    across all segments plus soft Gaussian priors on h and Q_b.  Uses
    multi-start L-BFGS-B (with log(C) as the decision variable) to find
    a robust global minimum.

    Args:
        segments: Experimental data segments.
        h_prior: Prior mean for the heat transfer coefficient [W/K].
            Default 188 (from recorded power consumption).
        h_sigma: Prior standard deviation for h [W/K].
            Default 56 (half the range 188–244 from prior analyses).
        Q_b_prior: Prior mean for background power Q_b [W].
        Q_b_sigma: Prior standard deviation for Q_b [W].

    Returns:
        Dictionary with keys:
            ``C_J``   – thermal capacity [J/K]
            ``C_MJ``  – thermal capacity [MJ/K]
            ``h``     – heat transfer coefficient [W/K]
            ``Q_b``   – background heat [W]
            ``tau_s`` – time constant C/h [s]
            ``tau_h`` – time constant C/h [h]
    """
    bounds = [
        (np.log(1e7), np.log(2e10)),  # log(C): 10 MJ/K to 20 GJ/K
        (50.0, 600.0),                 # h [W/K]
        (0.0, 3000.0),                 # Q_b [W]
    ]
    args = (segments, h_prior, h_sigma, Q_b_prior, Q_b_sigma)

    # Multiple starting points to guard against local minima
    starting_points = [
        [np.log(1e8),  h_prior,  Q_b_prior],
        [np.log(3e8),  h_prior,  Q_b_prior],
        [np.log(1e8),  244.0,    Q_b_prior],
        [np.log(3e8),  244.0,    500.0],
        [np.log(5e7),  h_prior,  300.0],
        [np.log(5e8),  200.0,    700.0],
        [np.log(1e9),  h_prior,  Q_b_prior],
    ]

    best_result = None
    best_cost = float("inf")
    for x0 in starting_points:
        result = minimize(
            _objective,
            x0,
            args=args,
            method="L-BFGS-B",
            bounds=bounds,
            options={"maxiter": 5000, "ftol": 1e-14},
        )
        if result.fun < best_cost:
            best_cost = result.fun
            best_result = result

    assert best_result is not None, "Optimisation failed – no valid result found."
    log_C, h, Q_b = best_result.x
    C = float(np.exp(log_C))
    tau = C / h
    return {
        "C_J": C,
        "C_MJ": C / 1e6,
        "h": h,
        "Q_b": Q_b,
        "tau_s": tau,
        "tau_h": tau / 3600.0,
    }


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------


def create_identification_plot(
    segments: Sequence[ExperimentSegment],
    C: float,
    h: float,
    Q_b: float,
    output_path: Path,
    show: bool = False,
    dpi: int = 200,
) -> Path:
    """Create and save a three-panel stacked plot of measured vs. predicted temperatures.

    Each panel (one per experimental segment) is stacked vertically and shows
    the measured indoor temperature in blue and the model prediction in orange
    dashed on the left y-axis, together with the per-segment RMSE.

    Args:
        segments: Experimental segments (one panel each).
        C: Estimated thermal capacity [J/K].
        h: Estimated heat transfer coefficient [W/K].
        Q_b: Estimated background heat [W].
        output_path: File path for the saved PNG.
        show: If True, call ``plt.show()`` after saving.
        dpi: Output resolution.

    Returns:
        The ``output_path`` that was written.
    """
    n = len(segments)
    fig, axes = plt.subplots(n, 1, figsize=(10, 3.5 * n), sharex=False)
    if n == 1:
        axes = [axes]

    fig.suptitle(
        f"Thermal Parameter Identification  (C = {C/1e6:.0f} MJ/K, "
        f"h = {h:.0f} W/K, Q_b = {Q_b:.0f} W)",
        fontsize=13,
        fontweight="bold",
    )

    for ax, seg in zip(axes, segments):
        t_seconds = np.array(
            [(ts - seg.timestamps[0]).total_seconds() for ts in seg.timestamps],
            dtype=float,
        )
        t_hours = t_seconds / 3600.0
        predicted = simulate_segment(seg, C, h, Q_b)
        rmse = float(
            np.sqrt(np.mean((np.array(predicted) - np.array(seg.temperatures)) ** 2))
        )

        ax.plot(t_hours, seg.temperatures, color="#1f77b4", linewidth=1.2, label="Measured T_i")
        ax.plot(
            t_hours,
            predicted,
            color="#ff7f0e",
            linewidth=2.0,
            linestyle="--",
            label=f"Model T_i  (RMSE = {rmse:.3f} °C)",
        )
        ax.set_title(seg.name, fontsize=11)
        ax.set_xlabel("Elapsed time (h)", fontsize=10)
        ax.set_ylabel("T_i (°C)", fontsize=10)
        ax.legend(fontsize=9, loc="best")
        ax.grid(True, alpha=0.3)

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
    if show:
        plt.show()
    else:
        plt.close(fig)
    return output_path


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(argv: Iterable[str] | None = None) -> int:
    """Run thermal parameter identification and save the output plot.

    Example usage::

        python -m heat_pump_cost.identify_thermal_parameters
        python -m heat_pump_cost.identify_thermal_parameters --h-prior 244 --h-sigma 30
        python -m heat_pump_cost.identify_thermal_parameters --q-r 5500 --show
    """
    from argparse import ArgumentParser

    parser = ArgumentParser(
        description=(
            "Identify thermal parameters C, h, Q_b from temperature recordings.\n"
            "Model: C * dT_i/dt = -h * (T_i - T_o) + Q_b + Q_r"
        )
    )
    parser.add_argument(
        "--output",
        default="assets/temperature_plot.png",
        help="Output path for the identification plot (default: assets/temperature_plot.png)",
    )
    parser.add_argument(
        "--h-prior",
        type=float,
        default=188.0,
        help="Prior mean for heat transfer coefficient h [W/K] (default: 188)",
    )
    parser.add_argument(
        "--h-sigma",
        type=float,
        default=500.0,
        help="Prior std for h [W/K] (default: 500, weak regularisation)",
    )
    parser.add_argument(
        "--q-b-prior",
        type=float,
        default=500.0,
        help="Prior mean for background heat Q_b [W] (default: 500)",
    )
    parser.add_argument(
        "--q-b-sigma",
        type=float,
        default=300.0,
        help="Prior std for Q_b [W] (default: 300)",
    )
    parser.add_argument(
        "--q-r",
        type=float,
        default=4000.0,
        help="Radiator power for Period 3 (full heating) [W] (default: 4000)",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Display the plot interactively after saving",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=200,
        help="Plot resolution in DPI (default: 200)",
    )
    args = parser.parse_args(args=list(argv) if argv is not None else None)

    project_root = Path(__file__).resolve().parents[2]
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = project_root / output_path

    # Load segments, overriding Q_r in Period 3 from the CLI argument
    segments = load_default_segments(project_root)
    segments[2] = ExperimentSegment(
        name=segments[2].name,
        timestamps=segments[2].timestamps,
        temperatures=segments[2].temperatures,
        T_o=segments[2].T_o,
        Q_r=args.q_r,
    )

    print("Identifying thermal parameters from three experimental periods …")
    params = identify_parameters(
        segments,
        h_prior=args.h_prior,
        h_sigma=args.h_sigma,
        Q_b_prior=args.q_b_prior,
        Q_b_sigma=args.q_b_sigma,
    )

    C_MJ = params["C_MJ"]
    h = params["h"]
    Q_b = params["Q_b"]
    tau_s = params["tau_s"]
    tau_h = params["tau_h"]

    print()
    print("─" * 55)
    print(f"  Thermal capacity     C  = {C_MJ:.1f} MJ/K")
    print(f"  Heat transfer coeff  h  = {h:.1f} W/K")
    print(f"  Background heat      Q_b = {Q_b:.0f} W  ({Q_b/1000:.3f} kW)")
    print(f"  Time constant        τ  = {tau_s:.0f} s  ({tau_h:.1f} h)")
    print("─" * 55)
    print()

    # Per-segment RMSE
    C_J = params["C_J"]
    for seg in segments:
        predicted = simulate_segment(seg, C_J, h, Q_b)
        residuals = np.array(predicted) - np.array(seg.temperatures)
        rmse = float(np.sqrt(np.mean(residuals**2)))
        print(f"  {seg.name:<45s}  RMSE = {rmse:.3f} °C")
    print()

    output_path = create_identification_plot(
        segments,
        C=C_J,
        h=h,
        Q_b=Q_b,
        output_path=output_path,
        show=args.show,
        dpi=args.dpi,
    )
    print(f"Saved identification plot to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
