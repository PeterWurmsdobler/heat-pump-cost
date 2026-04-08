# COP Estimation from Flow and Outdoor Temperature

The Coefficient of Performance (COP) of a heat pump is estimated using a fraction-of-Carnot model:

$$\text{COP} = \eta \cdot \frac{T_\text{cond}}{T_\text{cond} - T_\text{evap}}$$

where temperatures are in Kelvin and:

| Symbol | Value | Meaning |
|---|---|---|
| $\eta$ | 0.55 | Practical efficiency factor (fraction of ideal Carnot COP achieved by a modern heat pump) |
| $T_\text{evap}$ | $T_o + 273.15$ K | Evaporator temperature — taken as outdoor air temperature |
| $T_\text{cond}$ | $T_f + 5 + 273.15$ K | Condenser temperature — flow temperature plus a 5 K lift |

The **5 K condenser lift** accounts for the temperature difference needed to transfer heat from the refrigerant condensing inside the heat pump to the heating circuit water flowing at $T_f$.

## Example

At peak demand with $T_f = 74°C$ and $T_o = 5°C$:

$$T_\text{evap} = 278.15 \text{ K}, \quad T_\text{cond} = 352.15 \text{ K}$$

$$\text{COP}_\text{Carnot} = \frac{352.15}{352.15 - 278.15} = \frac{352.15}{74} = 4.76$$

$$\text{COP} = 0.55 \times 4.76 \approx 2.6$$

At steady-state heating with $T_f = 40°C$ and $T_o = 5°C$:

$$T_\text{cond} = 318.15 \text{ K}, \quad T_\text{cond} - T_\text{evap} = 40 \text{ K}$$

$$\text{COP} = 0.55 \times \frac{318.15}{40} \approx 4.4$$

## Notes

- The $\eta = 0.55$ factor is a commonly used approximation for a modern air-source heat pump operating under realistic field conditions. Manufacturer data sheets typically quote COP at fixed test points (e.g. EN 14511), so real-world seasonal performance depends strongly on the distribution of operating hours across flow and outdoor temperatures.
- No evaporator-side temperature lift is modelled; $T_\text{evap}$ is assumed equal to outdoor air temperature. In practice, the refrigerant evaporates slightly below outdoor air temperature, which would reduce COP marginally further.
- These COP values are used to convert heating power $Q_r$ (W) into electrical input power: $P_\text{elec} = Q_r / \text{COP}$.
