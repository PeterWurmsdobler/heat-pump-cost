# Considerations for the Fabric First vs Heat Pump First Debate

Heat pumps for homes constitute an important element in the electrification of our economies, and as such, an important contribution to the reduction of greenhouse gases in the combat against climate change. Yet, there seems to be a divide between those who think that any government policy should address the shortcomings in the poorly insulated housing stock first, i.e. insulating the building fabric, e.g. [Insulate Britain](https://insulatebritain.com/), and those who think that adopting heat-pumps is the most important cause, enabled through the [Boiler Upgrade Scheme (BUS)](https://www.gov.uk/apply-boiler-upgrade-scheme). 
In order to understand the debate better, I have been reading a few books on heat pumps. Among them, ["So You're Thinking About a Heat Pump: The UK Homeowner's Guide to Heat Pumps"](https://www.amazon.co.uk/Youre-Thinking-About-Heat-Pump/dp/B0GK7H511K/) was quite helpful in the process as it addressed the Fabric First vs Heat Pump First debate in a well balanced manner. 

The objective of this post is to inform the debate heat-pump first vs fabric first. To me, this debate is not so much a question whether to go with one or the other as if they were mutually exclusive. Rather, it is a question of balance in investment: what combination of measures will have more impact; it boils down to an optimisation problem. To this end, this article presents some quantitative analysis on my own house using estimated heat pump installation and home insulation costs in order to determine an optimal outcome.

## Analysis Scenario

The background to this quantitative analysis is my experience gathered when [Improving the Thermal Performance of UK 1930s Semi Detached Houses](https://peter-wurmsdobler.medium.com/improving-the-thermal-performance-of-uk-1930s-semi-detached-houses-6f64c6514565), an account of a series of improvements made to a 1930s semi-detached house over the past few years, starting with the house in the following state:

- Solid brick walls and walls in some areas only 10cm thick,
- Basic double glazing mostly and single glazing for entrance area,
- Minimal loft insulation (50mm) and no insulation in the eaves.

In this state, the worst case annual heat loss was estimated to be approximately **25,000 kWh/year** for our house in Cambridge, UK; this is quite a lot to modern standards. The required maximum heating power needed to maintain 21°C indoors for the average low temperature in January (2°C outside) was estimated to be **9 kW**! There is lots of scope for thermal performance improvements.


### Home Improvement Options

The following improvements have been considered from the very start; they are sorted by cost-effectiveness (Watts of heat reduction per £ spent) <sup>1</sup>. The heat loss reductions are given at winter conditions (21°C inside, 2°C outside). 

| Improvement | Cost (£) | Heat Loss<br>Reduction (W) | Effectiveness<br>(W/£) |
|-------------|----------|------------------------|------------------------|
| Loft & eaves insulation | £250 | 4,000 | 16.0 |
| Rockwool internal bay window | £100 | 200 | 2.0 |
| Double glazing entrance | £300 | 100 | 0.33 |
| Second layer ground floor | £1,000 | 200 | 0.20 |
| Insulating render front | £1,000 | 200 | 0.20 |
| External wall insulation | £12,000 | 2,000 | 0.17 |
| Triple glazing | £10,000 | 1,000 | 0.10 |

After implementing all improvements except the last two (external wall insulation and triple glazing), the maximum heating power was reduced to **4.3 kW** (which corresponds roughly to the display on my smart meter associated with the current gas boiler); the annual energy consumption has been about **12,000 kWh/year** for the past few years. This gives us an empirical ratio of approximately **2790 kWh/year/kW** (or 2.79 kWh/year/W) for the relationship between the maximum heating power needed and observed (kW) in the coldest period of the year to the annual heat demand required and consumed over the year (kWh/year).

### Heat Pump Options

The heat demand can be met using a heat pump powered by electricity. Then, the so-called **Seasonal Coefficient of Performance (SCOP)**, the ratio of heat output to electricity input, will then determine how much electric energy is needed to produce the same amount of heat; the SCOP can be expected to be around **4.0** for modern air-source heat pumps under UK conditions. The analysis here considers four heat pump sizes, i.e. power ratings or heat capacity in kW (costs are midpoint estimates from industry data) <sup>2</sup>:

| Capacity (kW) | Property Type | Cost (£) |
|---------------|---------------|----------|
| 1.5 | Studio | £5,500 |
| 3.0 | 1-bed flat/Studio | £7,750 |
| 5.0 | 1-2 bed (Small) | £9,000 |
| 10.0 | 3-4 bed (Medium) | £12,000 |

### Optimisation Objective

The optimum balance between heat-pump and fabric investment lies at the minimum of a cost function, here the combined expenditure for heat-pump and fabric improvement. To that end, improvements are conceptually applied in order of cost-effectiveness, ensuring the most efficient measures are implemented first. The total cost for fabric improvement is cumulative, starting in essence with the current state. As the improvement costs increase, the expected heat losses decrease. Then, for every point of fabric improvement and associated thermal performance, an appropriate heat pump is chosen to meet the power requirements; its power-dependent cost is added to the total cost function.

Two different sub-scenarios are examined with respect to capital expenditure for a 25-year lifetime:

1. **No Grant**: Heat pump installation without government support,
2. **With £7,500 Grant**: Heat pump with the UK government's BUS grant.

Both scenarios are analysed in two cases: first, with capital expenditure only, and second, with both capital and operational expenditure over a 25-year lifetime.

## Capital Expenditure Only

When considering only the upfront capital costs of installation, the analysis reveals a consistent optimal strategy across both scenarios.

### Scenario 1: No Government Grant

Without any government support, the optimal approach requires a total capital investment of **£8,859** which consists of:

- **£350** for insulation (loft insulation + rock-wool in bay window, reducing heating power from 9.0 to 4.8 kW),
- **£8,509** for a 4.8 kW heat pump installation.

![Capital costs without government grant](assets/heat_pump_1_no_grant_capital_only.png)

The analysis shows that implementing the two most cost-effective improvements combined with a moderately-sized heat pump represents the most cost-effective solution when considering capital costs alone.

### Scenario 2: With £7,500 Government Grant

The UK government's BUS provides a £7,500 grant towards heat pump installation. With this support, the total capital cost reduces to **£1,359**:

- **£350** for insulation as before, 4.8 kW worst case heat loss,
- **£1,009** for a 4.8 kW heat pump (after £7,500 grant deduction).

![Capital costs with government grant](assets/heat_pump_2_with_grant_capital_only.png)

When considering capital costs alone, the optimal strategy in both scenarios is identical: invest £350 in the two most cost-effective improvements (loft insulation and bay window insulation) to reduce heating power to 4.8 kW. The government grant provides significant immediate cost relief (£7,500 savings), making heat pumps more accessible without changing the underlying optimisation.

## Capital and Operational Expenditure

The analysis changes when operational costs, specifically electricity consumption, are included over the 25-year lifetime of the system. For this analysis, we assume: 

 - the **2790 kWh/year/kW** factor applied to the heat loss to obtain the corresponding expected heat demand,
 - an electricity rate of **£0.15/kWh** which represents a typical domestic electricity tariff in the UK for people running a heat-pump (and make use of some dynamic tariffs such as Octopus Cosy).

### Scenario 1: No Government Grant

Including 25 years of electricity costs at £0.15/kWh yields the total lifecycle cost: **£21,391** with:

- Capital costs: £9,036 (insulation + heat pump),
- Runtime costs: **£12,355** (57.8% of total).

![Total costs without government grant](assets/heat_pump_4_no_grant_with_runtime.png)

The runtime costs now exceed the capital investment, showing that operational expenses significantly impact long-term economics. The optimal heating power shifts to 4.7 kW, just a little bit below the previous 4.8kW and requiring £583 in insulation—loft, bay window, and entrance glazing. Annual electricity consumption at this optimal point is 3,295 kWh, costing £494 per year.

### Scenario 2: With £7,500 Government Grant

With the £7,500 grant and 25 years of operation the total lifecycle cost: **£13,891** including:

- Capital costs: £1,536 (insulation + heat pump after grant),
- Runtime costs: **£12,355** (88.9% of total).

![Total costs with government grant](assets/heat_pump_5_with_grant_with_runtime.png)

The grant reduces capital costs, but runtime costs remain unchanged. Runtime expenses now constitute 89% of total lifecycle costs, emphasising that the grant primarily addresses the upfront barrier rather than long-term economics, similar to the capital cost only case.

## Conclusion

The "fabric first vs heat pump first" debate has a clearer answer when heat pump efficiency is properly accounted for. When focusing solely on capital costs, minimal insulation (£350) combined with a moderately-sized heat pump is optimal, reducing heating power to 4.8 kW. When operational costs are considered over a 25-year lifetime, the optimal strategy remains remarkably similar: £583 in insulation (adding entrance glazing) with heating power of 4.7 kW.

The key insight is that modern heat pumps with SCOP ≈ 4 are sufficiently efficient that electricity costs, while substantial (£494/year or £12,355 over 25 years), do not justify extensive insulation measures like external wall insulation (£12,000) or triple glazing (£10,000). The optimal solution lies in implementing the most cost-effective improvements (loft insulation, bay window, entrance glazing) which provide good thermal performance at modest cost.

With the government grant, runtime costs dominate the total lifecycle cost (89%), yet the grant's £7,500 capital cost reduction has a larger impact on total cost than would be achieved through extreme insulation investment. Current policy effectively addresses both upfront and long-term economics by making heat pumps accessible while their efficiency keeps operational costs manageable.

For a 25-year ownership horizon, the analysis reveals that a balanced "Heat Pump First with Sensible Insulation" approach is optimal. The efficiency of modern heat pumps means that moderate insulation investment (£350-£600) combined with a properly-sized heat pump provides the best economic outcome, whether considering capital costs alone or including 25 years of operation.

---

## Post-Scriptum

Following the publication a few issues where raised:

1. Surprising loft insulation gain and cost. Indeed, £350 for insulation reducing heat loss by nearly 50% could be the headline for a tabloid; but according to my calculations, and subsequent experience, thorough insulation did make a big difference. The previous owner(s) had a one inch thick fleece of some kind between the joists in the loft. I took everything out, hovered all to make the entire loft clean and put down 300mm rock-wool, 100mm between the joists, and 200mm on top. When I changed the fascia & soffit I pushed 50mm rock-wool slabs up the eaves to meet the rock-wool in the loft; I also filled up the space above the back window and all window lintels. It all made the house much warmer, and my modelling showed the change from a U-value of 5.2 W/m²K to 0.1 W/m²K for the top (30m²) and 0.6W/m²K for the eaves (10m²). These areas were the lowest hanging fruit. Of course, the material was £350 and I did not account for my labour as almost everybody can do that.

2. Installation and running cost too low. The prices shown for installation covers the heat-pump proper; of course, at times additional work is required such as adding a hot water tank, upgrading radiators and even pipework, adding a few thousand pounds to the bill. As far as running costs are concerned, from people here in Cambridge I gathered that 15p for was an achievable average with some smart control; of course the average price depends on the electricity contract and usage pattern. All would increase the total cost proportional to the power rating. However, please observe that the insulation cost curve is a 1/x^y, or a hockey stick, with a strong kink caused by the considerable reduction through loft insulation, little gains for other bits, but high costs for external wall insulation and triple glazing. The heat-pump cost is nearly linear with a small slope. Consequently the minimum of the combined curve is nearly invariant to the total cost of the heat-pump, with or without running costs: minimum insulation with the maximum effect, then get a heat pump.

*Analysis based on: 1930s semi-detached house, Code and methodology available at [github.com/PeterWurmsdobler/heat-pump-cost](https://github.com/PeterWurmsdobler/heat-pump-cost).*