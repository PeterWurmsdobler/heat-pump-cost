
# email to Bosch Home Comfort

Impediments to UK heat-pump adoption: capital expenditure & spark gap (operational expenditure)

For the past few decades UK homes were heated through combi-boilers to some extent; however, a lot of houses still use the combination of system boilers, hot water tanks in airing cupboards, header tanks in the loft, all consuming quite some real estate within a property. Therefore, expectations in the UK are quite low, which is exploited by plumbers who propose in general very complex heat-pump based systems: many devices plumbed up resulting in high labour costs (in addition to component costs). Consequently, heat-pump up-take is very slow, despite a £7.5k boiler upgrade scheme (BUS) grant by the government. Installations are prohibitively expensive (£15-20k), in my experience mostly due to the complexity of the systems on offer: outdoor unit, indoor unit, additional storage tank, expansion vessel(s), pumps, valves, pipes, etc.

Space in UK homes is precious, most houses are small and do not have a basement, let alone a plant room; they need to sacrifice space in the kitchen or utility room for a heating system. In our case, a 1930ies house (like about 3 million UK properties), we have a 60cm x 60xm space in our utility room where currently the Viessman Vitodens 222-F is located (next to a Bosch washing machine and dryer). The best heat-pump solution is a Viessmann 151A all-in-one indoors unit with an external unit, but it is very expensive; it would nearly a drop-in replacement of our boiler. Ideally, I would love to use a Bosch product (next to our other Bosch devices). But it appears, there is none, or in the words of my Cambridge Energy Transition colleagues:

Let's hope and pray that somebody develops such a system beyond just Viessmann - this should be the objective of things like the BUS grant if I understand correctly, as this would make it simpler and thus cheaper for everybody.

My response to the forum was: Bosch could do for heat-pumps what they have done for white goods: design a self-contained, pre-plumbed appliance, scale up production to the levels of fridges; in the end, they employ the same physical principles. Fortunately, there is the Bosch Compress 6800i AW with an internal storage tank. Unfortunately, this model is not available in the UK and, where it is available, nearly prohibitively expensive.
 
## Unleashing the market

At a panel discussion at King's Cambridge organised by the Cambridge University Energy Technology Society (CUETS), one panellist presented the Adia Hub as a response to some major impediments to heat-pump adoption: large capital expenditure due to oversized pumps and unnecessary plumbing work as well as the issue of the spark gap, (electricity price)/(gas price) > COP. The Adia hub installer manual gives some overview, in essence use a smart hub in conjunction with smart valves and sensors to a) reduce or avoid the need for radiator upgrades and plumbing, and b) optimise energy consumption by navigating energy prices and heat demand. Promised outcome: lower installation cost,  lower energy bills, more comfort. That sounds very promising.

In the meanwhile I had a conversation with the CTO of Adia and obtained a better understanding of the operation principle of their solution and their value proposition: a) cut installation time (and cost) down to two days by not needing to upgrade the radiators, only use minimum number of components in addition to a hot water tank and expansion vessel, b) cut operational cost by controlling all radiators and optimising energy expenditure using advanced control systems and taking into account dynamic energy pricing. Their system already works with brands like Ideal, Haier, Samsung, Vaillant and Midea (Riello, Clivet, Airwell); Bosch Compress 2000 seems to be a branded Midea and is also supported. They would be interested in:

adding the Bosch 5800i and 6800i series to their supported devices (comms over Modbus/TCP)
licensing their software stack to a manufacturer such as Bosch and make use of the Bosch hardware in an integrated unit such as the 6800i AW
(instead of manufacturing their own hub as all its bit are already present in the Bosch tower)

I am convinced that the combination of Bosch's ability to produce white goods at large scale and modern software concepts would result in a compelling, cost-effective and highly competitive solution to the benefit of all: sales figures for Bosch, heat-pump adoption in the UK (and elsewhere), and contributing to climate change mitigation.

# email to Sam Duke@adia

Now I see how it works with a "traditional" hot water tank, heating the water from the bottom. Our Viessmann employs a Cylinder Loading System with plate heat exchanger: as soon as hot water is drawn from the top, more hot water is injected into the top and not relying on a heating coil heating up water and rising to the top, eventually. 
 
It appears the Adia hub is communicating to heat pumps over Modbus/TCP; at control.com I implemented such a protocol stack in C, that was in 2001. This requires heat-pumps to be co-operative and operate in "slave" mode I presume which might go against the policy of their suppliers who would like to sell their smart solutions, e.g. Bosch Home Connect. 

Over this weekend I have been reading 2.5 books on Heat pumps, and somehow had a revelation: in order for a heat-pump to work properly with a low temperature high volume flow, having traditional TRVs cannot be good at all. Decent performance can only be obtained by optimising the system which makes individual valve control necessary; otherwise, traditional TRVs would throttle the flow too much once the temperature set-point is reached (which works for a traditional boiler and a bypass). 

# response to Adia criticism

I can understand their view for a stationary system: in a steady state, constant flow volume and temperature, constant outside and inside temperatures, radiators correctly sized for every room, i.e. the heat loss for the room is compensated by the heat imparted to the room by the radiator, no individual sensor, control & actuator would be needed. The entire system is considered as one and moved up and down as one, all rooms in unison. This might cover most houses.

However, if one wanted to run different profiles in different rooms or zones, I do believe that the system has then to be controlled like a multiple-input-multiple-output (MIMO) system using some optimal control or model predictive control techniques. There, TRVs would start beating with the centralised controller that would try to modulate heat delivery through volume at constant temperature and TRVs would constrain and shift flow. 

# posts on cambridge enery transition

I hope to find some advice by this group with regards to a heat pump solution with internal space constraints in a 1930ies house in Cambridge: space in our utility room, 600mm x 600mm footprint, up to 2m tall. For the outside unit, some mono-bloc; there would potentially be enough space. But would it be possible to get an indoor unit with:

    insulated thermal store, perhaps ~D=500mm, H=1200mm, ~200l,
    heating pump, expansion vessel and other bits for radiator circuit,
    plate heat exchanger directly from mains for domestic hot water,
    other bits and bobs to fit into a compact unit.

My thoughts are that an external unit would supply heat to the thermal store and rely on some stratification: 

    for DHW, mains water would be heated up in a plate heat exchanger with water circulated from the top on demand.
    for space heating, a radiator circuit would either circulate water from the lower part, or use a coil inside the thermal store to extract heat.

Perhaps silly questions for specialists: does such a system make sense, or even exist, ideally in a compact appliance like design? If so, what makes are recommended?

--

I can see the issue of the thermal stores having to be 5°C above about 40°C in order to be useful, and a heat pump not being very good at lifting the temperature from 40°C to say 60°C.

In fact, I am not so attached to the idea of a thermal store; rather, the space constraint is important: our utility room has a 600x600x2000 space available where the indoor unit and all its bits can be placed (current location of floor-standing boiler & DHW cyclinder); unfortunately, our house is small, like most UK homes (my family in Austria all have a 20m^2 plant room in the basement of their house).

That said, are you aware of an indoor unit that would meet this space requirement? Many brochures, or project descriptions of videos show people have a few square meters to spare for all the units, expansion vessels, pumps and what not. People I know in Cambridge do not have this kind of space, but then maybe I know the wrong sort of people.

--

thanks for the comprehensive response and suggesting various products. As it happens, I did look into the Viessman Vitocal-151A; I did not realise that the Vitocal-151A is a split unit. I wonder if there is a similar product with a different split: mono-bloc outside, all other bits inside in a single, pre-plumbed unit, ideally all neatly designed in a compact box. Currently, we have a Vitodens-222F (since 2011) and are quite happy with it; but I would like to plan ahead. As you say, knowing our DHW (and space heating demand) will help in the design.

There is one aspect I would be quite keen on: I do not like the idea of "consuming" stagnant water from a tank, Rather I would like a system that heats mains water directly on demand through a heat exchanger and a small thermal buffer (as I am aware that heating up say 10°C mains water to 40°C at a flow rate of 10l/min does require quite some power). I think our Vitodens-222F does do that somehow, of course at a rated 26kW which is far beyond a heat pump for our house.

--

Post scriptum to previous response on Vitocal-151A:

The documentation says: "Compact air/water heat pump with electric drive in mono-block design with outdoor and indoor unit."

From what I can tell of the drawings/diagrams, both condenser and evaporator are on the outside; that makes a mono-block?

Would you mind putting me in contact with your neighbour so I can see how an installation looks like?

--

When we moved into our house in 2011, the heating system was "traditional" in the sense that it comprised a system boiler, hot water tank in the airing cupboard, etc. I reckon that many British households are used to this setup. As a starting point this status quo does make it easy for plumbers to sell an equally convoluted system (in my case I got a quotation for a 7kW heat pump + ancillary for 23k). Fortunately, my plumber at the time recommended the Viessman Vitodens 222-F. Nevertheless, I liked the concept of a self-contained, pre-plumbed appliance and had it installed, which then led me to the Vitocal-151A.

Consumers would be much more likely to adopt heat pumps if these devices had reached the level of maturity like other appliances, in particular since all components needed for a heat pump have been around for a while, compressors, condensers, pumps, etc. I have contacted R&D engineers at my employer Bosch and asked them to do for heat-pumps what they have done for white goods. Design a self-contained, pre-plumbed appliance, scale up production to the levels of fridges; in the end, they employ the same concept. Ideally, I would like to buy and install the pump myself, claiming the BUS grant as an individual, but I think that is not possible; somebody else needs to get a cut.

--

As for the Aira, I learned about that in an ad-feed on my phone (Google knows my search history), but again it is not self contained as you pointed out. The Ad pictures a person sitting in some kind of laundry room, possibly in a x-thousand sq-ft mansion. If in addition to the internal 100/250l tank another external buffer tank (40l/100l) is needed, I wondered if it would be possible to have say a 200l tank and a 50l buffer tank all in one unit, including an expansion vessel.

With regards to water heating at point of use, that is an interesting point; For the kitchen, tap-installed heaters are getting more common, like a Quooker, usually with some energy storage (in most cases water rather than electricity). I am not quite sure how an input/output analysis would fare, in terms of ecological footprint of the system, but I could imagine one could make a case for one or the other in a debating society. 

Instant water heating for showers, that is a different question; yesterday evening, just out of interest, I measured our water mains flow rate: 6.6l/min, or 0.11kg/s, which requires about 18kW for a deltaT of 40°C. Conversely, if all electric power in our house (limited by the 50A mains fuse, i.e. 11.5kW) was made available to a power-shower, we could get about 4l/min, a bit more than a trickle. After years of combi-boilers we are too accustomed to 20-30kW water heaters.

As for space heating with an air-to-air system, I would definitely consider that these days if I started all over again; one could use some heat recovery, manage humidity, and possibly also cool in the increasingly hot summers. The only downside, I do not like drafts; in our office I am always cold because of the constant air flow.
