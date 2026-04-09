# How the Spark Gap Drives Radiator Upgrades for Heat Pump Installations 

The preceding story, [Impediments to UK Heat Pump Adoption and Possible Solutions](https://peter-wurmsdobler.medium.com/impediments-to-uk-heat-pump-adoption-and-possible-solutions-7d3812c091e4), addresses the complexity (and cost) of heatpump installation as one impediment to their wider adoption; this story is about the spark gap and its implication on capital and operational expenses in a perhaps not obvious way, namely through the implications for the radiator capacity.

Various sources such as ["So You're Thinking About a Heat Pump: The UK Homeowner's Guide to Heat Pumps"](https://www.amazon.co.uk/Youre-Thinking-About-Heat-Pump/dp/B0GK7H511K/) or [The Ultimate Guide to Heat Pumps: Britain's best installers and experts tell you exactly what to watch for and what to ask](https://www.amazon.co.uk/Ultimate-Guide-Heat-Pumps-installers/dp/B0FNMNVC4Q) recommend radiator upgrades which do unfortunately increase installation costs. Initially, I hoped to avoid such an upgrade by using a heat pump in tandem with our log burner. In order to be able to make a more informed decision, however, I have carried out a simple analysis using steady-state thermal models. 

The outcome doesn't come as a surprise: the spark gap, the ratio of the unit price of electricity to that of gas, currently stands at about 4.67(^2); this directly sets the minimum [Coefficient of Performance](https://en.wikipedia.org/wiki/Coefficient_of_performance) (COP) a heat pump must achieve to be cheaper to run than a gas boiler. Achieving that COP requires operating at sufficiently low flow temperatures, which in turn requires more radiator capacity. The radiator upgrades are therefore driven by the spark gap rather than being an inherent requirement of heat pump technology; whether they are needed depends on both the heating load scenario and which costs are accounted for. For average heating loads in our home, the current radiators turn out to be sufficient once the gas connection is fully decommissioned; however, at design temperature conditions (-2°C for Cambridge), the spark gap forces a break-even radiator constant of K ≈ 265 W/K^1.2 (3.73× current)—economically absurd, and a direct consequence of the pricing gap rather than the technology. 

![Radiator upgrades](assets/radiator-upgrades.png)

# Static Analysis and Heat Loss

The starting point of this analysis is the state of our property after the efforts detailed in [Improving the Thermal Performance of UK 1930s Semi Detached Houses](https://peter-wurmsdobler.medium.com/improving-the-thermal-performance-of-uk-1930s-semi-detached-houses-6f64c6514565). To work out the representative heat loss of the building, I analysed a cold winter month in Cambridge, UK: the bleak January 2026 with an average outdoor temperature T_o = 5°C. During that time the indoor temperature was kept on average at T_i = 19°C (approximately 20°C downstairs, about 18°C upstairs), giving a temperature difference of ΔT = 14K.

Energy consumption for January 2026 was: electricity 263.75kWh (8.5kWh/day on average or 0.35kW continuous power), and gas 1,924.91kWh (62.1 kWh/day on average or 2.59kW continuous power); the latter includes both space heating and domestic hot water (DHW). It is assumed that energy for DHW stays mostly the same throughout the year and is solely responsible for the gas use in summer; for instance, in summer 2025 gas usage was about 12.5 kWh per day on average. In addition, we have been using a log burner as supplemental heat source, providing approximately 3 kW output for 3 hours daily which contributes 9 kWh/day as heat (0.375 kW average power). Over the heating period we are using about 1m^3 of locally sourced hard wood for £150, which results in about £1/day.

After subtracting the estimated DHW portion (12.5 kWh/day) from total gas consumption (62.1 kWh/day), the remaining 49.6 kWh/day of gas provides 47.12 kWh/day of actual heat to the radiators at 95% boiler efficiency(^1), i.e. 1.96 kW average power. Electricity consumed by appliances and eventually dissipated as heat will add about 0.3 kW as a heating equivalent. All combined, the total average heating power estimate is 2.635 kW (radiators 1.96 kW + log burner 0.375 kW + appliances 0.3 kW). Consequently, the empirical Heat Transfer Coefficient based on actual power consumption is **188 W/K** with ΔT = 14K.

For comparison, the theoretical heat transfer model derived from first principles in the previous article estimates the Heat Transfer Coefficient (HTC) to be 244 W/K, which would give a theoretical heat loss of Q_l = 244 × 14 = 3.42 kW. The actual heating power (2.635 kW) is about 77% of the theoretical heat loss. This discrepancy is understandable, considering unaccounted solar gain and internal heat gains from occupants, as well as the fact that not all rooms are maintained at 19°C continuously (heating off from 10pm to 5am, and entrance hall more like 15°C) and we are using thick curtains for the main entrance, French doors and windows. For the remainder of this analysis, we use the empirical value of **188 W/K**, which represents real-world operating conditions. 

## Stationary Model of a House

The model used here assumes a simple lumped-mass representation of the house with the following parameters: internal temperature T_i, and outside temperature T_o; heat is supplied as Q_h at flow temperature T_f and return temperature T_r, then transferred to the internal thermal mass as Q_r through radiators; supplemental heat Q_b is provided by a log burner, and Q_a from appliances. The house loses heat as Q_l through the building fabric.

![Simple thermal model for house](assets/house-model.png)
*Figure: Simple representation of a simple house model with heat sources and losses.*

The individual heat contributions can be written using heating fluid (water) density ρ, its specific thermal capacity c_p and a flow rate V_f, the characteristic radiator constant K and radiative exponent n, and finally the transfer coefficient h, all together:

Q_h = V_f * ρ * c_p * (T_f - T_r)<br>
Q_r = K * ((T_f + T_r)/2 - T_i)^n = K × ΔT^n<br>
Q_l = h * (T_i - T_o)

In an equilibrium, or steady state, the heat balance for the radiator circuit (no losses in short pipework), is Q_h = Q_r, and for the room thermal balance, Q_l = Q_r + Q_b + Q_a; just as a side note, in a steady state the balance is invariant to the thermal mass. Overall, the radiator system must deliver:

Q_r = Q_l - Q_b - Q_a = h * (T_i - T_o) - Q_b - Q_a

For the January 2026 conditions with empirical h = 188 W/K and ΔT = 14 K, the total heat loss is Q_l = 188 × 14 = 2.632 kW. The log burner contributes Q_b = 0.375 kW (average), and appliances contribute Q_a = 0.3 kW, leaving the radiators to deliver Q_r = 2.632 - 0.375 - 0.3 = 1.957 kW ≈ 1.96 kW. This matches precisely the actual gas consumption measured in January 2026, validating our empirical Heat Transfer Coefficient.


## Empirical Radiator Validation

The simplified stationary model treats all radiators as a single unit, assuming uniform flow and return temperatures through a well-balanced system. The characteristic constant K represents the combined heat transfer capacity of all radiators, i.e. all their surfaces and types, plus the heating contribution from pipework distributed throughout the house. My [Radiator Survey](https://github.com/PeterWurmsdobler/heat-pump-cost/radiator-survey.md) calculated this constant to be K = 71.2 W/K^1.2.

Using the radiator equation Q_r = K × ΔT^1.2 and Q_r = 1.96 kW gives 1960 W = 71.2 W/K^1.2 × ΔT^1.2, i.e. ΔT required works out to be 15.8 K and depends on both the indoor temperature 19°C and the mean radiator temperature which in turn depends on the flow rate and flow temperature; here we assume about 10 l/min which results in a mean radiator temperature of approximately 35°C (flow ~36°C, return ~34°C). These numbers correlate with the temperature perceived when touching the radiators during the day: they are warm, around the body temperature but never more than 40-45°C. 

## Operating Constraints

With our empirically validated radiator constant (K = 71.2 W/K^1.2), we can now explore the fundamental relationship between flow rate and flow temperature for delivering heating power. Using constants for water as the working fluid (ρ = 1 kg/l and c_p = 4.18 kJ/kg/K), with the January 2026 average conditions (T_o = 5°C and T_i = 19°C), and radiator exponent n = 1.2, there are combinations of flow temperature T_f and flow rate V_f that can deliver the same heating power, shown as curves at constant power in the following plot. In other words, a heating controller can modulate either the flow temperature T_f or the flow rate V_f to achieve the same effect (if not sabotaged by Thermostatic Radiator Valves, TRVs).

![Contour Plot](assets/operations_contour.png)
*Figure: Contour plot showing constant heating power curves. The 1.96 kW average radiator heating power is highlighted in red. This curve represents the operational constraint imposed by the current radiator capacity.*

The current radiators confine operation to the red 1.96 kW curve, which demonstrates the fundamental trade-off: low flow operation (~1 l/min) requires 49°C flow temperature with a large temperature drop to the return (ΔT ≈ 28 K), whilst high flow operation (~20 l/min) requires only 36°C flow temperature with a small temperature drop to the return (ΔT ≈ 1.4 K). At both extremes the mean radiator temperature is roughly the same (~35°C, determined by K and the heating load), but the higher flow rate achieves the target power with a much lower flow temperature which is what matters for the heat pump COP. 

# The Radiator Constant Impact

The contour plot shows something else: for a given radiator constant K and flow temperature, a horizontal line, the delivered heating power gets smaller and converges towards a constant with increasing flow rate; in other words, there is a limit to how much power can be delivered over existing radiators at a given flow temperature which is reached when the difference between radiator flow and return temperature goes to zero as the flow rate goes to infinity. Most pumps will struggle to reach that point as fluid dynamics will affect resistance and pumping power is limited; so practically, the maximum flow rate will be below 20l/min. The heat delivered becomes then a function of the flow temperature only, and so does the COP.

## Performance over Power

As already stated at the beginning, the spark gap is simply the ratio of the unit price of electricity to that of gas: at January 2026 prices, 27.69p/kWh divided by 5.93p/kWh gives 4.67(^2). For the heat pump to cost no more to run than the gas boiler it replaces, it must achieve a COP of at least 4.67; below that threshold, each unit of heat costs more to produce electrically than it would with gas. It is therefore perhaps revealing to show both the required flow temperature T_f and the achievable COP as a function of heat delivered, in our current setup (K = 71.2 W/K^1.2), bearing in mind that the heat pump needs to run at about 5°C above the radiator flow temperature since heat needs to be transferred from the internal heat pump refrigerant circuit to the radiator circuit. Three scenarios detailed below demonstrate the situation.

![Performance vs Power](assets/performance_vs_power.png)
*Figure: For the current radiator constant K = 71.2 W/K^1.2, the flow temperature (left axis, blue) and the expected COP (right axis, green) plotted over heat power delivered. The flow temperature curve is calculated at T_o=5°C. Two COP curves are shown: solid green for T_o=5°C (typical winter) and dashed green for T_o=-2°C (design temperature), illustrating how outdoor temperature affects COP independently of flow temperature. The red dashed line shows break-even COP = 4.67. The three marked points show: 1.96 kW with log burner (COP = 4.85 at 5°C, above break-even), 2.34 kW continuous without log burner (COP = 4.56 at 5°C, slightly below), and 3.65 kW at design temperature (COP = 3.32 at -2°C, well below due to outdoor temperature).*

For all three scenarios the assumption is that the heat pump also covers domestic hot water, allowing the gas connection to be fully decommissioned and the standing charge of 35.09p/day (£0.35/day) to be saved.

### Scenario 1 Heat Pump With Log Burner

If the gas boiler is replaced with a heat pump whilst continuing to use the log burner for supplemental heat, the heat balance remains with radiators delivering Q_r = 1.96 kW, log burner providing Q_b = 0.375 kW, appliances contributing Q_a = 0.3 kW, and total heat Q_l = 2.635 kW (including internal gains). High flow operation optimised for the heat pump at 20 l/min requires a flow temperature of 36°C with return temperature ~35°C (ΔT ≈ 1.4 K), delivering 1.96 kW heating power. The estimated COP is 4.85 (at T_o=5°C, T_f=36°C), requiring electrical input of ~0.40 kW for daily electricity consumption of 9.7 kWh and daily electricity cost of £2.68 at 27.69p/kWh. Adding the log burner wood cost of £1.00/day gives a total daily cost of £3.68.

For comparison, with Q_r = 1.96 kW, the current gas-plus-log-burner baseline is: gas space heating £2.94/day + gas standing charge £0.35/day + log burner £1.00/day = **£4.29/day**. The heat pump at £3.68/day is £0.61/day cheaper, approximately 14% less expensive. The COP of 4.85 **exceeds** the spark gap of 4.67, so the heat pump already has an advantage on unit energy costs alone. Including the standing charge saving (£0.35/day), the heat pump is advantaged even further.

### Scenario 2 Heat Pump Without Log Burner

Without the log burner, the heat pump must provide the full heating requirement. Based on the heat balance equation (Q_r + Q_b + Q_a = Q_l), removing the log burner means that the total heat delivered Q_l = 1.96 + 0.375 + 0.3 = 2.635 kW (actual measured, including appliance gains) must now come from radiators and appliances, with Q_r = 2.335 kW required from the heat pump. Heat pump operation at maximum flow (20 l/min) requires a flow temperature of 38°C with return temperature ~37°C (ΔT ≈ 1.7 K), delivering 2.335 kW heating power. The estimated COP is 4.56 (at T_o=5°C, T_f=38°C), requiring electrical input of ~0.51 kW for daily electricity consumption of 12.3 kWh and a daily cost of £3.40 at 27.69p/kWh.

For comparison, with Q_r = 2.335 kW, the heat pump now covers what was previously provided by both the gas boiler and the log burner; the current baseline is therefore: gas space heating £2.94/day + standing charge £0.35/day + log burner £1.00/day = **£4.29/day**. The heat pump at £3.40/day is £0.89/day cheaper, approximately 20% less expensive. The COP of 4.56 sits just below the spark gap of 4.67, so on pure unit energy costs the heat pump does not quite break even; a spark gap of 4.56 would be sufficient. Taking the standing charge saving (£0.35/day) and the wood cost no longer incurred (£1.00/day) into account, the effective break-even COP drops to 3.62, which the COP of 4.56 readily exceeds.

### Scenario 3 Heat Pump at Design Temperature

For planning and sizing heat pump capacity, it is standard practice to consider operation at the design outdoor temperature—typically -2°C for Cambridge, UK. At this design condition, the heat loss through the building fabric increases substantially. With h = 188 W/K and ΔT = (19°C - (-2°C)) = 21 K, the total heat loss becomes Q_l = 188 × 21 = 3.948 kW. Subtracting appliance heat gains of Q_a = 0.3 kW, the radiators must deliver Q_r = 3.65 kW (assuming no log burner at design conditions for conservative sizing).

At maximum flow (20 l/min), delivering 3.65 kW requires a flow temperature of ~47°C with return temperature ~43°C (ΔT ≈ 5.3 K). However, the COP at design temperature is significantly degraded by the cold outdoor air: at T_o=-2°C and T_f=47°C, the estimated COP is only 3.32, requiring electrical input of ~1.10 kW for total daily energy consumption of 26.4 kWh and daily electricity cost of £7.31 at 27.69p/kWh.

For comparison with the current gas baseline at design conditions: gas consumption would be 3.65 kW / 0.95 = 3.84 kW gas input, costing (3.84 × 24 × 0.0593) + 0.35 = £5.82/day for space heating alone, plus DHW and standing charge brings the total to approximately £6.25/day. The heat pump at £7.31/day is £1.06/day more expensive, a 17% cost premium. The COP of 3.32 sits well below the spark gap of 4.67. This is clearly visible in the dual-curve COP plot above, where the dashed green line (T_o = -2°C) shows substantially lower COP than the solid green line (T_o = 5°C) at any given power level, emphasising that outdoor temperature lowers the COP independently of the radiator flow temperature.


## Adjusting the Radiator Constant

At this point it is clear that, on unit energy costs alone, the radiators need to be upgraded in order for the COP to exceed the break-even threshold of 4.67 at typical winter conditions, i.e. the constant K needs to be higher, but to what extent? To this end, let's work out the flow temperature and the expected COP plotted over a variable radiator constant K, but for various heating powers: the base load with log burner (1.96 kW at T_o=5°C) and continuous operation without log burner (2.34 kW at T_o=5°C). The intersection with the minimum COP to break even should reveal the required K for each case. (Note, heat pump temperature needs to be 5°C above the radiator flow temperature).

![Performance vs K](assets/performance_vs_k.png)
*Figure: For S1 and S2 at T_o=5°C, the flow temperature (left axis, solid lines) and the expected COP (right axis, dashed lines) plotted over radiator constant K. The circles mark where COP reaches 4.67 (break-even threshold at January 2026 prices). The current K = 71.2 already exceeds the break-even for 1.96 kW (blue, K≈64). To achieve break-even on pure unit energy without the log burner, K must increase to ~76 (green, 1.07× current). All break-even points at T_o=5°C converge to the same flow temperature of 37.1°C.*

With the current K = 71.2, Scenario 1 (1.96 kW with log burner) already **exceeds** the required COP of 4.67, achieving COP = 4.85. Because that COP threshold is set by the spark gap alone, all break-even points for scenarios at T_o = 5°C converge to the same flow temperature of 37.1°C regardless of heating load; reaching that point requires progressively more radiator capacity as the heating load increases. For the 1.96 kW scenario with log burner, the current radiators are already sufficient. For the 2.34 kW scenario without log burner, K ≈ 76.4 W/K^1.2 (1.07× current) is required on pure unit energy — a very modest upgrade.

The picture changes dramatically for Scenario 3 at design temperature. For the 3.65 kW design temperature condition at T_o = -2°C, break-even COP of 4.67 requires a flow temperature of only 29.2°C — the cold outdoor air demands a lower temperature lift to reach the same COP. Delivering 3.65 kW at 29.2°C means a mean radiator temperature of just 27.9°C, barely 9 K above indoor temperature. The required K is approximately 265 W/K^1.2, which is **3.73× the current value**:

![Performance vs K S3](assets/performance_vs_k_s3.png)
*Figure: For S3 (3.65 kW at design temperature T_o = -2°C), flow temperature (left axis, red) and COP (right axis, green) plotted over radiator constant K on a scale extending to 300. The light green solid line shows COP at T_o = 5°C for reference; the dashed line shows COP at -2°C. The break-even marker (K ≈ 265, 3.73× current) sits far to the right, visually demonstrating the absurdity of a purely capital-side solution to a pricing-side problem.*

The S3 plot makes the core message of this article visible at a glance: the large spark gap of 4.67 forces a break-even flow temperature of only 29°C at design conditions, which demands a radiator upgrade that is commercially ridiculous. This is not a thermodynamic barrier — an infinitely large radiator would eventually get there — but it is an economic one. The spark gap is the true driver: a spark gap of roughly 3.3 would raise the break-even flow temperature to the point where no radiator upgrade is needed at all for typical winter conditions. Until energy pricing shifts in that direction, upgrading radiators to achieve unit-energy parity at design temperatures remains uneconomic, regardless of the technology.

# Conclusion

When accounting for the full cost picture, including the gas standing charge saving and elimination of wood burner costs, the heat pump proves cheaper than the current gas-plus-log-burner baseline for typical heating conditions (Scenarios 1 & 2) by 14–20%. However, at the design temperature condition (Scenario 3: -2°C), the heat pump incurs a 17% cost premium (£7.31/day vs £6.25/day). This is important context: such extreme conditions occur rarely in Cambridge (approximately 1% of the heating season), whilst average winter conditions (T_o ≈ 5°C) dominate the seasonal economics where the heat pump maintains its cost advantage.

The extent of radiator upgrades needed depends on whether pure unit energy costs alone need to beat gas, or whether the full cost comparison is used. For average heating loads at typical winter temperatures (5°C), the current radiators are already sufficient. A modest upgrade to K ≈ 76 W/K^1.2 (1.07× current) would enable unit energy parity without the log burner. For design temperature conditions (-2°C), the required K rises to approximately 265 W/K^1.2 (3.73× current)—not a thermodynamic impossibility, but an economic absurdity imposed by the spark gap. It is this pricing gap, not any inherent limitation of heat pump technology, that makes radiator upgrades so disproportionate at cold conditions.

Should energy pricing shift (e.g. a move away from merit order based marginal pricing, or adding energy transition costs to gas rather than onto electricity), the spark gap would drop and required upgrades would become less severe. A spark gap below roughly 3.9 would bring the break-even K for design conditions down to the current radiator capacity. A spark gap below roughly 3.3 would raise the break-even flow temperature high enough that no radiator upgrade would be needed at all even for typical winter conditions, removing this impediment to heat pump adoption entirely.

The situation changes, however, if dynamic operation is considered:

https://peter-wurmsdobler.medium.com/quantitative-analysis-of-dynamic-heat-pump-operation-for-domestic-heating-723cbfb93e13

*Analysis based on: 1930s semi-detached house, Code and methodology available at [github.com/PeterWurmsdobler/heat-pump-cost](https://github.com/PeterWurmsdobler/heat-pump-cost).*

# References

1. **Boiler efficiency:** The Viessmann Vitodens 222-F condensing gas boiler achieves 95% efficiency under typical operating conditions and a rated power of 25kW.

2. **Energy costs** as of January 2026, Ofgem energy price cap for a typical dual-fuel household paying by Direct Debit sets electricity at 27.69p per kWh with a 54.75p daily standing charge, and gas at 5.93p per kWh with a 35.09p daily standing charge. 

