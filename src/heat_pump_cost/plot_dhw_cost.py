"""Plot daily cost and COP for domestic hot water (DHW) generation.

Calculates the cost of heating 200 litres of water from 10°C to 55°C
using either a gas boiler or heat pump, as a function of outdoor temperature.

Key parameters:
  - DHW volume: 200 L/day
  - Temperature rise: 10°C → 55°C (ΔT = 45 K)
  - Thermal energy: 200 kg × 4.18 kJ/kg/K × 45 K = 37,620 kJ = 10.5 kWh
  - Flow temperature: 55°C (required for DHW)
  - Gas boiler efficiency: 95%
  - Electricity price: 27.69 p/kWh (January 2026)
  - Gas price: 5.93 p/kWh (January 2026)
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from heat_pump_cost.radiator_analysis import cop_estimate

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DHW_THERMAL_ENERGY_KWH = 10.5  # kWh thermal to heat 200L from 10°C to 55°C
DHW_FLOW_TEMP = 55.0           # °C - required flow temperature for DHW

GAS_PRICE_PER_KWH = 5.93 / 100.0      # £/kWh
ELECTRICITY_PRICE_PER_KWH = 27.69 / 100.0  # £/kWh
BOILER_EFFICIENCY = 0.95


def calculate_dhw_costs(t_outdoor_range: np.ndarray) -> dict:
    """Calculate DHW costs and COP across a range of outdoor temperatures.
    
    Args:
        t_outdoor_range: Array of outdoor temperatures [°C]
        
    Returns:
        Dictionary with arrays: t_outdoor, cop, hp_cost_gbp, gas_cost_gbp
    """
    # Calculate COP for each outdoor temperature at DHW flow temp (55°C)
    cop_array = np.array([cop_estimate(t_o, DHW_FLOW_TEMP) for t_o in t_outdoor_range])
    
    # Heat pump electricity consumption [kWh]
    hp_electricity_kwh = DHW_THERMAL_ENERGY_KWH / cop_array
    
    # Heat pump daily cost [£]
    hp_cost_gbp = hp_electricity_kwh * ELECTRICITY_PRICE_PER_KWH
    
    # Gas boiler consumption and cost [£] - constant for all temperatures
    gas_kwh = DHW_THERMAL_ENERGY_KWH / BOILER_EFFICIENCY
    gas_cost_gbp = gas_kwh * GAS_PRICE_PER_KWH  # This is a scalar
    
    return {
        "t_outdoor": t_outdoor_range,
        "cop": cop_array,
        "hp_electricity_kwh": hp_electricity_kwh,
        "hp_cost_gbp": hp_cost_gbp,
        "gas_cost_gbp": gas_cost_gbp,  # Scalar value
    }


def plot_dhw_cost_and_cop(
    output_path: Path,
    t_min: float = -10.0,
    t_max: float = 40.0,
    show: bool = False,
    dpi: int = 200,
) -> Path:
    """Create dual-axis plot showing DHW cost and COP vs outdoor temperature.
    
    Left axis: Daily cost (£/day) - blue
    Right axis: COP - green
    
    Args:
        output_path: Path to save the figure
        t_min: Minimum outdoor temperature [°C]
        t_max: Maximum outdoor temperature [°C]
        show: If True, display the plot
        dpi: Output resolution
        
    Returns:
        The written output_path
    """
    # Calculate costs across temperature range
    t_outdoor = np.linspace(t_min, t_max, 200)
    data = calculate_dhw_costs(t_outdoor)
    
    # Create figure with single axis
    fig, ax = plt.subplots(figsize=(10, 7.5))
    
    # ═══════════════════════════════════════════════════════════════════════
    # Left axis: Daily cost (blue)
    # ═══════════════════════════════════════════════════════════════════════
    
    # Heat pump cost (varies with temperature)
    l1, = ax.plot(t_outdoor, data["hp_cost_gbp"], color="#1f77b4", linewidth=2.5, 
                  label="Heat pump cost")
    ax.fill_between(t_outdoor, data["hp_cost_gbp"], alpha=0.2, color="#1f77b4")
    
    # Gas boiler baseline (constant)
    gas_baseline = data["gas_cost_gbp"]  # Scalar value
    l2 = ax.axhline(gas_baseline, color="#ff7f0e", linewidth=2, linestyle="--",
                    label=f"Gas boiler ({gas_baseline:.2f} £/day)")
    
    ax.set_xlabel("Outdoor temperature (°C)", fontsize=11)
    ax.set_ylabel("Daily cost (£/day)", fontsize=11)
    ax.set_title("DHW Daily Cost and COP (200 L/day, 10→55°C)", 
                 fontsize=11, fontweight="bold")
    ax.grid(True, alpha=0.3)
    ax.set_xlim(t_min, t_max)
    ax.set_ylim(0.2, 1.2)
    
    # ═══════════════════════════════════════════════════════════════════════
    # Right axis: COP (green)
    # ═══════════════════════════════════════════════════════════════════════
    
    axr = ax.twinx()
    l3, = axr.plot(t_outdoor, data["cop"], color="#2ca02c", linewidth=2.5,
                   label="COP")
    axr.fill_between(t_outdoor, data["cop"], alpha=0.2, color="#2ca02c")
    
    axr.set_ylabel("COP", fontsize=11, color="#2ca02c")
    axr.tick_params(axis="y", labelcolor="#2ca02c")
    axr.set_ylim(2, 10)
    
    # Add break-even COP reference line (COP where HP cost equals gas cost)
    # At break-even: (E_thermal / COP) × P_elec = (E_thermal / η_boiler) × P_gas
    # Therefore: COP = P_elec × η_boiler / P_gas = spark_gap × η_boiler
    spark_gap = ELECTRICITY_PRICE_PER_KWH / GAS_PRICE_PER_KWH
    break_even_cop = spark_gap * BOILER_EFFICIENCY
    l4 = axr.axhline(break_even_cop, color="#2ca02c", linewidth=1.5, linestyle=":",
                     alpha=0.7, label=f"Break-even COP = {break_even_cop:.2f}")
    
    # Find break-even temperature (where HP cost = gas cost)
    break_even_idx = np.argmin(np.abs(data["hp_cost_gbp"] - gas_baseline))
    break_even_temp = t_outdoor[break_even_idx]
    break_even_hp_cost = data["hp_cost_gbp"][break_even_idx]
    break_even_cop_value = data["cop"][break_even_idx]
    
    # Add vertical line at break-even temperature
    ax.axvline(break_even_temp, color="gray", linewidth=1.5, linestyle="-",
               alpha=0.6, zorder=1)
    
    # Add dots at intersection points
    ax.plot(break_even_temp, break_even_hp_cost, 'o', color="#1f77b4", 
            markersize=8, zorder=5)
    ax.plot(break_even_temp, gas_baseline, 'o', color="#ff7f0e", 
            markersize=8, zorder=5)
    axr.plot(break_even_temp, break_even_cop_value, 'o', color="#2ca02c", 
             markersize=8, zorder=5)
    
    # Annotate the break-even temperature (above and right of orange crossing point)
    ax.annotate(f'Break-even\nT_o = {break_even_temp:.1f}°C',
                xy=(break_even_temp, gas_baseline), xytext=(break_even_temp + 6, 0.80),
                fontsize=9, ha='left', color='gray',
                arrowprops=dict(arrowstyle='->', color='gray', lw=1, alpha=0.6))
    
    # Combined legend - top center
    lines = [l1, l2, l3, l4]
    labels = [l.get_label() for l in lines]
    ax.legend(lines, labels, loc="upper center", fontsize=9)
    
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
    
    if show:
        plt.show()
    else:
        plt.close(fig)
    
    return output_path


def plot_dhw_spark_gap(
    output_path: Path,
    t_min: float = -10.0,
    t_max: float = 40.0,
    show: bool = False,
    dpi: int = 200,
) -> Path:
    """Create plot showing required spark gap for DHW break-even vs outdoor temperature.
    
    Shows what spark gap is needed to make heat pump DHW economically viable
    at different outdoor temperatures.
    
    Args:
        output_path: Path to save the figure
        t_min: Minimum outdoor temperature [°C]
        t_max: Maximum outdoor temperature [°C]
        show: If True, display the plot
        dpi: Output resolution
        
    Returns:
        The written output_path
    """
    # Calculate required spark gap across temperature range
    t_outdoor = np.linspace(t_min, t_max, 200)
    data = calculate_dhw_costs(t_outdoor)
    
    # Required spark gap = COP / boiler_efficiency
    required_spark_gap = data["cop"] / BOILER_EFFICIENCY
    
    # Current spark gap
    current_spark_gap = ELECTRICITY_PRICE_PER_KWH / GAS_PRICE_PER_KWH
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 7.5))
    
    # Plot required spark gap
    ax.plot(t_outdoor, required_spark_gap, color="#1f77b4", linewidth=2.5,
            label="Required spark gap")
    ax.fill_between(t_outdoor, required_spark_gap, alpha=0.2, color="#1f77b4")
    
    # Current spark gap line
    ax.axhline(current_spark_gap, color="#ff7f0e", linewidth=2, linestyle="--",
               label=f"Current spark gap = {current_spark_gap:.2f}")
    
    # Find break-even temperature
    break_even_idx = np.argmin(np.abs(required_spark_gap - current_spark_gap))
    break_even_temp = t_outdoor[break_even_idx]
    
    # Add vertical line at break-even
    ax.axvline(break_even_temp, color="gray", linewidth=1.5, linestyle="-",
               alpha=0.6)
    ax.plot(break_even_temp, current_spark_gap, 'o', color="#ff7f0e",
            markersize=8)
    
    # Annotate break-even point
    ax.annotate(f'Break-even\nT_o = {break_even_temp:.1f}°C',
                xy=(break_even_temp, current_spark_gap),
                xytext=(break_even_temp + 6, current_spark_gap + 0.5),
                fontsize=9, ha='left', color='gray',
                arrowprops=dict(arrowstyle='->', color='gray', lw=1, alpha=0.6))
    
    # Highlight design temperature (-2°C)
    design_temp = -2.0
    design_idx = np.argmin(np.abs(t_outdoor - design_temp))
    design_spark_gap = required_spark_gap[design_idx]
    
    ax.axvline(design_temp, color="red", linewidth=1.5, linestyle=":",
               alpha=0.6)
    ax.plot(design_temp, design_spark_gap, 'o', color="red", markersize=8)
    
    # Annotate design temperature - place in top left area of plot
    ax.text(-8, 9.2, f'Design temp: T_o = {design_temp:.0f}°C\nRequired spark gap = {design_spark_gap:.2f}',
            fontsize=9, ha='left', va='top', color='red',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='red', alpha=0.8))
    
    ax.set_xlabel("Outdoor temperature (°C)", fontsize=11)
    ax.set_ylabel("Required spark gap for break-even", fontsize=11)
    ax.set_title("DHW Break-even Spark Gap vs Outdoor Temperature (200 L/day, 10→55°C)",
                 fontsize=11, fontweight="bold")
    ax.grid(True, alpha=0.3)
    ax.set_xlim(t_min, t_max)
    ax.set_ylim(2, 10)
    ax.legend(loc="upper right", fontsize=9)
    
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
    
    if show:
        plt.show()
    else:
        plt.close(fig)
    
    return output_path


if __name__ == "__main__":
    # Generate the plots
    assets_dir = Path(__file__).parent.parent.parent / "assets"
    
    # Cost and COP plot
    output_path_cost = assets_dir / "hot_water_cost.png"
    print("Generating DHW cost and COP plot...")
    plot_dhw_cost_and_cop(output_path_cost, show=False)
    print(f"Saved: {output_path_cost}")
    
    # Spark gap plot
    output_path_spark = assets_dir / "hot_water_spark_gap.png"
    print("\nGenerating DHW spark gap plot...")
    plot_dhw_spark_gap(output_path_spark, show=False)
    print(f"Saved: {output_path_spark}")
    
    # Print some key statistics
    t_range = np.linspace(-10, 40, 200)
    data = calculate_dhw_costs(t_range)
    
    print(f"\n{'─' * 60}")
    print("DHW Cost Analysis (200 L/day, 10→55°C)")
    print(f"{'─' * 60}")
    print(f"Thermal energy required:  {DHW_THERMAL_ENERGY_KWH:.1f} kWh/day")
    print(f"Gas boiler cost (95% eff): £{data['gas_cost_gbp']:.3f}/day")
    print(f"\nHeat pump cost by outdoor temperature:")
    for t_o in [-10, -2, 0, 5, 10, 15, 20]:
        idx = np.argmin(np.abs(t_range - t_o))
        cop = data['cop'][idx]
        cost = data['hp_cost_gbp'][idx]
        elec_kwh = data['hp_electricity_kwh'][idx]
        required_sg = cop / BOILER_EFFICIENCY
        print(f"  T_o = {t_o:3.0f}°C: COP = {cop:.2f}, "
              f"elec = {elec_kwh:.2f} kWh, cost = £{cost:.3f}/day, "
              f"req. spark gap = {required_sg:.2f}")
    
    # Break-even analysis
    spark_gap = ELECTRICITY_PRICE_PER_KWH / GAS_PRICE_PER_KWH
    break_even_cop = spark_gap * BOILER_EFFICIENCY
    print(f"\nSpark gap (elec/gas):     {spark_gap:.2f}")
    print(f"Break-even COP:           {break_even_cop:.2f}")
