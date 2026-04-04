"""Read a temperature CSV and create a datetime/temperature plot."""

from __future__ import annotations

from csv import reader
from datetime import datetime
from math import exp, log
from pathlib import Path
from typing import Iterable, Sequence, Tuple

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from scipy.optimize import curve_fit


def read_temperature_csv(csv_path: Path) -> Tuple[Sequence[datetime], Sequence[float]]:
    """Read a temperature CSV file with datetime and temperature columns.

    Args:
        csv_path: Path to a CSV file containing rows like:
            2026-04-03 22:50:11,22.11

    Returns:
        Tuple of timestamps and temperature values.
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Temperature CSV file not found: {csv_path}")

    timestamps: list[datetime] = []
    temperatures: list[float] = []

    with csv_path.open(newline="", encoding="utf-8") as csvfile:
        csv_reader = reader(csvfile)
        for row_number, row in enumerate(csv_reader, start=1):
            if not row:
                continue
            if len(row) < 2:
                raise ValueError(
                    f"Expected at least 2 columns on line {row_number}, got {len(row)}"
                )

            timestamp_str = row[0].strip()
            temperature_str = row[1].strip()

            try:
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            except ValueError as exc:
                raise ValueError(
                    f"Invalid datetime format on line {row_number}: '{timestamp_str}'"
                ) from exc

            try:
                temperature = float(temperature_str)
            except ValueError as exc:
                raise ValueError(
                    f"Invalid temperature value on line {row_number}: '{temperature_str}'"
                ) from exc

            timestamps.append(timestamp)
            temperatures.append(temperature)

    return timestamps, temperatures


def plot_temperatures(
    timestamps: Sequence[datetime],
    temperatures: Sequence[float],
    predicted_temperatures: Sequence[float] | None = None,
    smooth_temperatures: Sequence[float] | None = None,
    title: str = "Temperature over Time",
    xlabel: str = "Time",
    ylabel: str = "Temperature (°C)",
    figsize: Tuple[int, int] = (12, 6),
    predicted_label: str = "Model prediction",
    smooth_label: str = "Smoothed indoor temperature",
) -> plt.Figure:
    """Create a matplotlib plot of temperature over time."""
    if len(timestamps) != len(temperatures):
        raise ValueError("Timestamps and temperatures must have the same length.")
    if predicted_temperatures is not None and len(predicted_temperatures) != len(timestamps):
        raise ValueError("Predicted temperatures must have the same length as timestamps.")
    if smooth_temperatures is not None and len(smooth_temperatures) != len(timestamps):
        raise ValueError("Smoothed temperatures must have the same length as timestamps.")

    fig, ax = plt.subplots(figsize=figsize)
    ax.plot(timestamps, temperatures, marker="o", linestyle="-", color="#1f77b4", label="Measured indoor temperature")
    if smooth_temperatures is not None:
        ax.plot(
            timestamps,
            smooth_temperatures,
            linestyle="-",
            color="#2ca02c",
            label=smooth_label,
            alpha=0.8,
            linewidth=2,
        )
    if predicted_temperatures is not None:
        ax.plot(
            timestamps,
            predicted_temperatures,
            linestyle="--",
            color="#ff7f0e",
            label=predicted_label,
            alpha=0.8,
            linewidth=4,
        )

    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    fig.autofmt_xdate()
    return fig


def smooth_series(values: Sequence[float], window: int = 11) -> list[float]:
    """Smooth a sequence using a centered moving average."""
    if window <= 1 or len(values) < window:
        return list(values)

    half = window // 2
    padded = [values[0]] * half + list(values) + [values[-1]] * half
    smoothed: list[float] = []
    for i in range(half, half + len(values)):
        window_values = padded[i - half : i + half + 1]
        smoothed.append(sum(window_values) / len(window_values))
    return smoothed


def estimate_thermal_capacity(
    timestamps: Sequence[datetime],
    temperatures: Sequence[float],
    h: float,
    T_o: float,
    smooth_window: int = 1,
) -> tuple[float, float, float]:
    """Estimate the thermal capacity C and amplitude A from temperature time series.

    Fit the decay model: T_i(t) = A * exp(-t / tau) + T0
    where tau = C / h, and T0 = T_o (constrained to actual outdoor temperature).
    
    CRITICAL FIX: T0 is NOT fitted. It is FIXED to the true outdoor temperature T_o.
    This prevents the fitter from "cheating" by making T0 float to intermediate values
    when only observing the early part of the decay curve.
    """
    if len(timestamps) < 3:
        raise ValueError("At least three temperature samples are required for curve fitting.")

    if smooth_window > 1:
        temperatures = smooth_series(temperatures, window=smooth_window)

    t_seconds = np.array([(ts - timestamps[0]).total_seconds() for ts in timestamps], dtype=float)
    temp_data = np.array(temperatures, dtype=float)

    # Fit only A and tau; keep T0 fixed at the true outdoor temperature
    def decay_fixed_asymptote(t, A, tau):
        return A * np.exp(-t / tau) + T_o

    # Initial guesses
    A_guess = temp_data[0] - T_o  # Initial excess above outdoor temp
    tau_guess = 3600.0  # Conservative guess: 1 hour (will likely be much larger)

    try:
        popt, pcov = curve_fit(decay_fixed_asymptote, t_seconds, temp_data, p0=[A_guess, tau_guess])
        A_fit, tau_fit = popt
    except RuntimeError as e:
        raise ValueError(f"Curve fitting failed: {e}")

    if tau_fit <= 0 or A_fit <= 0:
        raise ValueError("Fitted parameters are not physically meaningful.")

    T0_fit = T_o  # Fixed boundary condition (not fitted)
    C = h * tau_fit
    return C, A_fit, T0_fit


def predict_temperatures(
    timestamps: Sequence[datetime],
    A: float,
    C: float,
    h: float,
    T_o: float,
) -> list[float]:
    """Predict indoor temperature using the first-order model and estimated C."""
    if A <= 0:
        return [T_o for _ in timestamps]

    initial_time = timestamps[0]
    return [
        T_o + A * exp(-(h / C) * (ts - initial_time).total_seconds())
        for ts in timestamps
    ]


def compute_rmse(predictions: Sequence[float], targets: Sequence[float]) -> float:
    if len(predictions) != len(targets):
        raise ValueError("Predictions and targets must have the same length.")
    return float(np.sqrt(np.mean((np.array(predictions) - np.array(targets)) ** 2)))


def create_temperature_plot(
    csv_path: Path | str = "data/temperatures-1.csv",
    output_path: Path | str = "assets/temperature_plot.png",
    start: datetime | None = None,
    end: datetime | None = None,
    h: float = 244.0,
    T_o: float = 7.0,
    estimate_c: bool = False,
    smooth_window: int = 11,
    show: bool = False,
    dpi: int = 200,
) -> Path:
    """Read the CSV file and create/save the temperature plot."""
    project_root = Path(__file__).resolve().parents[2]
    csv_path = Path(csv_path)
    output_path = Path(output_path)

    if not csv_path.is_absolute():
        csv_path = project_root / csv_path

    if not output_path.is_absolute():
        output_path = project_root / output_path

    timestamps, temperatures = read_temperature_csv(csv_path)

    if start is not None or end is not None:
        filtered = [
            (ts, temp)
            for ts, temp in zip(timestamps, temperatures)
            if (start is None or ts >= start) and (end is None or ts <= end)
        ]
        if not filtered:
            raise ValueError(
                f"No temperature records found between {start!r} and {end!r}."
            )
        timestamps, temperatures = map(list, zip(*filtered))

    predicted = None
    smooth_temperatures = None
    if estimate_c:
        C, A, T0 = estimate_thermal_capacity(timestamps, temperatures, h, T_o, smooth_window=smooth_window)
        tau = C / h
        predicted = predict_temperatures(timestamps, A, C, h, T0)
        rmse = compute_rmse(predicted, temperatures)
        print(f"Estimated time constant τ = {tau:.1f} s ({tau / 3600:.3f} h)")
        print(f"Estimated thermal capacity C = {C:.0f} J/K")
        print(f"Estimated amplitude A = {A:.3f} °C")
        print(f"Fitted baseline T0 = {T0:.3f} °C")
        print(f"Residual RMSE = {rmse:.4f} °C")
        print(f"Using h = {h} W/K and outdoor temperature T_o = {T_o} °C")

    fig = plot_temperatures(
        timestamps,
        temperatures,
        predicted_temperatures=predicted,
        smooth_temperatures=smooth_temperatures,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")

    if show:
        plt.show()
    else:
        plt.close(fig)

    return output_path


def main(argv: Iterable[str] | None = None) -> int:
    """Run the temperature plot creation script."""
    from argparse import ArgumentParser

    parser = ArgumentParser(
        description="Read temperature data from a CSV and create a time-series plot."
    )
    parser.add_argument(
        "--csv",
        default="data/temperatures-1.csv",
        help="Path to the temperature CSV file (default: data/temperatures-1.csv)",
    )
    parser.add_argument(
        "--output",
        default="assets/temperature_plot.png",
        help="Path to save the generated plot (default: assets/temperature_plot.png)",
    )
    parser.add_argument(
        "--start",
        default=None,
        help="Start datetime to include in the plot, in YYYY-MM-DD HH:MM:SS format.",
    )
    parser.add_argument(
        "--end",
        default=None,
        help="End datetime to include in the plot, in YYYY-MM-DD HH:MM:SS format.",
    )
    parser.add_argument(
        "--h",
        type=float,
        default=244.0,
        help="Heat transfer coefficient h in W/K (default: 244)",
    )
    parser.add_argument(
        "--smooth-window",
        type=int,
        default=11,
        help="Moving average window size for smoothing before exponential fitting (odd integer, default 11).",
    )
    parser.add_argument(
        "--outdoor-temp",
        type=float,
        default=7.0,
        help="Outdoor temperature T_o in °C (default: 7)",
    )
    parser.add_argument(
        "--estimate-c",
        action="store_true",
        help="Estimate thermal capacity C and overlay the model prediction.",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Display the plot interactively after saving it.",
    )
    args = parser.parse_args(args=list(argv) if argv is not None else None)

    start_dt = None
    end_dt = None
    if args.start is not None:
        start_dt = datetime.strptime(args.start, "%Y-%m-%d %H:%M:%S")
    if args.end is not None:
        end_dt = datetime.strptime(args.end, "%Y-%m-%d %H:%M:%S")
    if start_dt is not None and end_dt is not None and start_dt > end_dt:
        raise ValueError("Start datetime must be before or equal to end datetime.")

    output_path = create_temperature_plot(
        csv_path=args.csv,
        output_path=args.output,
        start=start_dt,
        end=end_dt,
        h=args.h,
        T_o=args.outdoor_temp,
        estimate_c=args.estimate_c,
        smooth_window=args.smooth_window,
        show=args.show,
    )

    print(f"Saved temperature plot to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
