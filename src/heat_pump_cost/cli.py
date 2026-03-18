"""Command-line interface for heat pump cost analysis."""

import argparse
import sys

from heat_pump_cost.plot_cost_analysis import run_analysis


def main():
    """CLI entry point for heat pump cost analysis."""
    parser = argparse.ArgumentParser(
        description="Analyze optimal balance between heat pump and insulation costs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default settings (25,000 kWh initial heat loss, 15p/kWh electricity)
  heat-pump-cost

  # Specify custom initial heat loss
  heat-pump-cost --initial-heat-loss 20000

  # Use custom data files
  heat-pump-cost --heat-pumps data/my-heat-pumps.csv --improvements data/my-improvements.csv

  # Specify output directory
  heat-pump-cost --output-dir results/

  # Custom electricity rate (20p/kWh)
  heat-pump-cost --electricity-rate 0.20
"""
    )
    
    parser.add_argument(
        '--initial-heat-loss',
        type=float,
        default=25000,
        help='Initial annual heat loss in kWh (default: 25000)'
    )
    
    parser.add_argument(
        '--heat-pumps',
        type=str,
        default='data/heat-pump-ratings.csv',
        help='Path to heat pump ratings CSV file (default: data/heat-pump-ratings.csv)'
    )
    
    parser.add_argument(
        '--improvements',
        type=str,
        default='data/home-improvements.csv',
        help='Path to home improvements CSV file (default: data/home-improvements.csv)'
    )
    
    parser.add_argument(
        '--electricity-rate',
        type=float,
        default=0.15,
        help='Electricity cost per kWh in £ (default: 0.15)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='assets',
        help='Directory to save output plots (default: assets)'
    )
    
    args = parser.parse_args()
    
    # Run the analysis
    try:
        run_analysis(
            initial_heat_loss=args.initial_heat_loss,
            heat_pumps_csv=args.heat_pumps,
            improvements_csv=args.improvements,
            electricity_rate=args.electricity_rate,
            output_dir=args.output_dir
        )
        print("\n✓ Analysis complete!")
        return 0
    except FileNotFoundError as e:
        print(f"Error: Could not find file: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
