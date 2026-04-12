# Quantitative Analysis of Heat Pump Operation for Domestic Hot Water

The preceding story, [Quantitative Analysis of Dynamic Heat Pump Operation for Design Temperature](), looks at the heat pump operation for a design temperature of -2C; it already sets aside some time during the day needed for domestic hot water (DHW) preparation using the same heat pump. This story focuses on DHC only and tries to assess the economic side of DHC using a single heat pump (DHC and space heating).

IMAGE

Most heat pumps have to be rated for both space heating at a design temperature and domestic hotwater at an expected daily use. For instance, an average shower takes about 8 minutes which consumes about 48l of hot water at about 45°C at a flow rate of 6l/min. Given the thermal capacity of water (4.18 kJ/kg/K), this requires either a powerful heat pump (of the order of 20–30 kW which is similar to a gas boiler), or a hot water tank that is heated gradually when time and cost permit; these periods are not available for space heating. For instance, heating 200 l/day of water from 10°C to 55°C requires XXX kWh of thermal energy; at a heat pump power rating of 6 kW, this requires about XXX hours for hot water generation. 

## Daily Cost of DHW

Work out cost of hot water at 55°C as a function of outside temperature and COP through spark gap. Reference is cost of gas heated water at 95% efficiency which is £XXX.

![Hot water cost](assets/hot_water_cost_.png)
*Figure: Cost of hot water as a function of outside temperature and spark gap.*


## Annual Cost of DHW

Look at outside temperatures in Cambridge over the year, assumption of average temperatures and 200l hot water per day. With gas (energy and standing charge) this would cost about £XXX. Using a heat pump at current electricity costs, this would be £XXX/year.

![Hot water cost](assets/hot_water_cost_daily.png)
*Figure: Cost of hot water as a function of outside temperature and spark gap.*



# Conclusion

Over the year, we get an average COP of XXX; hence a spark gap of XXX and we'll break even.


*Analysis conducted on a 1930s semi-detached house. Code and methodology available at [github.com/PeterWurmsdobler/heat-pump-cost](https://github.com/PeterWurmsdobler/heat-pump-cost).*


# References

1. **Boiler efficiency:** The Viessmann Vitodens 222-F condensing gas boiler achieves 95% efficiency under typical operating conditions and a rated power of 25kW.

2. **Energy costs**: as of January 2026, Ofgem energy price cap for a typical dual-fuel household paying by Direct Debit sets electricity at 27.69p per kWh with a 54.75p daily standing charge, and gas at 5.93p per kWh with a 35.09p daily standing charge. 
