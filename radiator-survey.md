# Radiators

The purpose of this document is to capture the current state of the radiator isntallation and work out the thermal performance.

## Current survey

These are the radiatrors throughout our house, with their location, dimensions and rated T50 power.

[Compact Type 11 Single Panel Single Convector Radiator - 500 x 1200mm](https://www.wickes.co.uk/Compact-Type-11-Single-Panel-Single-Convector-Radiator---500-x-1200mm/p/176167)

master bedroom 1, 1.2 m × 0.5 m, 1037 W

[Compact Type 11 Single Panel Single Convector Radiator - 500 x 1000mm](https://www.wickes.co.uk/Compact-Type-11-Single-Panel-Single-Convector-Radiator---500-x-1000mm/p/176165)

master bedroom 2, 1.0 m × 0.5 m, 864 W

[Compact Type 11 Single Panel Single Convector Radiator - 500 x 600mm](https://www.wickes.co.uk/Compact-Type-11-Single-Panel-Single-Convector-Radiator---500-x-600mm/p/176161)

box room, 0.6 m × 0.5 m, 518 W

[Chrome Straight Single Panel Vertical Towel Radiator](https://www.wickes.co.uk/Kudox-Chrome-Straight-Single-Panel-Vertical-Towel-Radiator---1200-x-500mm/p/137726)

bath room, 0.5 m × 1.2 m, 340 W

[Slimline Single Panel Vertical Designer Radiator](https://www.wickes.co.uk/Henrad-by-Stelrad-Grey-Verona-Slimline-Single-Panel-Vertical-Designer-Radiator---1800-x-440-mm/p/323550)

family room, 0.4 m × 1.8 m, 1199 W

kitchen/diner, 0.4 m × 1.8 m, 1199 W

[Compact Type 21 Double Panel Plus Single Convector Radiator - 600 x 600mm](https://www.wickes.co.uk/Compact-Type-21-Double-Panel-Plus-Single-Convector-Radiator---600mm-x-600mm/p/176203)

entrance hall, 0.6 m × 0.6 m, 817 W

[Compact Type 22 Double Panel Double Convector Radiator - 500 x 1200mm](https://www.wickes.co.uk/Compact-Type-22-Double-Panel-Double-Convector-Radiator---500-x-1200mm/p/176229)

reception room, 1.2 m × 0.5 m, 1816 W

## Evaluation

The effective heat transfer coefficient U (W/m²/K^1.2) for each radiator is derived by solving:

Q = W × H × U × ΔT^1.2

at the rated condition ΔT = 50 K (i.e. 50^1.2 ≈ 109.3), giving U = Q / (W × H × 109.3).

| Room | Type | W × H (m) | Area (m²) | Rated power (W) | U (W/m²/K^1.2) | K contribution (W/K^1.2) |
|---|---|---|---|---|---|---|
| Master bedroom 1 | Type 11 | 1.2 × 0.5 | 0.60 | 1037 | 15.8 | 9.5 |
| Master bedroom 2 | Type 11 | 1.0 × 0.5 | 0.50 | 864 | 15.8 | 7.9 |
| Box room | Type 11 | 0.6 × 0.5 | 0.30 | 518 | 15.8 | 4.7 |
| Bathroom | Towel rail | 0.5 × 1.2 | 0.60 | 340 | 5.2 | 3.1 |
| Family room | Slimline single | 0.4 × 1.8 | 0.72 | 1199 | 15.2 | 11.0 |
| Kitchen/diner | Slimline single | 0.4 × 1.8 | 0.72 | 1199 | 15.2 | 11.0 |
| Entrance hall | Type 21 | 0.6 × 0.6 | 0.36 | 817 | 20.8 | 7.5 |
| Reception room | Type 22 | 1.2 × 0.5 | 0.60 | 1816 | 27.7 | 16.6 |
| **Total** | | | | **7790 W** | | **71.2** |

The K contribution per radiator is W × H × U = Q_rated / 50^1.2 = Q_rated / 109.3. Summing all contributions gives a survey-based house radiator constant of **K_survey = 71.2 W/K^1.2**.

This value is grounded in manufacturers' rated output figures and represents an upper bound. In practice, not all radiators run simultaneously or at fully open thermostatic valves, the bathroom towel rail contributes little to space heating, and flow distribution across a real circuit is uneven. The empirically identified K from actual operation captures the integrated system response under actual operating conditions, which will naturally fall below the sum of rated peak outputs.
