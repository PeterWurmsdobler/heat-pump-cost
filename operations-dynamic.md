# Simple Quantitative Analysis of Dynamic Heat Pump Operation for Domestic Heating

The preceding story, [How the Spark Gap Drives Radiator Upgrades for Heat Pump Installations ](https://medium.com/@peter-wurmsdobler/how-the-spark-gap-drives-radiator-upgrades-for-heat-pump-installations-1d3b098b29fd), addresses the implications of the spark gap on capital and operational expenses due to a nearly unavoidable upgrade in radiator capacity in order to keep the flow temperature low and the [Coefficient of Performance](https://en.wikipedia.org/wiki/Coefficient_of_performance) (COP) high; there a simple static thermal analysis looks at average quantities for heat loss and temperature for a heat pump in a stationary operation. The situation changes if dynamic aspects are taken into account for the operation of the heat pump in contrast to the gas boiler operation most homes are used to, both in terms of setpoint temperature profiles and electricity tariffs. As presented in sources such as ["So You're Thinking About a Heat Pump: The UK Homeowner's Guide to Heat Pumps"](https://www.amazon.co.uk/Youre-Thinking-About-Heat-Pump/dp/B0GK7H511K/), heat pumps require different operating strategies compared to gas boilers. The objective of this story is to demonstrate quantitatively how control and operation strategy impacts the economics of domestic heat pump heating. 

# Dynamic Modelling

A stationary model assumes all process variables to be constant at a given point of operation: for a constant outdoor temperature a constant heating power is required to maintain a constant indoor temperature by compensating a constant heat loss. While this static analysis can provide some insight in minimum requirements for heating at various operation points, a dynamic analysis is looking at time-variant process variables such as heating power or flow temperature. To that end a dynamic model of the system is required first.

## Dynamic Thermal Model

A dynamic model reflects the time-variant behaviour of a system. Here, I would like to use the simplest conceivable model, a linear first order model with two time-invariant parameters: the thermal capacity C of the entire house, and the specific heat loss, or Heat Transfer Coefficient (HTC), or h. The following process variables will be considered: internal temperature T_i, and outside temperature T_o; heat is supplied as Q_h at flow temperature T_f and return temperature T_r, then transferred to the internal thermal mass as Q_r through radiators. The house loses heat as Q_l through the building fabric determined by h.

![Simple dynamic thermal model for house](assets/house-model-dynamic.png)
*Figure: Simple representation of a simple dynamic house model with heat source, capacity and losses.*

Most commonly differential equations are used to describe dynamic systems. The following equations define the behaviour, using heating fluid (water) density ρ, its specific thermal capacity c_p and a flow rate V_f, the characteristic radiator constant K and radiative exponent n, and finally the transfer coefficient h, all together:

Q_h = V_f * ρ * c_p * (T_f - T_r)<br>
Q_r = K * ((T_f + T_r)/2 - T_i)^n<br>
Q_l = h * (T_i - T_o)<br>
C * dT_i/dt = Q_r - Q_l

[How the Spark Gap Drives Radiator Upgrades for Heat Pump Installations ](https://medium.com/@peter-wurmsdobler/how-the-spark-gap-drives-radiator-upgrades-for-heat-pump-installations-1d3b098b29fd) has identified the values of some parameters for the dynamic analysis: h = 244 W/K; K = 4.9 W/K^1.2, ρ = 1 kg/l and c_p = 4.18 kJ/kg/K, V_f is assumed to be constant at 20 l/s for this analysis; heat power is only modulated through the flow temperature. Also note, the heat balance for the radiator circuit (no losses in short pipework), is Q_h = Q_r. There is only one parameter missing: C, the house's thermal capacity.

## Model Parameter Identification

Modelling a thermal system as a lumped mass at a certain heat capacity C and an estiamted heat loss coefficient lends itself to a very simple experiment: let the system cool down on its own over night through its thermal loss and without any added heat, work out the time constant, then estimate the thermal mass C. Since the outside temperature is not quite constant, however, the system parameter identification gets a git more complicated, but not too much. Given the model above, with no heating power, the equations degenerate to:

C * dT_i/dt = -h * (T_i - T_o)

If we can measure the inside and outdoor temperature once the heating has stopped late in the evening, we can plot those in a graph, and employ some system identification mathematics to work out the parameter C of the dynamic system. It works out to be C = XXX Js/K. The following plot shows the measure outside temperature, measured inside temperature and estimated inside temperature based on the model.

GRAPH: plot of T_o, T_i and T_i_est.

# Dynamic Heating Simulation

Since we now have got a parameterised dynamic model, it should be possible to work out the heating requirments, and eventually the cost of heating. For this story, let's assume the January 2026 conditions with an average outdoor temperature T_o = 5°C. Without any other heat sources, the the heating requirement in a steady state would be XXX W to maintain an average of 19°C indoors, i.e. Q_l = Q_r = 244 × 14 = **3.42 kW**, or ~82kWh/day, to give a ballpark figure for the heating requirements. But this story is about dynamics.

## Gas Boiler Space Heating

Let's assume a traditional daily heating profile as pictured below using a gas boiler with a maximum rate power of 12kW: heating off after 22h, heating on at 6h in the morning with a setpoint of T_s = 19°C and at full capacity, off at 9h when we leave the house but keep the house over as T_s = 15°C, on again at 17pm until 22h with T_s = 19°C. The simplisitic relay-based controller would do the following:

- if T_i < T_s, then full wack when on until target temperature of T_s is reached; 
- feed-forward heating power at constant T_s with Q_h = h * (T_s - T_o);
- if T_i > T_s, then no heating required at all, let the temperature decay; 

GRAPH: profiles of T_i, T_s, and P on the right

The gas boiler would not struggle to produce the required power and deliver the heat through the necesary flow temperature through the existing radiators. Realising this temperature profile using a gas boiler would cost us £/day, XXX hours on full power at 12kW, i.e. XXX kWh delivered at XXX p/kWh yields £ XXX.

GRAPH: profiles of T_f, COP on the right

## Equivalent Heat Pump Variant

Let's assume we got an equivalent and very powerful heat pump installed: 12kW peak power. Now, let's run the heat pump to deliever the same power, which would lead to the same flow and return temperatures at the same flow rate. Then let's look at the COP and the resulting electricity consumption. XXX hours on full power at 12kW heat, divided by the COP at the time, all together yields XXX kWh in electricity. At a constant cost of XXX p/kWh, this would cost £ XXX. This is what you get it you run a heat pump like a gas boiler on a flat tariff.

GRAPH: profiles of T_f, COP on the right


## Smooth Operator Heat Pump

Let's assume we use a heat pump at say twice the average power, 6kW. Then let's devise a controller that tries to meet the heating requirements in a more laid back way: start heating a bit earlier, don't let the house cool down too much, smooth operation.

GRAPH: profiles of T_i, T_s, and P on the right

Then let's look at the COP and the resulting electricity consumption. XXX hours on full power at 12kW heat, divided by the COP at the time, all together yields XXX kWh in electricity. At a constant cost of XXX p/kWh, this would cost £ XXX. 

GRAPH: profiles of T_f, COP on the right

There is already one major lessons from the previous simulation: do not run a heat pump as if it was a gas boiler.

## Playing the Dynamic Tarrifs

Suppose electricity does not incur the same cost, not a flat rate, but a dynamic rate such as Octopus Cosy.

GRAPH: example for tariffs

If we now combine the desired indoor temperature and the knowledge of the cost of electicity, as well as the dynamic model of the system, some clever optimal control algorithm could work out the heating profile for one day ahead that minimises the heating cost. 

GRAPH: profiles of T_i, T_s, and P on the right

Then let's look at the COP and the resulting electricity consumption. XXX hours on full power at 12kW heat, divided by the COP at the time, all together yields XXX kWh in electricity. At a constant cost of XXX p/kWh at the time of use, this would cost £ XXX. 

GRAPH: profiles of T_f, COP on the right


There is another major lessons from the previous simulation: optimise the system.


## Contingencies

These simulations only assume that the heat pump is being used for space heating; most heat pumps also need to provide power for domestic hot water. Given the thermal capacity of water (4.18kJ/kg/K), a few people taking showers at a certain flow rate either needs a powerful heat pump, order of 20kW-30kW, or a hot water tank that is being heated gradually when time and cost permits. This periods are not available for space heating. For instance, XXX l/day, at a power rating of XXX kW, requires about XXX hours for hot water generation.

There is another factor to be taken into account in colder areas: defrost cycles. Periodically, the heat pump switches into reverse mode to make sure the pipework does not freeze up.

# Conclusion

Depending on profile, SCOP can be higher or lower, cost can be higher or lower: Adia Thermal?

