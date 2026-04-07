# Thermal Parameter Identification for the Dynamic House Model

This document describes the system-identification approach used to estimate the unknown
parameters of the first-order dynamic thermal model of the house from recorded indoor
temperature data.  The results feed directly into the dynamic heating simulations in
`operations-dynamic.md`.

---

## 1. The Model

The house is represented by a linear, first-order ordinary differential equation:

```
C · dT_i/dt = -h · (T_i - T_o(t)) + Q_b + Q_r(t)
```

| Symbol | Meaning | Unit |
|--------|---------|------|
| T_i | Indoor temperature | °C |
| T_o | Outdoor temperature (known, time-varying) | °C |
| C | Thermal capacity of the house | J/K |
| h | Heat Transfer Coefficient (HTC) | W/K |
| Q_b | Background heat (appliances, occupancy) | W |
| Q_r | Radiator heat input (controlled) | W |

The ODE is the simplest plausible lumped-parameter description: a single thermal mass *C*
losing heat through the building fabric at rate *h*, with two heat sources — a known
radiator input *Q_r* and a small background *Q_b*.

Two parameters had prior estimates from earlier analysis:
- **h = 188 W/K** from recorded electricity consumption
- **h = 244 W/K** from a first-principles heat-loss calculation

The thermal capacity **C was completely unknown**.

---

## 2. Experimental Design

Three time windows were selected from the temperature logs to provide complementary
information:

| Period | File | Start | End | T_o | Q_r |
|--------|------|-------|-----|-----|-----|
| 1 – Passive cooling | `temperatures-1.csv` | 2026-04-04 01:00 | 2026-04-04 06:00 | 7 °C (constant) | 0 W |
| 2 – Passive cooling | `temperatures-2.csv` | 2026-04-05 22:45 | 2026-04-06 04:20 | 3 °C (constant) | 0 W |
| 3 – Forced heating  | `temperatures-2.csv` | 2026-04-06 06:30 | 2026-04-06 08:15 | 3 → 7 °C (ramp) | 6 000 W |

The outdoor temperature in Period 3 rises linearly from 3 °C to 7 °C over the 1 h 45 min
window; this is modelled as a linear ramp function *T_o(t)*.

**Why three periods?**  
Periods 1 and 2 are passive-decay experiments: with *Q_r = 0* the ODE simplifies to

```
C · dT_i/dt = -h · (T_i - T_o) + Q_b
```

The asymptote of the decay constrains the equilibrium `T_eq = T_o + Q_b/h`, so the two
cooling windows together pin down *Q_b/h*.  The *rate* of decay constrains the time
constant τ = C/h.  Period 3 adds a nonzero *Q_r*, which lifts *T_i* and provides an
additional constraint with a different signal character.

---

## 3. Identifiability

With only passive cooling data, the time constant **τ = C/h ≈ 44 h** is tightly
identified, but *C* and *h* individually are not separable from temperature data alone —
any (C, h) pair with the same ratio τ fits equally well.  Period 3 provides a weak
additional constraint (the heating ramp inflects the trajectory), but the main resolution
of the *C/h* ambiguity comes from the **prior on h**.  This is by design: the prior
encodes the physical knowledge obtained from the earlier analyses and the approach is
formally a MAP (Maximum A Posteriori) estimate.

---

## 4. Estimation Method

The parameters θ = (C, h, Q_b) are estimated by minimising the following cost function:

```
J(θ) = Σ_k  MSE_k(θ)  +  ((h - h_prior) / σ_h)²  +  ((Q_b - Q_b_prior) / σ_Q_b)²
```

where the sum runs over the three experimental segments and MSE_k is the mean squared
residual between the simulated and measured *T_i* in segment *k*.  The two penalty terms
are soft Gaussian priors that regularise toward the physically motivated prior values.

**Default priors:**

| Parameter | Prior mean | Prior σ | Rationale |
|-----------|-----------|---------|-----------|
| h | 188 W/K | 56 W/K | Recorded consumption estimate; σ spans the full 188–244 W/K range |
| Q_b | 500 W | 300 W | Rough appliance/occupancy estimate |

**ODE integration**: each residual evaluation numerically integrates the full ODE with
[`scipy.integrate.solve_ivp`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html)
(RK45, relative tolerance 1e-6), initialised from the measured first sample of each
segment.  This means the prediction faithfully reflects the nonlinear (in *C*, *h*)
dynamics from the observed starting temperature.

**Optimisation**: the decision variable is (log C, h, Q_b) — using log C ensures C
remains positive for any unbounded update step.  Multi-start L-BFGS-B is run from seven
different initialisations to guard against local minima.

---

## 5. Results

With the default h prior (188 W/K):

| Parameter | Estimated value |
|-----------|----------------|
| C | **29.9 MJ/K** |
| h | **188 W/K** |
| Q_b | **~500 W** |
| τ = C/h | **44.1 h** |

Per-segment RMSE (all within sensor noise):

| Period | RMSE |
|--------|------|
| Period 1 – Cooling, T_o=7°C | 0.18 °C |
| Period 2 – Cooling, T_o=3°C | 0.09 °C |
| Period 3 – Heating on       | 0.11 °C |

The long time constant of **44 hours** means the house temperature changes slowly and
each 5–6 h window captures only a fraction of the full exponential; the trajectory looks
nearly linear over these windows, which is why the per-segment fits are so tight.

The estimated C = 30 MJ/K is physically plausible: a 130 m² brick/cavity-wall house with
concrete floors, internal partitions and thermal mass in the fabric can easily accumulate
30–50 MJ/K.

With the alternative prior (h = 244 W/K, σ = 30 W/K) the optimiser converges to
C ≈ 39 MJ/K, h ≈ 244 W/K, with τ ≈ 44.6 h — the time constant barely changes, as
expected from the identifiability analysis.

![Three-period identification plot](assets/temperature_plot.png)
*Figure: Measured indoor temperature (blue) and model prediction (orange dashed) for all
three experimental periods.  The vertical axis is T_i in °C; the horizontal axis is
elapsed time in hours from the start of each period.*

---

## 6. Running the Identification

The identification is implemented in
`src/heat_pump_cost/identify_thermal_parameters.py` and exposed through the
`heat-pump-identify` CLI entry point.

```bash
# Default run (h prior = 188 W/K, saves to assets/temperature_plot.png)
heat-pump-identify

# Use the first-principles prior
heat-pump-identify --h-prior 244 --h-sigma 30

# Change the assumed radiator power in Period 3
heat-pump-identify --q-r 5500

# Show the plot interactively
heat-pump-identify --show

# Specify output path
heat-pump-identify --output assets/my_identification.png
```

All parameters can also be changed by editing the `DEFAULT_SEGMENTS_SPEC` list in
`identify_thermal_parameters.py`, which defines the CSV files, time windows, outdoor
temperatures, and heat inputs for each experimental period.
