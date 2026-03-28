# Accepting the Need for Radiator Upgrades with a Heat Pump Installation 

Motivated by the desire to transition away from heating with gas and reduce CO2 emissions I have been reading up on heat pumps and their installation. Various sources such as ["So You're Thinking About a Heat Pump: The UK Homeowner's Guide to Heat Pumps"](https://www.amazon.co.uk/Youre-Thinking-About-Heat-Pump/dp/B0GK7H511K/) or [The Ultimate Guide to Heat Pumps: Britain's best installers and experts tell you exactly what to watch for and what to ask](https://www.amazon.co.uk/Ultimate-Guide-Heat-Pumps-installers/dp/B0FNMNVC4Q) recommend radiator upgrades which do unfortunately increase installation costs. Initially, I hoped to avoid such an upgrade by using a heat pump in tandem with our log burner. In order to be able to make a more informed decision, however, I have carried out a simple analysis using steady-state thermal models; the outcome confirms expert advice: the physical relationship between radiator capacity, flow temperature, and heat pump efficiency creates some constraints. For a complete heat pump installation without reliance on a log burner, radiator upgrades become necessary to achieve acceptable operating economics. Note however that this story focuses on order-of-magnitude estimates rather than precise scientific calculations.

# Static Analysis and Heat Loss

The starting point of this analysis is the state of our property after the efforts detailed in [Improving the Thermal Performance of UK 1930s Semi Detached Houses](https://peter-wurmsdobler.medium.com/improving-the-thermal-performance-of-uk-1930s-semi-detached-houses-6f64c6514565). Therein the heat transfer model  estimates the specific heat loss, or Heat Transfer Coefficient (HTC), to be **244 W/K**. In order to work out a representative heat loss of the building, I chose a cold winter month in Cambridge, UK: the bleak January 2026 with an average outdoor temperature T_o = 5°C; the indoor temperature was kept on average at T_i = 19°C (approximately 20°C downstairs, about 18°C upstairs). The resulting temperature difference is ΔT = 14K and yields an heat loss of Q_l = 244 × 14 = **3.42 kW**.

To validate this estimate, I looked up our energy consumption for January 2026: electricity consumption was 263.75kWh (8.5kWh/day on average or 0.35kW continuous power), and gas utilisation was 1,924.91kWh (62.1 kWh/day on average or 2.59kW continuous power) which includes space heating and domestic hot water. The latter is assumed to stay mostly the same throughout the year and determines the gas use in summer; for instance, in summer 2025 gas usage was about 12.5 kWh per day on average. As mentioned before, we have been using a log burner as supplemental heat source, providing approximately 3 kW output for 3 hours daily which contributes 9 kWh/day as heat (0.375 kW average power).

After subtracting assumed hot water consumption (12.5 kWh/day) from total gas consumption (62.1 kWh/day), the remaining 49.6 kWh/day of gas provides 47.12 kWh/day of actual heat to the radiators at 95% boiler efficiency, i.e. 1.96 kW average power. Since most of electricity is eventually dissipated as heat, e.g. from appliances, it will add about 0.3 kW as a heating equivalent. All combined, the total average heating power is 2.635 kW (radiators 1.96 kW + log burner 0.375 kW + appliances 0.3 kW), which is 77% of the estimated heat loss from first principles (3.42 kW). This discrepancy is a bit more than I expecyed but also reasonable, considering unaccounted solar gain and internal heat gains from occupants, and the fact that not all rooms are maintained at 19°C continuously (heating off from 10pm to 5am, and entrance hall more like 15°C). 

## Stationary Model of a House

The model used here assumes a simple lumped-mass representation of the house with the following parameters: internal thermal capacity or mass C, insulated envelope with heat transfer coefficient h, internal temperature T_i, and outside temperature T_o. Heat is supplied as Q_h through a flow rate V_f at flow temperature T_f and return temperature T_r. Heat is transferred to the internal thermal mass as Q_r through radiators with a characteristic constant K and radiative exponent n. Supplemental heat Q_b is provided by a log burner, and Q_a from appliances. The house loses heat as Q_l through the building fabric.

![Simle termal model for house](assets/house-model.png)
*Figure: Simple representation of a simple house model with heat sources and losses.*

The individual heat contributions can be written using heating fluid (water) density ρ and its specific thermal capacity c_p as:

Q_h = V_f * ρ * c_p * (T_f - T_r)<br>
Q_r = K * ((T_f + T_r)/2 - T_i)^n<br>
Q_l = h * (T_i - T_o)

In an equilibrium, or steady state as a stationary process, the heat balance is for the radiator circuit (no losses in short pipework), Q_h = Q_r, and for the room thermal balance, Q_r + Q_b + Q_a = Q_l. Therefore, the radiator system must deliver:

Q_r = Q_l - Q_b - Q_a = h * (T_i - T_o) - Q_b - Q_a

This simplified model treats all radiators as a single unit, assuming uniform flow and return temperatures throughout the system. The characteristic constant K represents the combined heat transfer capacity of all radiators, i.e. all their surfaces and types, plus the heating contribution from pipework distributed throughout the house. For the January 2026 conditions, the theoretical heat loss is Q_l = 3.42 kW, the log burner contributes Q_b = 0.375 kW (average), appliances contribute Q_a = 0.3 kW, giving a required radiator output of Q_r = 2.745 kW (theoretical). The radiator output obtained from the gas bill was Q_r = 1.96 kW, with total heat delivered of 2.635 kW.

## Empirical Validation

To validate the model, I used actual operating conditions from January 2026 with average radiator heating power of 1.96 kW, mean radiator temperature approximately 47.5°C (flow ~50°C, return ~45°C) as in these conditions it was bearable to touch them, indoor temperature 19°C, and temperature difference ΔT = 47.5 - 19 = 28.5K. The house radiators (see References) comprise Type 11 and Type 22 panels with total area 4.04 m² and calculated radiator constant from surface area of K = 35.9 W/K^n.

Using the radiator equation Q_r = K × ΔT^n with n = 1.2 and Q_r = 1.96 kW gives 1960 W = K × (28.5)^1.2 = K × 53.9, yielding an empirical K = 36.4 W/K^1.2. The empirical value (36.4) is about 1% higher than the calculated value from radiator area alone (35.9), which provides decent validation of our model. The close agreement confirms that the radiator specifications and operating conditions are accurately captured.

## Operating Constraints

With our empirically validated radiator constant (K = 36.4 W/K^1.2), we can now explore the fundamental relationship between flow rate and flow temperature for delivering heating power. Using constants for water as the working fluid (ρ = 1 kg/l and c_p = 4.18 kJ/kg/K), with the January 2026 average conditions (T_o = 5°C and T_i = 19°C), and radiator exponent n = 1.2, there are multiple combinations of flow temperature T_f and flow rate V_f that can deliver the same heating power.

![Contour Plot](assets/operations_contour.png)
*Figure: Contour plot showing constant heating power curves. The 1.96 kW average radiator heating power is highlighted in red. This curve represents the operational constraint imposed by the current radiator capacity.*

This contour plot reveals why radiator upgrades are recommended. For a given radiator constant K (i.e. all radiators combined), any target heating power defines a specific curve on this plot. The current radiators (K = 36.4 W/K^1.2) confine operation to the red 1.96 kW curve, which demonstrates the fundamental trade-off: low flow operation (~0.6 l/min) requires 70°C flow temperature with large temperature drop to the return temerpature (ΔT ≈ 33K) as well as a large temperature difference to the room temperature (ΔT ≈ 51K), whilst high flow operation (~20 l/min) requires only 47°C flow temperature with small temperature drop to the return temerpature (ΔT ≈ 1.5K) as well as a small temperature difference to the room temperature (ΔT ≈ 27K). Note that the delivered heating power converges to a constant at constant flow temperature with increasing flow rate, meaning that there is a limit to the flow rate. The only way to deliver more heat is to increase the flow temperature.

On the other hand, at 47°C which is already slightly above the recommended flow temperature, a heat pump can achieve a Coefficient of Performance (COP) of approximately 3.0; at 70°C the COP drops to around 2.3 whereas a flow temperature of 40°C could achieve a COP of 4. Consequently, higher heating power with the current radiators shifts the entire operating envelope upward into progressively lower COP territory. Radiator upgrades with higher K values moves these contours downward, enabling higher heat delivery at lower, more efficient temperatures. To deliver the theoretical peak load of 3.12 kW (with appliances contributing an additional 0.3 kW to reach total 3.42 kW) at a flow temperature of 47°C would require K ≈ 63 W/K^1.2, approximately 1.7× the current capacity, illustrating precisely why experts recommend radiator upgrades.

# Gas Boiler vs Heat Pump

To understand the practical implications of switching from a gas boiler to a heat pump, three scenarios are analysed based on the January 2026 measured performance. These scenarios are ordered by increasing dependence on the heat pump, revealing how the radiator capacity constraint progressively impacts performance and economics.

## Scenario 1: Gas Boiler Operation (with Log Burner)

Under actual January 2026 conditions, the radiators deliver Q_r = 1.96 kW average whilst the log burner provides Q_b = 0.375 kW average (9 kWh/day), and appliances contribute Q_a = 0.3 kW, giving total heat Q_l = 2.635 kW (including internal gains). The observed flow temperature is approximately 47°C with gas consumption for space heating of 49.6 kWh/day, resulting in a daily cost of £3.47 at 7p/kWh and 95% boiler efficiency.

The current system already operates at relatively high flow rates (~20 l/min), typical of modern condensing boilers with variable speed pumps, enabling the relatively low flow temperature of 47°C. With flow at 47°C and return at ~46°C, the mean water temperature is approximately 46.5°C. The radiator surface temperature is typically a few degrees cooler (around 39-41°C) due to heat transfer to air and thermal radiation, matching observed experience: radiators feel warm but are still comfortable to touch during typical January conditions, confirming the model predictions.

## Scenario 2: Heat Pump Replacing Gas Boiler (with Log Burner)

If the gas boiler is replaced with a heat pump whilst continuing to use the log burner for supplemental heat, the heat balance remains with radiators delivering Q_r = 1.96 kW, log burner providing Q_b = 0.375 kW, appliances contributing Q_a = 0.3 kW, and total heat Q_l = 2.635 kW (including internal gains). High flow operation optimised for the heat pump at 20 l/min requires a flow temperature of 47°C with return temperature ~46°C (ΔT ≈ 1.4K), delivering 1.96 kW heating power. The estimated COP is 3.0 (at T_o=5°C, T_f=47°C), requiring electrical input of ~0.65 kW for daily electricity consumption of 15.7 kWh and daily cost of £3.93 at 25p/kWh. 

With the log burner continuing to provide supplemental heat and appliances contributing internal gains, the heat pump operates at the edge of sensible performance with 47°C temperature. Daily operating cost (£3.93) is 13% higher than gas (£3.47), making this scenario more expensive despite achieving fossil fuel independence. This is partly due to the flow temperature still being a bit on the high side, and consequently the COP below the spark gap.

## Scenario 3: Heat Pump Without Log Burner

Without the log burner, the heat pump must provide the full heating requirement, exposing the radiator capacity constraint. Based on the heat balance equation (Q_r + Q_b + Q_a = Q_l), removing the log burner means that the total heat delivered Q_l = 1.96 + 0.375 + 0.3 = 2.635 kW (actual measured, including appliance gains) must now come from radiators and appliances, with Q_r = 2.335 kW required from the heat pump. 

Heat pump operation at maximum flow (20 l/min) requires a flow temperature of 52°C with return temperature ~50°C (ΔT ≈ 2K) to deliver 2.335 kW heating power. The estimated COP is 2.85 (at T_o=5°C, T_f=52°C), requiring electrical input of ~0.82 kW for daily electricity consumption of 19.7 kWh and daily cost of £4.93 at 25p/kWh. The operating cost is thus 42% higher than the gas+log burner configuration (£3.47/day).

The constraint is exacerbated during peak conditions. For a conservative design representing the theoretical full load during the coldest conditions, appliances contribute Q_a = 0.3 kW, leaving the heat pump to deliver 3.42 - 0.3 = 3.12 kW. At maximum flow (20 l/min), this requires a flow temperature of ~65°C with COP dropping to 2.45 and daily cost of £7.65. This worst-case scenario reveals why the expert recommendation for radiator upgrades is sound: attempting to deliver peak heating loads with insufficient radiator capacity forces operation into low-COP, high-cost area.

As mentioned before, radiator upgrade to K ≈ 65 W/K^1.2 would alleviate the problem. The same 2.335 kW average load could be delivered at 45-47°C (COP ~3.2, daily cost ~£4.38), whilst the 3.12 kW peak load would require only 50-52°C (COP ~2.9, daily cost ~£6.46). The upgrade transforms both the economics and the practical viability of heat pump operation without supplemental heating.

# Conclusion

The quantitative analysis explains why experts recommend radiator upgrades for heat pump installations. The contour plot reveals the fundamental constraint: current radiators with capacity K = 36.4 W/K^1.2 can deliver 1.96 kW at 47°C with excellent efficiency (COP ~3.0), but handling higher loads drives operation toward progressively higher temperatures and lower efficiency. At 2.335 kW (without log burner) the system requires 52°C (COP ~2.85), whilst the 3.12 kW theoretical peak load (accounting for 0.3 kW appliance contribution) demands ~65°C (COP ~2.45). Without sufficient radiator capacity, delivering required heating power necessitates higher flow temperatures, which directly reduces heat pump COP and increases operating costs. 

In conclusion, current radiators cannot support economically viable heat pump operation even with supplemental heating, as costs exceed gas heating in all scenarios. The recommended upgrade specification is: K value of 60-70 W/K^1.2 (approximately 1.7-1.9× current capacity), achieved by replacing existing radiators with larger Type 22 panels, adding additional radiators in key rooms, or upgrading to Type 33 (triple panel) in limited spaces. This would enable delivery of the 3.12 kW peak load at 45-47°C (accounting for 0.3 kW appliance contribution to reach theoretical 3.42 kW total). Generally speaking, radiator upgrades are not merely recommended but absolutely essential to achieve acceptable operating costs that make the technology transition economically viable.


# References

**Radiator specifications:** The installed radiators comprise single panel with single convector (Type 11) with dimensions 0.6×0.5 m, 1.0×0.5 m, 1.2×0.5 m, 0.5×0.6 m, and two 0.4×1.8 m panels totalling A = 3.14 m², and double panel with double convector (Type 22) with dimensions 0.6×0.5 m and 1.2×0.5 m totalling A = 0.9 m². Total radiator area is 4.04 m². Heat transfer coefficients based on typical radiator performance data (validated against multiple sources including manufacturer specifications are U ≈ 8 W/m²/K^1.2 for Type 11 radiators and U ≈ 12 W/m²/K^1.2 for Type 22 radiators.

**Boiler efficiency:** The Viessmann Vitodens 222-F condensing gas boiler achieves 95% efficiency under typical operating conditions.

**Energy costs** as of January 2026: Natural gas at 7p/kWh and electricity assumed at 25p/kWh for heat pump analysis as an obtainable price depending on the tariff.

**Appliance contribution:** Annual electricity consumption of approximately 2,695 kWh (7.4 kWh/day) is assumed to be largely dissipated as heat within the house (0.3 kW average), contributing to internal gains and reducing the heating load that must be supplied by radiators and supplemental heating sources.
