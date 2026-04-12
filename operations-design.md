# Quantitative Analysis of Dynamic Heat Pump Operation for Design Temperature

The preceding story, [Quantitative Analysis of Dynamic Heat Pump Operation for Domestic Heating](https://medium.com/@peter-wurmsdobler/quantitative-analysis-of-dynamic-heat-pump-operation-for-domestic-heating-723cbfb93e13), highlights the importance of the operation of a heat pump in terms of heating schedule in order to keep the flow temperature low, COP high and cost low. There, a cold winter months with an outside average temperature of 5 C is used, which to a certain degree is quite representative for the coldest season in Cambridge UK. This story investigates the heating system operation for the design temperature for the same location, -2C, and presents the cost comparison between heating with gas, or a heat pump with current radiators, or after an upgrade.

![Cat prefers consistent heat](assets/smooth-operator.png)
*Figure: Our cat would probably prefer the smooth operation of a heating system with a heat pump.*

# Smooth Heating Alone

Let's use the same target temperature profile and controller as in the previous story. The heat source operates continuously with varying power levels, maintaining baseline heating to prevent excessive temperature drops, and keeping flow temperatures low. The controller uses predictive logic with a 3-hour lookahead to pre-heat smoothly before comfort periods with realistic temperature targets:

- **Night (22:00–06:00)**: Maintain ~17°C with baseline XXX heating  
- **Morning (06:00–09:00)**: Achieve 19°C comfort with ramped power  
- **Day (09:00–17:00)**: Maintain ~17°C with baseline XXX heating  
- **Evening (17:00–22:00)**: Achieve 19°C comfort with ramped power

Assuming an outside temperature of -2C, an optimal heating power profile can be calculated for one day independently on how the heat was being produced. The total amount of heat required for one day would be XXX kWh. If a gas boiler was used to supply that heat at 95% efficiency, it would cost £XXX/day, including the gas standing charge.

![Heating at Design Temperature](assets/design_heating_profile.png)
*Figure: Heating power profile (right) and resulting indoor temperature (left).*

## Heat Pump With Current Radiators

Using the current radiators, the flow temperatures can be calculated as well as the resulting COP. Given the electricity flat fee of 27p/kWh, the cost of heating with a heat pump would be £XXX/day, which is high because the COP for these design temperatures is quite low, and the spark gap is quite high. Conversely, if the spark gap was XXX, the heat pump would break even even without a radiator upgrade.

![Flow Temperature and COP at Design Temperature](assets/design_flow_temperature_cop.png)
*Figure: Flow Temperature (left) and COP (right) at design temperature.*


## Heat Pump With Upgraded Radiators

Using the upgraded radiators, K = XXX, the flow temperatures can be calculated as well as the resulting COP. Given the electricity flat fee of 27p/kWh, the cost of heating with a heat pump would be £XXX/day, .... Conversely, if the spark gap was XXX, the heat pump would break even even without a radiator upgrade.

![Flow Temperature and COP at Design Temperature with radiator upgrade](assets/design_flow_temperature_cop_upgrade.png)
*Figure: Flow Temperature (left) and COP (right) at design temperature with radiator upgrade.*


# Smooth Heating With Interruptions

The previous simulations assume that the heat pump is being used for space heating alone; most heat pumps also need to provide power for domestic hot water which requires about 2 hours per day. There is another factor to be taken into account in colder areas: defrost cycles. Periodically, the heat pump switches into reverse mode to melt ice build-up on the outdoor heat exchanger coil. Let's assume about 5 minutes every hour, so nearly 10% of the time.

Now, let's take these times into account in our control algorithm: work out a heating schedule that maintains the temperature as defined above, but in addition make sure that we have hot water in the morning (for showers), and in the evening (washing up and shower). We accommodate through a one hour DHW operation in the morning, so water is hot by 7am, and one in the evening, again for water to be hot by 7pm.

Assuming an outside temperature of -2C, an optimal heating power profile can be calculated for one day independently on how the heat was being produced. The total amount of heat required for one day would be XXX kWh. If a gas boiler was used to supply that heat at 95% efficiency, it would cost £XXX/day, including the gas standing charge. 

![Heating at Design Temperature with gaps](assets/design_heating_profile_with_gaps.png)
*Figure: Heating power profile (right) and resulting indoor temperature (left), with gaps.*

If a heat pump is used to produce DHW at say 55C, the flow temperature has to be the around 60C; the resulting COP and an outside temperature of -2C is XXX. To produce the 11.6 kWh of thermal energy for hot water would require XXX kWh elecyricity, which sets the daily DHC cost.

## Heat Pump With Current Radiators

Using the current radiators, the flow temperatures can be calculated as well as the resulting COP. Given the electricity flat fee of 27p/kWh, the cost of heating with a heat pump would be £XXX/day, .... Conversely, if the spark gap was XXX, the heat pump would break even even without a radiator upgrade.

![Flow Temperature and COP at Design Temperature with gaps](assets/design_flow_temperature_cop_gaps.png)
*Figure: Flow Temperature (left) and COP (right) at design temperature, with gaps.*

## Heat Pump With Upgraded Radiators

Using the upgrades radiators, the flow temperatures can be calculated as well as the resulting COP. Given the electricity flat fee of 27p/kWh, the cost of heating with a heat pump would be £XXX/day, .... Conversely, if the spark gap was XXX, the heat pump would break even even without a radiator upgrade.

![Flow Temperature and COP at Design Temperature with gaps and radiator upgrade](assets/design_flow_temperature_cop_upgrade.png)
*Figure: Flow Temperature (left) and COP (right) at design temperature with gaps and radiator upgrade.*

# Conclusion

The situation has changed a bit; without upgrade and taking the hot water into account, the average COP is XXX and a heat pump would break even at a spark gap of XXX. With a radiator upgrade, the break even spark gap would be XXX.

The difference in cost per day at design temperatures between using current radiators and upgraded radiators is about £/day. The Upgrade would cost me about £2000 in materials and labour (a bit tricky rerouting of pipes), which translates into XXX days. Assuming about 10 of such days per year, this means the investment is returns in XXX years. Perhaps I'll pass on that as for the majority of cold days we should be fine with current radiators, even at the current spark gap.


*Analysis conducted on a 1930s semi-detached house. Code and methodology available at [github.com/PeterWurmsdobler/heat-pump-cost](https://github.com/PeterWurmsdobler/heat-pump-cost).*


# References

1. **Boiler efficiency:** The Viessmann Vitodens 222-F condensing gas boiler achieves 95% efficiency under typical operating conditions and a rated power of 25kW; radiator constant K = XXX W/K^1.2 (from manufacturer specifications, see [Radiator Upgrade](https://github.com/PeterWurmsdobler/heat-pump-cost/blob/main/radiator-survey.md)).

2. **Energy costs**: as of January 2026, Ofgem energy price cap for a typical dual-fuel household paying by Direct Debit sets electricity at 27.69p per kWh with a 54.75p daily standing charge, and gas at 5.93p per kWh with a 35.09p daily standing charge. 
