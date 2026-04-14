"""Analyze annual DHW costs using Cambridge 2025 temperature data.

Calculates daily cost of heating 200L of water (split into two 100L batches
at 04:00 and 15:00) throughout the year, based on actual outdoor temperatures.
"""

from __future__ import annotations

from csv import reader
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

from heat_pump_cost.radiator_analysis import cop_estimate

# ---------------------------------------------------------------------------
# Constants from plot_dhw_cost.py
# ---------------------------------------------------------------------------

DHW_THERMAL_ENERGY_PER_BATCH_KWH = 10.5 / 2  # 5.25 kWh per 100L batch
DHW_FLOW_TEMP = 55.0  # °C

GAS_PRICE_PER_KWH = 5.93 / 100.0      # £/kWh
ELECTRICITY_PRICE_PER_KWH = 27.69 / 100.0  # £/kWh
BOILER_EFFICIENCY = 0.95

GAS_STANDING_CHARGE = 0.3509  # £/day


def read_cambridge_temperatures(csv_path: Path) -> dict:
    """Read Cambridge temperature CSV file.
    
    Format: datetime, temperature (in 1/10 °C)
    
    Args:
        csv_path: Path to temperature CSV file
        
    Returns:
        Dictionary with arrays: timestamps, temperatures_c
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Temperature CSV file not found: {csv_path}")

    timestamps: list[datetime] = []
    temperatures_c: list[float] = []

    with csv_path.open(newline="", encoding="utf-8") as csvfile:
        csv_reader = reader(csvfile)
        for row_number, row in enumerate(csv_reader, start=1):
            if not row:
                continue
            if len(row) < 2:
                continue  # Skip incomplete rows

            timestamp_str = row[0].strip()
            temp_tenths_str = row[1].strip()

            try:
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue  # Skip rows with invalid datetime

            try:
                temp_tenths = float(temp_tenths_str)
                temp_c = temp_tenths / 10.0  # Convert from 1/10°C to °C
            except ValueError:
                continue  # Skip rows with invalid temperature

            timestamps.append(timestamp)
            temperatures_c.append(temp_c)

    return {
        "timestamps": np.array(timestamps),
        "temperatures_c": np.array(temperatures_c),
    }


def calculate_dhw_batch_cost(t_outdoor: float, thermal_energy_kwh: float) -> dict:
    """Calculate cost of heating one batch of DHW.
    
    Args:
        t_outdoor: Outdoor temperature [°C]
        thermal_energy_kwh: Thermal energy required [kWh]
        
    Returns:
        Dictionary with hp_cost_gbp, gas_cost_gbp, cop
    """
    # Heat pump
    cop = cop_estimate(t_outdoor, DHW_FLOW_TEMP)
    hp_electricity_kwh = thermal_energy_kwh / cop
    hp_cost_gbp = hp_electricity_kwh * ELECTRICITY_PRICE_PER_KWH
    
    # Gas boiler
    gas_kwh = thermal_energy_kwh / BOILER_EFFICIENCY
    gas_cost_gbp = gas_kwh * GAS_PRICE_PER_KWH
    
    return {
        "hp_cost_gbp": hp_cost_gbp,
        "gas_cost_gbp": gas_cost_gbp,
        "cop": cop,
        "hp_electricity_kwh": hp_electricity_kwh,
    }


def analyze_annual_dhw_costs(csv_path: Path) -> dict:
    """Analyze annual DHW costs based on actual temperature data.
    
    Assumes two DHW batches per day:
    - 100L at 04:00 (5.25 kWh thermal)
    - 100L at 15:00 (5.25 kWh thermal)
    
    Args:
        csv_path: Path to Cambridge temperature CSV
        
    Returns:
        Dictionary with daily and annual cost data
    """
    # Read temperature data
    data = read_cambridge_temperatures(csv_path)
    timestamps = data["timestamps"]
    temperatures = data["temperatures_c"]
    
    print(f"Loaded {len(timestamps)} temperature readings")
    print(f"Date range: {timestamps[0]} to {timestamps[-1]}")
    
    # Group by date and extract morning (04:00) and afternoon (15:00) temperatures
    daily_data = {}
    
    for timestamp, temp in zip(timestamps, temperatures):
        date = timestamp.date()
        hour = timestamp.hour
        
        if date not in daily_data:
            daily_data[date] = {"morning_temp": None, "afternoon_temp": None}
        
        # Morning batch: use temperature closest to 04:00
        if hour == 4:
            daily_data[date]["morning_temp"] = temp
        # Afternoon batch: use temperature closest to 15:00
        elif hour == 15:
            daily_data[date]["afternoon_temp"] = temp
    
    # Calculate daily costs
    dates = []
    daily_hp_costs = []
    daily_gas_costs = []
    daily_avg_temps = []
    daily_avg_cops = []
    
    for date in sorted(daily_data.keys()):
        morning_temp = daily_data[date]["morning_temp"]
        afternoon_temp = daily_data[date]["afternoon_temp"]
        
        # Skip days with missing data
        if morning_temp is None or afternoon_temp is None:
            continue
        
        # Calculate cost for each batch
        morning_batch = calculate_dhw_batch_cost(morning_temp, DHW_THERMAL_ENERGY_PER_BATCH_KWH)
        afternoon_batch = calculate_dhw_batch_cost(afternoon_temp, DHW_THERMAL_ENERGY_PER_BATCH_KWH)
        
        # Daily totals
        daily_hp_cost = morning_batch["hp_cost_gbp"] + afternoon_batch["hp_cost_gbp"]
        daily_gas_cost = morning_batch["gas_cost_gbp"] + afternoon_batch["gas_cost_gbp"]
        avg_temp = (morning_temp + afternoon_temp) / 2
        avg_cop = (morning_batch["cop"] + afternoon_batch["cop"]) / 2
        
        dates.append(date)
        daily_hp_costs.append(daily_hp_cost)
        daily_gas_costs.append(daily_gas_cost)
        daily_avg_temps.append(avg_temp)
        daily_avg_cops.append(avg_cop)
    
    # Convert to arrays
    dates = np.array(dates)
    daily_hp_costs = np.array(daily_hp_costs)
    daily_gas_costs = np.array(daily_gas_costs)
    daily_avg_temps = np.array(daily_avg_temps)
    daily_avg_cops = np.array(daily_avg_cops)
    
    # Annual totals
    num_days = len(dates)
    annual_hp_cost = np.sum(daily_hp_costs)
    annual_gas_energy_cost = np.sum(daily_gas_costs)
    annual_gas_total_cost = annual_gas_energy_cost + (GAS_STANDING_CHARGE * num_days)
    average_cop = np.mean(daily_avg_cops)
    
    return {
        "dates": dates,
        "daily_hp_costs": daily_hp_costs,
        "daily_gas_costs": daily_gas_costs,
        "daily_avg_temps": daily_avg_temps,
        "daily_avg_cops": daily_avg_cops,
        "num_days": num_days,
        "annual_hp_cost": annual_hp_cost,
        "annual_gas_energy_cost": annual_gas_energy_cost,
        "annual_gas_total_cost": annual_gas_total_cost,
        "average_cop": average_cop,
    }


def plot_annual_dhw_costs(
    results: dict,
    output_path: Path,
    show: bool = False,
    dpi: int = 200,
) -> Path:
    """Create plot showing daily DHW costs and temperatures throughout the year.
    
    Args:
        results: Dictionary from analyze_annual_dhw_costs
        output_path: Path to save the figure
        show: If True, display the plot
        dpi: Output resolution
        
    Returns:
        The written output_path
    """
    dates = results["dates"]
    daily_hp_costs = results["daily_hp_costs"]
    daily_gas_costs = results["daily_gas_costs"]
    daily_avg_temps = results["daily_avg_temps"]
    
    # Convert dates to matplotlib format
    dates_mpl = [datetime.combine(d, datetime.min.time()) for d in dates]
    
    fig, ax = plt.subplots(figsize=(10, 7.5))
    
    # ═══════════════════════════════════════════════════════════════════════
    # Left axis: Daily cost (£/day)
    # ═══════════════════════════════════════════════════════════════════════
    
    l1, = ax.plot(dates_mpl, daily_hp_costs, color="#1f77b4", linewidth=1.5,
                  label="Heat pump")
    l2, = ax.plot(dates_mpl, daily_gas_costs, color="#ff7f0e", linewidth=1.5,
                  linestyle="--", label="Gas boiler")
    
    ax.set_xlabel("Date (2025)", fontsize=11)
    ax.set_ylabel("Daily DHW cost (£/day)", fontsize=11)
    ax.set_title("Annual DHW Cost and Temperature (Cambridge 2025, 200 L/day)",
                 fontsize=11, fontweight="bold")
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0.4, 1.2)
    
    # Format x-axis as months
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    
    # ═══════════════════════════════════════════════════════════════════════
    # Right axis: Temperature (°C)
    # ═══════════════════════════════════════════════════════════════════════
    
    axr = ax.twinx()
    l3, = axr.plot(dates_mpl, daily_avg_temps, color="#2ca02c", linewidth=1.5,
                   alpha=0.7, label="Avg. outdoor temp")
    axr.fill_between(dates_mpl, daily_avg_temps, alpha=0.2, color="#2ca02c")
    
    axr.set_ylabel("Average outdoor temperature (°C)", fontsize=11, color="#2ca02c")
    axr.tick_params(axis="y", labelcolor="#2ca02c")
    axr.set_ylim(-5, 25)
    
    # Combined legend
    lines = [l1, l2, l3]
    labels = [l.get_label() for l in lines]
    ax.legend(lines, labels, loc="upper right", fontsize=9)
    
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
    
    if show:
        plt.show()
    else:
        plt.close(fig)
    
    return output_path


if __name__ == "__main__":
    # Paths
    data_dir = Path(__file__).parent.parent.parent / "data"
    csv_path = data_dir / "temperatures-cambridge-2025.csv"
    assets_dir = Path(__file__).parent.parent.parent / "assets"
    output_path = assets_dir / "annual_dhw_cost.png"
    
    print("Analyzing annual DHW costs...")
    print(f"Reading data from: {csv_path}")
    
    # Analyze
    results = analyze_annual_dhw_costs(csv_path)
    
    # Print results
    print(f"\n{'=' * 70}")
    print("Annual DHW Cost Analysis (Cambridge 2025, 200 L/day)")
    print(f"{'=' * 70}")
    print(f"Number of days analyzed:       {results['num_days']}")
    print(f"Average outdoor temperature:   {np.mean(results['daily_avg_temps']):.1f}°C")
    print(f"Average heat pump COP:         {results['average_cop']:.2f}")
    print(f"\nCosts:")
    print(f"  Heat pump (electricity):     £{results['annual_hp_cost']:.2f}")
    print(f"  Gas (energy only):           £{results['annual_gas_energy_cost']:.2f}")
    print(f"  Gas standing charge:         £{GAS_STANDING_CHARGE * results['num_days']:.2f}")
    
    # Scenario 1: DHW only (keeping gas for space heating)
    diff_dhw_only = results['annual_hp_cost'] - results['annual_gas_energy_cost']
    pct_dhw_only = ((results['annual_hp_cost'] / results['annual_gas_energy_cost']) - 1) * 100
    print(f"\nScenario 1: DHW only (gas retained for space heating)")
    print(f"  HP vs Gas (energy only):     £{diff_dhw_only:+.2f} ({pct_dhw_only:+.1f}%)")
    
    # Scenario 2: Full gas elimination
    diff_full = results['annual_hp_cost'] - results['annual_gas_total_cost']
    pct_full = ((results['annual_hp_cost'] / results['annual_gas_total_cost']) - 1) * 100
    print(f"\nScenario 2: Full gas elimination (space heating + DHW)")
    print(f"  HP vs Gas (with standing):   £{diff_full:+.2f} ({pct_full:+.1f}%)")
    print(f"{'=' * 70}")
    
    # Generate plot
    print(f"\nGenerating plot: {output_path}")
    plot_annual_dhw_costs(results, output_path)
    print("Done!")
