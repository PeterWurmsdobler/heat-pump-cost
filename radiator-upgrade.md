# Radiators

The purpose of this document is to capture the current state of the radiator isntallation and work out the thermal performance.

## Current survey

These are the radiatrors throughout our house, with their location, dimensions and rated T50 power.

[Compact Type 11 Single Panel Single Convector Radiator - 500 x 1400mm](https://www.wickes.co.uk/Compact-Type-11-Single-Panel-Single-Convector-Radiator---500-x-1400mm/p/176168)

master bedroom 1, 1.4 m × 0.5 m, 1210 W

[Compact Type 11 Single Panel Single Convector Radiator - 500 x 1200mm](https://www.wickes.co.uk/Compact-Type-11-Single-Panel-Single-Convector-Radiator---500-x-1200mm/p/176167)

master bedroom 2, 1.2 m × 0.5 m, 1037 W

[Compact Type 11 Single Panel Single Convector Radiator - 500 x 1000mm](https://www.wickes.co.uk/Compact-Type-11-Single-Panel-Single-Convector-Radiator---500-x-1000mm/p/176165)

box room, 1.0 m × 0.5 m, 864 W

[Milano Bow Central Connection Heated Towel Rail 1269mm x 500mm](https://www.bestheating.com/milano-bow-d-bar-heated-towel-rail-choice-of-size-and-finish-149208)

bath room, 0.5 m × 1.269 m, 952 W

[Henrad by Stelrad White Plan Double Convector Vertical Designer Radiator - 1800mm](https://www.wickes.co.uk/Henrad-by-Stelrad-White-Plan-Double-Convector-Vertical-Designer-Radiator---1800mm/p/9000294470)

family room, 0.4 m × 1.8 m,  1476 W

kitchen/diner, 0.4 m × 1.8 m,  1476 W

[Compact Type 21 Double Panel Plus Single Convector Radiator - 800 x 600mm](https://www.wickes.co.uk/Compact-Type-21-Double-Panel-Plus-Single-Convector-Radiator---600mm-x-800mm/p/176205)

entrance hall, 0.8 m × 0.6 m,  1090 W

[Compact Type 22 Double Panel Double Convector Radiator - 500 x 1400mm](https://www.wickes.co.uk/Compact-Type-22-Double-Panel-Double-Convector-Radiator---500-x-1400mm/p/176230)

reception room, 1.4 m × 0.5 m,  2118 W

## Evaluation

The effective heat transfer coefficient U (W/m²/K^1.2) for each radiator is derived by solving:

Q = W × H × U × ΔT^1.2

at the rated condition ΔT = 50 K (i.e. 50^1.2 ≈ 109.3), giving U = Q / (W × H × 109.3).

| Room | Type | W × H (m) | Area (m²) | Rated power (W) | U (W/m²/K^1.2) | K contribution (W/K^1.2) |
|---|---|---|---|---|---|---|
| **Total** | | | | **XXX W** | | **XXX** |

The K contribution per radiator is W × H × U = Q_rated / 50^1.2 = Q_rated / 109.3. Summing all contributions gives a survey-based house radiator constant of **K_survey = XXX W/K^1.2**.

This value is grounded in manufacturers' rated output figures and represents an upper bound. In practice, not all radiators run simultaneously or at fully open thermostatic valves, the bathroom towel rail contributes little to space heating, and flow distribution across a real circuit is uneven. 