# Accepting the Need for Radiator Upgrades with a Heat Pump Installation 

Motivated by the desire to transition away from heating with gas and reduce CO2 emissions I have been reading up on heat pumps and their installation. Various sources such as ["So You're Thinking About a Heat Pump: The UK Homeowner's Guide to Heat Pumps"](https://www.amazon.co.uk/Youre-Thinking-About-Heat-Pump/dp/B0GK7H511K/) or [The Ultimate Guide to Heat Pumps: Britain's best installers and experts tell you exactly what to watch for and what to ask](https://www.amazon.co.uk/Ultimate-Guide-Heat-Pumps-installers/dp/B0FNMNVC4Q) recommend radiator upgrades which do unfortunately increase installation costs. Initially, I hoped to avoid such an upgrade by using a heat pump in tandem with our log burner. In order to be able to make a more informed decision, however, I have carried out a simple analysis using steady-state thermal models. The outcome presented in this post confirms expert advice and made me accept the need for radiator upgrades: the physical relationship between radiator capacity, flow temperature, and heat pump efficiency creates constraints for achieving acceptable operating economics. Note, that this story focuses on order-of-magnitude estimates rather than precise scientific calculations.

# Static Analysis and Heat Loss

The starting point of this analysis is the state of our property after the efforts detailed in [Improving the Thermal Performance of UK 1930s Semi Detached Houses](https://peter-wurmsdobler.medium.com/improving-the-thermal-performance-of-uk-1930s-semi-detached-houses-6f64c6514565). Therein the heat transfer model derived from first principles estimates the specific heat loss, or Heat Transfer Coefficient (HTC), to be **244 W/K**. In order to work out a representative heat loss of the building, I chose a cold winter month in Cambridge, UK: the bleak January 2026 with an average outdoor temperature T_o = 5°C; the indoor temperature was kept on average at T_i = 19°C (approximately 20°C downstairs, about 18°C upstairs). The resulting temperature difference is ΔT = 14K and yields an heat loss of Q_l = 244 × 14 = **3.42 kW**.

To validate this estimate, I looked up our energy consumption for January 2026: over that period electricity consumption was 263.75kWh (8.5kWh/day on average or 0.35kW continuous power), and gas utilisation was 1,924.91kWh (62.1 kWh/day on average or 2.59kW continuous power); the latter includes space heating and domestic hot water (DHC). It is assumed that energy for DHC stays mostly the same throughout the year and is responsible for the gas use in summer; for instance, in summer 2025 gas usage was about 12.5 kWh per day on average. As mentioned before, we have been using a log burner as supplemental heat source, providing approximately 3 kW output for 3 hours daily which contributes 9 kWh/day as heat (0.375 kW average power). In total our log burner consumes about 1m^3 per year of locally sourced hard wood (partly from neigbours).

After subtracting assumed DHC (12.5 kWh/day) from total gas consumption (62.1 kWh/day), the remaining 49.6 kWh/day of gas provides 47.12 kWh/day of actual heat to the radiators at 95% boiler efficiency(^1), i.e. 1.96 kW average power. Since most of electricity is eventually dissipated as heat, e.g. from appliances, it will add about 0.3 kW as a heating equivalent. All combined, the total average heating power is 2.635 kW (radiators 1.96 kW + log burner 0.375 kW + appliances 0.3 kW), which is 77% of the estimated heat loss from the thermal model (3.42 kW). This discrepancy is a bit more than I expected but also reasonable, considering unaccounted solar gain and internal heat gains from occupants, as well as the fact that not all rooms are maintained at 19°C continuously (heating off from 10pm to 5am, and entrance hall more like 15°C). 

## Stationary Model of a House

The model used here assumes a simple lumped-mass representation of the house with the following parameters: internal thermal capacity or mass C, insulated envelope with heat transfer coefficient h, internal temperature T_i, and outside temperature T_o. Heat is supplied as Q_h through a flow rate V_f at flow temperature T_f and return temperature T_r. Heat is transferred to the internal thermal mass as Q_r through radiators with a characteristic constant K and radiative exponent n. Supplemental heat Q_b is provided by a log burner, and Q_a from appliances. The house loses heat as Q_l through the building fabric.

![Simle termal model for house](assets/house-model.png)
*Figure: Simple representation of a simple house model with heat sources and losses.*

The individual heat contributions can be written using heating fluid (water) density ρ and its specific thermal capacity c_p as:

Q_h = V_f * ρ * c_p * (T_f - T_r)<br>
Q_r = K * ((T_f + T_r)/2 - T_i)^n<br>
Q_l = h * (T_i - T_o)

In an equilibrium, or steady state as a stationary process, the heat balance for the radiator circuit (no losses in short pipework), is Q_h = Q_r, and for the room thermal balance, Q_r + Q_b + Q_a = Q_l; the balance is invariant to the thermal mass C. Overall, the radiator system must deliver:

Q_r = Q_l - Q_b - Q_a = h * (T_i - T_o) - Q_b - Q_a

This simplified model treats all radiators as a single unit, assuming uniform flow and return temperatures throughout a well-balanced system. The characteristic constant K represents the combined heat transfer capacity of all radiators, i.e. all their surfaces and types, plus the heating contribution from pipework distributed throughout the house. For the January 2026 conditions, the theoretical heat loss is Q_l = 3.42 kW, the log burner contributes Q_b = 0.375 kW (average), appliances contribute Q_a = 0.3 kW, giving a required radiator output of Q_r = 2.745 kW (theoretical). The radiator output obtained from the gas bill was Q_r = 1.96 kW, with total heat delivered of 2.635 kW.

## Empirical Validation

To validate the model, on one hand I used the operating conditions from January 2026 with an average radiator heating power of 1.96 kW. On the other, The installed radiators comprise single panel with single convector (Type 11) with dimensions 0.6×0.5 m, 1.0×0.5 m, 1.2×0.5 m, 0.5×0.6 m, and two 0.4×1.8 m panels totalling A = 3.14 m², and double panel with double convector (Type 22) with dimensions 0.6×0.5 m and 1.2×0.5 m totalling A = 0.9 m². Heat transfer coefficients based on typical radiator performance data are U ≈ 8 W/m²/K^1.2 for Type 11 radiators and U ≈ 12 W/m²/K^1.2 for Type 22 radiators. The resulting radiator constant K = 35.9 W/K^1.2.

Using the radiator equation Q_r = K × ΔT^1.2 and Q_r = 1.96 kW gives 1960 W = 35.9 W/K^1.2 × ΔT^1.2, i.e. ΔT required works out to be 28.5K. ΔT now depends on both the indoor temperature 19°C and the mean radiator temperature which depends on the flow rate and flow temperature; here we assume about 10 l/min which results in a mean radiator temperature of approximately 47.5°C (flow ~50°C, return ~45°C). I haven't got a temperature probe on the flow pipes, but the radiators "felt" very warm but not hot and it was bearable to touch them, which means the flow temperature is about 40ish °C. In addition, the boilers displayed a "boiler" temperature in the same range.

## Operating Constraints

With our empirically validated radiator constant (K = 35.9 W/K^1.2), we can now explore the fundamental relationship between flow rate and flow temperature for delivering heating power. Using constants for water as the working fluid (ρ = 1 kg/l and c_p = 4.18 kJ/kg/K), with the January 2026 average conditions (T_o = 5°C and T_i = 19°C), and radiator exponent n = 1.2, there are multiple combinations of flow temperature T_f and flow rate V_f that can deliver the same heating power.

![Contour Plot](assets/operations_contour.png)
*Figure: Contour plot showing constant heating power curves. The 1.96 kW average radiator heating power is highlighted in red. This curve represents the operational constraint imposed by the current radiator capacity.*

For a given radiator constant K = 35.9 W/K^1.2, any target heating power defines a specific curve on this plot. The current radiators confine operation to the red 1.96 kW curve, which demonstrates the fundamental trade-off: low flow operation (~0.6 l/min) requires 70°C flow temperature with large temperature drop to the return temerpature (ΔT ≈ 33K) as well as a large temperature difference to the room temperature (ΔT ≈ 51K), whilst high flow operation (~20 l/min) requires only 47°C flow temperature with small temperature drop to the return temerpature (ΔT ≈ 1.5K) as well as a small temperature difference to the room temperature (ΔT ≈ 27K). 

# The Radiator Constant Impact

The countour plot shows well that for a given radiator constant K and flow temperature the delivered heating power converges to a constant with increasing flow rate; in other words, there is a limit to how much power can be delivered over existing radiators which is reached when the difference between radiator flow and return temperature goes to zero as the flow rate to infinity. Most pumps will struggle to reach that as fluid dynamics will affect resistance and pumping power; so practically, we stay with a maximum flow rate below 20l/min.

## Performance over Power

Suppose we set the flow rate at 20l/min for the rest of analysis. Then the heat delivered becomes a function of the flow temperature, and so does the COP. It is perhaps revealing to show the required flow temperature T_f as a function of heat delivered P_r in our current setup (K = 35.9 W/K^1.2), then also show the achievable COP for that power, bearing in mind that the heat pump needs to run at about 5°C above the radiator flow temperature since heat needs to be transferred from the internal heat pump circuit to the radiator circuit. 

*Figure: For a given radiator constant K the flow temperature (left) and the expected COP (right) plotted over heat power delivered; the constant COP = 3.6 is break even with the spark gap.*

### Scenario 1 Heat Pump Without Log Burner

If the gas boiler is replaced with a heat pump whilst continuing to use the log burner for supplemental heat, the heat balance remains with radiators delivering Q_r = 1.96 kW, log burner providing Q_b = 0.375 kW, appliances contributing Q_a = 0.3 kW, and total heat Q_l = 2.635 kW (including internal gains). High flow operation optimised for the heat pump at 20 l/min requires a flow temperature of 47°C with return temperature ~46°C (ΔT ≈ 1.4K), delivering 1.96 kW heating power. The estimated COP is 3.0 (at T_o=5°C, T_f=47°C), requiring electrical input of ~0.65 kW for daily electricity consumption of 15.7 kWh and daily cost of £3.93 at 25p/kWh. 

With the log burner continuing to provide supplemental heat and appliances contributing internal gains, the heat pump operates at the edge of sensible performance with 47°C temperature. Daily operating cost (£3.93) is 13% higher than gas (£3.47), making this scenario more expensive despite achieving fossil fuel independence. This is partly due to the flow temperature still being a bit on the high side, and consequently the COP below the spark gap.

## Scenario 2 Heat Pump Without Log Burner

Without the log burner, the heat pump must provide the full heating requirement. Based on the heat balance equation (Q_r + Q_b + Q_a = Q_l), removing the log burner means that the total heat delivered Q_l = 1.96 + 0.375 + 0.3 = 2.635 kW (actual measured, including appliance gains) must now come from radiators and appliances, with Q_r = 2.335 kW required from the heat pump. 

Heat pump operation at maximum flow (20 l/min) requires a flow temperature of 52°C with return temperature ~50°C (ΔT ≈ 2K) to deliver 2.335 kW heating power. The estimated COP is 2.85 (at T_o=5°C, T_f=52°C), requiring electrical input of ~0.82 kW for daily electricity consumption of 19.7 kWh and daily cost of £4.93 at 25p/kWh. The operating cost is thus 42% higher than the gas+log burner configuration (£3.47/day).

The constraint is exacerbated during peak conditions. For a conservative design representing the theoretical full load during the coldest conditions, appliances contribute Q_a = 0.3 kW, leaving the heat pump to deliver 3.42 - 0.3 = 3.12 kW. At maximum flow (20 l/min), this requires a flow temperature of ~65°C with COP dropping to 2.45 and daily cost of £7.65. This worst-case scenario confirms the need for radiator upgrades: attempting to deliver peak heating loads with insufficient radiator capacity forces operation into low-COP, high-cost area.


## Adjusting the Radiator Constant

At this point it is clear that radiators need to be upgraded, i.e. the constant K needs to be higher, but to waht extent? To this end, let's work out the flow temperature and the expected COP plotted over a variable radiator constant K, but for various heating power, the base load with log burner (1.96kW), one without log burner (2.335 kW) and the worst case (3.12 kW). The intersection with the minimum COP to break even should reveal the required K for each case. (Note, heat pump temperature needs to be 5°C above the radiator flow temperature).

*Figure: For a series of heating power Q_r, the flow temperature and the expected COP plotted over radiator constant K.*

The conclusion is that a radiator upgrade to K ≈ XXX W/K^1.2, XXX W/K^1.2 and XXX W/K^1.2 would alleviate the problem for the three cases, 1.96kW, 2.335 kW and 3.12 kW, respectively. In other terms, an increase of a factor X, Y and Z would be required, The upgrade transforms both the economics and the practical viability of heat pump operation without supplemental heating.

# Conclusion

Current radiators cannot support economically viable heat pump operation even with supplemental heating, as costs exceed gas heating in all scenarios. The recommended upgrade specification is: K value of XXX W/K^1.2 (approximately YYY× current capacity), achieved by replacing existing radiators with larger Type 22 panels, adding additional radiators in key rooms, or upgrading to Type 33 (triple panel) in limited spaces. This would enable delivery of the 3.12 kW peak load at 45°C (accounting for 0.3 kW appliance contribution to reach theoretical 3.42 kW total). Generally speaking, radiator upgrades are not merely recommended but absolutely essential to achieve acceptable operating costs that make the technology transition economically viable.


# References

1. **Boiler efficiency:** The Viessmann Vitodens 222-F condensing gas boiler achieves 95% efficiency under typical operating conditions.

2. **Energy costs** as of January 2026: Natural gas at 7p/kWh and electricity assumed at 25p/kWh for heat pump analysis as an obtainable price depending on the tariff; a "spark gap" of 25/7 or 3.6.

