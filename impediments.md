# Impediments to UK heat-pump Adoption and Possible Solutions

Heat pumps for homes constitute an important element in the electrification of our economies, and as such, an important contribution to the reduction of greenhouse gases in the combat against climate change. Yet, there are two main impediments to their adoption: capital expenditure and the "spark gap". The latter refers to the ratio of electricity to gas price which is quite often larger than the Coefficient of Performance (COP) obtained with a heat-pump; as a result the operational costs for a heat-pump through electricity are higher than heating on gas. The former refers to prohibitive upfront costs of a heat pump system installation due to oversized pumps, unnecessary plumbing and related work and is the focus of this article.


## Historic Context in the UK

At some point in the past the transition to gas heating happened with a standard central heating system installation in a UK home consisting of a system boiler, at times installed into the builders opening of the chimney breast as "back boiler", a hot water tank in the airing cupboard (often in the 1st floor), both a header tank and a cold water storage tank in the loft, as well as pipework (varying diameters from 8mm, 10mm to 15mm to radiators), single panel radiators and other paraphanelia distributed over the house. The power rating of the gas boiler would have been about 10kW as the hot water storage was used as a thermal buffer and people used to take baths. Those who had showers used a power shower to boost the presssure, but still with hot water tank supply, or an electric shower.

Then came the transition to the combi-boiler, idealy of the condensing kind that sports very good efficiency; this boiler would operate the central heating system and produce domestic hot water at the same time. Incorporating a circulation pump, it could simply be installed instead of the system boiler and made all header tanks as well as the hot water tank superfluous. The combi-boiler power rating was and is mostly determined by the larger of two numbers: the space heating and the domestic hot water demand. It is usually the second one that determines the result: flow rate * delta T * thermal capacity of water yields for a 10l/min flow, a delta T from 5deC to 40degC  something like 10/60 kg/s * 35K * 4.18kJ/kg/K = 24.5kW. 

The current state of affairs is that there is a range of installations: XXX% homes still using the traditional system, XXX% use a modern condensing boiler with integrated hot water tank, and XXX% of UK homes using a condensing combi-boiler. The latter may have even installed or updated more modern radiators, or even made sure that the pipes to the radiators are 15mm, but quite often repurposed the space where the hot water tank used to be to something useful. If one wanted to move on to a heat-pump and maintain the habit of taking showers (with their implicit power demand), one would either need a heat-pump at an industrial rating of 20kW+, or one has to bring back the hot water tank.

## Costs of a Real Installation

The capital expenditure for a heat pump installation extends well beyond the outdoor unit typically featured in marketing materials. While the outdoor unit itself costs £3,000-£8,000 depending on capacity, a complete installation requires numerous additional components, extensive plumbing work, and substantial labour. Total installation costs in the UK typically range from £15,000 to £25,000, even after accounting for the £7,500 Boiler Upgrade Scheme (BUS) grant. A typical heat pump system installation includes:

**Core Heat Pump Components:**
- Outdoor unit (air-source heat pump): £3,000-£8,000
- Indoor unit/controls: £500-£1,500

**Hot Water System:**
- Hot water cylinder (insulated thermal store, 200-300L): £800-£2,000
- Expansion vessel (heating circuit): £150-£300
- Secondary expansion vessel (DHW circuit, if separate): £100-£200

**Hydraulic Components:**
- Circulation pump(s) for radiator circuit: £200-£400
- Diverter valves (3-way or 4-way): £150-£400
- Buffer tank (optional, for system stability): £400-£800
- Pressure relief valves: £50-£100
- Fill and drain valves: £30-£80

**Pipework and Insulation:**
- Pipe upgrades to 15mm diameter for adequate flow: £500-£1,500
- Pipe insulation: £200-£500
- Refrigerant lines (split systems): £300-£600
- Condensate drain: £100-£200

**Controls and Sensors:**
- Smart thermostat/controller: £200-£500
- Flow and return sensors: £100-£300
- Outdoor temperature sensor: £50-£100
- DHW cylinder sensors: £50-£150

**Electrical Work:**
- Dedicated circuit upgrades (typically 32A): £300-£800
- Wiring and consumer unit modifications: £200-£500

**Labour and Installation:**
- Design and heat loss calculations: £300-£800
- Installation labour (2-5 days, multiple tradespeople): £3,000-£8,000
- Commissioning and testing: £300-£600
- Building control notifications: £100-£300

**Total typical cost: £15,000-£25,000** (before BUS grant)

This complexity represents a significant barrier to adoption. Many consumers are accustomed to traditional heating configurations involving system boilers, header tanks, and hot water cylinders that occupy considerable space. Installers often propose similarly elaborate systems, resulting in high labour costs that remain prohibitive despite government subsidies.


## Commoditisation of Heat Pumps

Modern combi-boilers replaced complex multi-component heating systems with single integrated appliances, reducing both installation time and costs. A similar transition for heat pumps through standardisation and component integration could follow this trajectory. A standardised heat pump system would require five basic connections:

- Mains water input (for DHW),
- Mains electricity input with power supply to external unit,
- Flow/return connections to heating system (radiators and/or underfloor),
- Flow/return connections to external unit (mono-bloc configuration),
- Hot water output (DHW).

### Examples of Integrated Systems

Several manufacturers have developed systems approaching this integration:

**Viessmann Vitocal 151-A:** A split system combining an outdoor mono-bloc unit with an indoor unit containing integrated hot water cylinder, circulation pump, expansion vessel, controls, and ancillary components in a pre-plumbed package. The footprint is comparable to a floor-standing boiler such as the Vitodens 222-F, making it nearly a drop-in replacement.

**Bosch Compress 6800i AW:** Incorporates an integrated internal storage tank in a compact design. However, this model is not currently available in the UK market.

### Potential Benefits of Integration

Integrated system design could reduce installation complexity through:
- Factory assembly and testing of hydraulic components,
- Standardised footprint dimensions (approximately 60cm × 60cm × 200cm),
- Pre-plumbed configurations reducing on-site labour,
- Modular designs for different DHW capacities.

This approach could potentially reduce:
- Installation time from 3-5 days to 1-2 days,
- Labour costs through fewer trades required,
- Component costs through volume manufacturing,
- System complexity with fewer connection points.

Current installations cost £15,000-£25,000. With integrated appliances and simplified installation procedures, total costs might reduce to £8,000-£12,000 (including installation), though this assumes achieving manufacturing economies of scale comparable to white goods. 

## Radiator Compatibility and Control Systems

Radiator replacement constitutes a significant cost in heat pump installations. Heat pumps operate at lower flow temperatures (35-45°C) compared to gas boilers (60-80°C), and installers commonly recommend upgrading to larger, double-panel radiators in order to transmit the same amount of heat. However, advanced control systems offer an alternative approach that may reduce or eliminate this requirement.

### The Adia Hub Approach

There happens to be a system by UK company [Adia Thermal](https://adiathermal.co.uk/); the Adia Hub system provides one method for managing existing radiator infrastructure through intelligent control rather than hardware replacement. The system comprises:

- Smart thermostatic valves on each radiator,
- Room temperature sensors throughout the home,
- Central controller implementing optimisation algorithms,
- Heat pump integration via Modbus/TCP communication.

This configuration enables the system to maximise flow volume by fully opening valves when heat is needed, operate at lower temperatures with extended run times, balance heat delivery dynamically across rooms, and optimise energy consumption based on variable electricity pricing.

Reported benefits include:
- Reduced installation time from 5 days to 2 days,
- Elimination of most radiator replacements (saving £2,000-£5,000)
- Minimal additional components beyond DHW cylinder and expansion vessel,
- Compatibility with multiple heat pump brands (Ideal, Haier, Samsung, Vaillant, Midea, Bosch Compress 2000).

### Control System Challenges

Traditional Thermostatic Radiator Valves (TRVs) present operational challenges with heat pumps. TRVs were designed for high-temperature gas boiler systems with bypass circuits. When a TRV closes to limit room temperature, it restricts flow, which conflicts with the heat pump's requirement for constant high-volume, low-temperature circulation. Both central heat-pump control and TRVs will start beating each other resulting in oscillations and poor performance. Modern control systems address this through:

- **MIMO control** (Multiple-Input Multiple-Output) treating the home as an interconnected thermal environment
- **Predictive algorithms** incorporating weather forecasts and occupancy patterns
- **Zone management** allowing different temperature profiles without flow restriction
- **Weather compensation** adjusting flow temperature based on outdoor conditions

### Implementation Considerations

The Adia Hub currently interfaces with several heat pump manufacturers through standardised Modbus/TCP communication. Extension to additional brands, or direct integration of their or similar control logic into manufacturer systems, could broaden adoption; Traditional suppliers are usually very good mass manufacturing pumps and components and have less experience in modern software development.

An alternative perspective maintains that in properly designed systems—with correctly sized radiators, constant flow parameters, and stable conditions—individual valve control may be unnecessary. Such systems can be modulated centrally with all zones responding uniformly. This approach works well for properties with consistent occupancy and heating requirements.

For properties with variable occupancy patterns or differential zone heating needs, distributed intelligent control offers additional functionality. The critical consideration is avoiding operational conflicts between local TRVs and centralised heat pump controllers—either through elimination of local control or through coordinated intelligent management.


## Integrated System Configuration

An integrated heat pump system suitable for UK residential properties would combine hardware simplicity with intelligent control:

### Hardware Configuration

**Outdoor Unit:**
- Mono-bloc air-source heat pump with all refrigerant components contained,
- Weatherproof construction with acoustic output below 45 dB,
- Capacity matched to building requirements (typically 3-10 kW).

**Indoor Unit** (60cm × 60cm footprint, up to 2m tall):
- Integrated insulated hot water cylinder (200-250L),
- Plate heat exchanger for instantaneous DHW from mains,
- Circulation pump for heating circuit,
- Expansion vessels for heating and DHW circuits,
- Diverter valves for heating/DHW priority management,
- Pre-assembled and tested hydraulic components,
- Integrated controls and communication interfaces.

**Standard Connections:**
- Single electrical connection (32A dedicated circuit),
- Mains cold water input,
- Hot water output (DHW),
- Heating flow and return (2 pipes),
- Connection to outdoor unit (2 insulated pipes).

This configuration occupies space equivalent to a floor-standing combi-boiler or washing machine, compatible with typical UK homes without basements or plant rooms.

### Control Options

Once the hardware has been commoditised by companies that have experience in making white goods, the added value and differentiation lies mostly in the control system:

**Integrated Smart Controller:**
- Weather compensation
- Time-of-use tariff optimisation
- DHW scheduling with legionella protection
- Self-learning algorithms for occupancy patterns
- Remote monitoring and control capability

**Smart Zone Management:**
- Wireless smart radiator valves in all rooms
- Room temperature sensors
- Hub controller for MIMO optimisation
- Heat pump integration via standard protocols (Modbus/TCP)
- Dynamic flow balancing
- Multi-zone temperature profiles

### Installation and Economics

Installation could proceed over two days: removal of existing boiler, positioning of indoor and outdoor units, and pipe connections on day one; electrical work, commissioning, and control installation on day two.

Estimated costs with this approach:
- Equipment: £5,000-£8,000 (assuming mass production)
- Installation: £2,000-£3,000 (simplified 2-day procedure)
- Total: £7,000-£11,000
- After £7,500 BUS grant: £0-£3,500 net cost

These figures assume achievement of manufacturing economies of scale and adoption of simplified installation procedures. Implementation would require coordination among manufacturers for integration and production scaling, standards bodies for communication protocol definition, policy makers for appropriate incentive structures, and installers for streamlined deployment methods.







