# Quantitative Analysis of Dynamic Heat Pump Operation for Design Temperature

The preceding story, [Quantitative Analysis of Dynamic Heat Pump Operation for Domestic Heating](https://medium.com/@peter-wurmsdobler/quantitative-analysis-of-dynamic-heat-pump-operation-for-domestic-heating-723cbfb93e13), highlights the importance of the operation of a heat pump in terms of heating schedule in order to keep the flow temperature low, COP high and cost low. There, a cold winter month with an outside average temperature of 5°C is used, which to a certain degree is quite representative for the coldest season in Cambridge, UK. This story investigates the heating system operation for the design temperature for the same location, −2°C, and presents the cost comparison between heating with gas, or a heat pump with current radiators, or after an upgrade.

![Cat prefers consistent heat](assets/smooth-operator-cold.png)
*Figure: Our cat would probably prefer the smooth operation of a heating system with a heat pump in particular if it's cold outside.*

# Heat Pump for Heating Only

For this analysis, we use a feedforward planner that optimises a 24-hour heating schedule to meet a target temperature profile: an average of 19°C (20°C living areas, 18°C bedrooms, cooler hallway). The optimiser balances two objectives: achieving comfort quickly when needed while minimising flow temperatures to maximise efficiency. It computes hourly power levels that:

- **Pre-heat before comfort periods**: Ramp up power 2 hours before morning (06:00) and evening (17:00) schedules to reach 19°C smoothly, with peak power around 5.5–6 kW,
- **Maintain comfort efficiently**: Once 19°C is achieved, reduce power to ~3 kW to hold temperature,
- **Setback periods (night/day)**: Deliver steady baseline heating at ~2 kW to maintain ~17°C without excessive temperature drops.

This approach is exemplary and many other optimisation strategies are conceivable, in particular with feedback and dynamic weather compensation: model predictive control, rule-based schedulers, or machine learning planners could achieve similar results. It's all software, ultimately, and the physics of thermal inertia favours a combination of model-based feedback and feed-forward control strategy.

Assuming an outside temperature of −2°C, the total space heat required for one day is 59.0 kWh. If a gas boiler were used to supply that heat at 95% efficiency(^1), it would cost £4.03/day, including the gas standing charge.

![Heating at Design Temperature](assets/design_heating_profile.png)
*Figure: Heating power profile (right) and resulting indoor temperature (left).*

## Heat Pump With Current Radiators

Using the current radiators, K = 71.2 W/K^1.2, the necessary flow temperatures can be calculated as well as the resulting COP (see [COP estimation](https://github.com/PeterWurmsdobler/heat-pump-cost/blob/main/cop-estimation.md)). At 27.69p/kWh, the cost of space heating with a heat pump is £4.45/day, exceeding the gas baseline of £4.03/day because the achievable SCOP of 3.67 falls below the current spark gap of 4.67. Conversely, a spark gap of 3.67 would allow the heat pump to break even without a radiator upgrade.

![Flow Temperature and COP at Design Temperature](assets/design_flow_temperature_cop.png)
*Figure: Flow Temperature (left) and COP (right) at design temperature.*


## Heat Pump With Upgraded Radiators

In a second survey for our house I have worked out how radiators could easily be upgraded and to what extent, details in [Radiator Upgrades](https://github.com/PeterWurmsdobler/heat-pump-cost/blob/main/radiator-upgrade.md).
Using the upgraded radiators, K = 93.5 W/K^1.2, the required flow temperatures can again be calculated as well as the resulting COP. At 27.69p/kWh, the cost of space heating with a heat pump is £4.11/day, close to the gas baseline of £4.03/day. The SCOP of 3.97 approaches the current spark gap of 4.67; similarly, a spark gap of 3.97 would allow the heat pump to break even with the radiator upgrade.

![Flow Temperature and COP at Design Temperature with radiator upgrade](assets/design_flow_temperature_cop_upgrade.png)
*Figure: Flow Temperature (left) and COP (right) at design temperature with radiator upgrade.*


# Heating With Interruptions

The previous simulations assume that the heat pump is being used for space heating alone; most heat pumps also need to provide power for domestic hot water (DHW) generation, which requires about 2 hours per day, depending on the power rating and amount of hot water needed. There is another factor to be taken into account at the negative design temperature: defrost cycles. Periodically, the heat pump switches into reverse mode to melt ice build-up on the outdoor heat exchanger coil. Let's assume about 10 minutes every hour, so about 17% of the time.

Taking these times into account in our control algorithm needs to work out a heating schedule that maintains the temperature as defined above, but in addition make sure that we have hot water in the morning (for showers), and in the evening (washing up and shower). We accommodate this through four short DHW slots: a 40-minute pre-heat at 04:00–04:40 charges the cylinder before the morning routine, with a 20-minute top-up at 07:00–07:20 to maintain hot water availability throughout the morning. The same pattern is repeated for the afternoon: a 40-minute pre-heat at 15:00–15:40 and a 20-minute top-up at 18:00–18:20 cover the evening. A well-insulated hot water cylinder loses only a few degrees over several hours, so staggering the pre-heat and top-up in this way provides reliable hot water while keeping each space-heating interruption short.

Assuming an outside temperature of −2°C, the space heat delivered in the available hours (excluding DHW slots and defrost downtime) is 58.7 kWh/day. If a gas boiler were used to supply that heat at 95% efficiency, it would cost £4.01/day, including the gas standing charge. Note that only space heating costs are compared in this section; domestic hot water costs will be covered separately.

![Heating at Design Temperature with gaps](assets/design_heating_profile_with_gaps.png)
*Figure: Heating power profile (right) and resulting indoor temperature (left), with gaps.*


## Heat Pump With Current Radiators

Using the current radiators, K = 71.2 W/K^1.2, the necessary flow temperatures can be calculated as well as the resulting COP. At 27.69p/kWh, the cost of space heating with a heat pump is £4.96/day (space heating only), compared to the gas baseline of £4.01/day. The space heating SCOP of 3.27 sets the break-even spark gap; a spark gap of 3.27 would allow the heat pump to break even without a radiator upgrade.

![Flow Temperature and COP at Design Temperature with gaps](assets/design_flow_temperature_cop_gaps.png)
*Figure: Flow Temperature (left) and COP (right) at design temperature, with gaps.*

## Heat Pump With Upgraded Radiators

Using the upgraded radiators, K = 93.5 W/K^1.2, the new flow temperatures can again be calculated as well as the resulting COP. At 27.69p/kWh, the cost of space heating with a heat pump is £4.54/day (space heating only), close to the gas baseline of £4.01/day. The space heating SCOP of 3.58 sets the break-even spark gap; again, a spark gap of 3.58 would allow the heat pump to break even with the radiator upgrade.

![Flow Temperature and COP at Design Temperature with gaps and radiator upgrade](assets/design_flow_temperature_cop_gaps_upgrade.png)
*Figure: Flow Temperature (left) and COP (right) at design temperature with gaps and radiator upgrade.*

# Conclusion

At design temperature (−2°C), the heat pump costs more to run than a gas boiler regardless of whether the radiators are upgraded. Without an upgrade, the space heating SCOP is 3.27; with upgraded radiators it improves to 3.58. Both fall below the current spark gap of 4.67, which means the heat pump cannot break even on unit energy costs alone at these extreme conditions. The radiator upgrade closes the gap (SCOP 3.27 → 3.58) but does not change the outcome. Conversely, the spark gap only needs to fall to 3.27 to make the current radiator setup break even, not an outrageous number in comparison to European countries. As renewables are being built out in the UK, gas price will set the electricity price less often (about 90% currently), and consequently, the spark gap will decrease and approach 3 or less in due course(^3).

For now, the difference in space heating cost at design temperature conditions (including DHW and defrost interruptions) between current and upgraded radiators is £0.42/day. The upgrade according to my recent survey would cost about £2000 at least, in materials and labour (rerouting pipes is involved), which translates into about 4,760 design-temperature days to recover the investment. At roughly 12 such days per year (according to the Cambridge Botanic Garden station), recovery takes about 397 years, so quite a long time. In contrast, during the more typical cold winter months (T_o = 5°C), smooth heat pump operation with the current radiators already costs £1.96/day against a gas baseline of £2.42/day, 19% cheaper. All conditions combined, the seasonal economics remain in favour of the heat pump without any radiator upgrade.

A second lesson from the simulation with interruptions is that despite the average power needed to heat the home at an outside temperature of −2°C being about 3.65 kW as shown in [How the Spark Gap Drives Radiator Upgrades for Heat Pump Installations](https://medium.com/@peter-wurmsdobler/how-the-spark-gap-drives-radiator-upgrades-for-heat-pump-installations-1d3b098b29fd), it needs about 6 kW to allow flexibility and interruptions due to domestic hot water generation and defrost cycles, so about twice the average rating at design temperature. That's worth noting.

*Analysis conducted on a 1930s semi-detached house. Code and methodology available at [github.com/PeterWurmsdobler/heat-pump-cost](https://github.com/PeterWurmsdobler/heat-pump-cost).*


# References

1. **Boiler efficiency:** The Viessmann Vitodens 222-F condensing gas boiler achieves 95% efficiency under typical operating conditions and a rated power of 25kW; radiator constant K = 93.5 W/K^1.2 (from manufacturer specifications, see [Radiator Upgrade](https://github.com/PeterWurmsdobler/heat-pump-cost/blob/main/radiator-upgrade.md)).

2. **Energy costs**: as of January 2026, Ofgem energy price cap for a typical dual-fuel household paying by Direct Debit sets electricity at 27.69p per kWh with a 54.75p daily standing charge, and gas at 5.93p per kWh with a 35.09p daily standing charge. 

3. **Lower Spark gap**: Admittedly, there is some wishful thinking here as in theory, once gas falls off the marginal pricing's merit order (gas not needed any more), only renewables would determine the price. However, since renewables cannot fill every slot due to the intermittency of wind and solar, batteries and overbuild are needed, i.e. more capital expenditure. So as the build out increases, the overbuild factor goes up and the utilisation factor goes down: so the price must go up. In other words, water-wind-solar are cheap as long as they can sell every kWh when they only cover a fraction of the demand; the price will change to something proportional to the overbuild factor once renewables cover 100% of the demand, which I would hope will still be below 3 times that of gas.
