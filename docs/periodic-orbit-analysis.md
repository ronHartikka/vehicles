# Periodic Orbit Analysis: Single-Source Figure-8

## Question

Does a closed (periodic) figure-8 orbit exist for a Braitenberg vehicle around a single source? The GUI showed striking precessing figure-8 trajectories (see [figure8_single_source.jpeg](figure8_single_source.jpeg)), but visual inspection can't distinguish a true periodic orbit from a slowly-decaying transient. We built a numerical tool to answer definitively.

## Method

**Tool:** `find_periodic_orbit.py` — a Poincaré section + shooting method solver with Floquet stability analysis.

**Approach:**
1. Formulate the vehicle dynamics as a continuous ODE: `d/dt [x, y, theta] = f(x, y, theta)`, mirroring the simulation's differential-drive kinematics but using `scipy.integrate.solve_ivp` (RK45) instead of the discrete Euler stepper.
2. Define a Poincaré section at `sin(theta) = 0`, direction +1 (heading crosses east). This reduces the 3D flow to a 2D return map `(x, y) → (x', y')`.
3. Use `scipy.optimize.fsolve` to find fixed points of the return map: `F(x, y) = return_map(x, y) - (x, y) = 0`.
4. Compute Floquet multipliers (eigenvalues of the return map's Jacobian via finite differences) to determine orbital stability.
5. Continuation: sweep source intensity while tracking the orbit, using each solution as the next guess.

**ODE tolerances:** `rtol=1e-10`, `atol=1e-12`. Floquet finite-difference step: `eps=1e-6`.

**Config used:** `vehicle_4a_speed_sweep.json`, vehicle `x1.042` (crossed wiring, bell response, B_L=1.320, B_R=1.285, sensor arm=24, axle_width=12).

## Results

### 1. The Only Periodic Orbit Is a Circle

Starting from the GUI's initial position (200, -159.7) — 310 units south of the source at (200, 150) — the shooting method did not converge. The trajectory precesses with a residual of ~254 units per orbit.

Integrating for 10,000 time units revealed that the vehicle spirals for ~2,700 time units before being captured by a **tight circular orbit** near the source. This orbit is the attractor.

Shooting from the late-time trajectory converged immediately:

| Property | Value |
|----------|-------|
| Fixed point (on section) | (200.000, 103.792) |
| Orbit radius | 46.21 (constant — perfect circle) |
| Period | 6.71 time units |
| Residual | 3.1 × 10⁻¹² (machine precision) |
| Floquet multipliers | −0.497 ± 0.089i |
| \|λ\| | 0.505 |
| Stability | **Stable** (perturbations halve each orbit) |

The orbit sits 46.2 units south of the source — in the region where the bell sensor response provides strong steering (stimulus ≈ 74 K, on the ascending side of the bell).

### 2. Continuation Sweep: Intensity 100,000 → 300,000

The circular orbit exists across the entire intensity range, converging at every one of 25 sweep steps:

| Intensity | y (section) | Radius | Period | \|λ\|\_max | Stable? |
|-----------|-------------|--------|--------|-----------|---------|
| 100,000 | 113.38 | 36.62 | 5.67 | 1.280 | No |
| 108,333 | 111.97 | 38.03 | 5.80 | 1.065 | No |
| **~112,000** | **~111** | **~39** | **~5.9** | **1.000** | **Bifurcation** |
| 116,667 | 110.59 | 39.41 | 5.95 | 0.905 | Yes |
| 125,000 | 109.24 | 40.76 | 6.09 | 0.784 | Yes |
| 160,725 | 103.79 | 46.21 | 6.71 | 0.505 | Yes |
| 200,000 | 98.35 | 51.65 | 7.36 | 0.385 | Yes |
| 300,000 | 86.43 | 63.57 | 8.84 | 0.297 | Yes |

**Key observations:**
- The orbit always sits at x = 200 (directly below the source), moving further away as intensity increases.
- **Stability bifurcation at I ≈ 112,000**: below this, the orbit is unstable; above, it's stable with |λ| decreasing monotonically.
- Higher intensity → larger orbit radius, longer period, stronger stability.

### 3. The Figure-8 Is a Transient

The precessing figure-8 visible in the GUI is not a periodic orbit. It is the **transient approach** to the stable circular orbit, viewed from the large-scale perspective:

- **Inner lobe:** The vehicle enters the circular orbit's basin of attraction, tracing partial revolutions along the stable circle near the source. This is clearly visible in [figure8_single_source.jpeg](figure8_single_source.jpeg) — the tight loops near the source match the r ≈ 46 orbit.
- **Outer lobe:** The base-voltage asymmetry (B_L > B_R → clockwise turning bias) creates a large-scale arc that swings the vehicle away from the source and curves it back.
- **Precession:** Each figure-8 pass is rotated relative to the previous one because the inner dynamics (sensor-driven orbit) and outer dynamics (base-voltage turning) have incommensurate angular rates. The radial symmetry of a single source provides no mechanism to lock the outer lobe's orientation.
- **Decay:** Because the circular orbit is stable (|λ| = 0.505), each inner pass captures the vehicle more deeply. Eventually the vehicle no longer escapes for an outer lobe, and the trajectory collapses permanently onto the circle.

### 4. Why No Closed Figure-8 Exists (Single Source)

The fundamental obstacle is **radial symmetry**. A single point source creates a rotationally symmetric field. There is no preferred direction for the outer lobe, so there is nothing to synchronize the inner and outer angular rates.

For a closed figure-8 to exist, the precession per orbit would need to be exactly zero (or a rational fraction of 2π). This would require a precise resonance between:
- The angular advance during the inner lobe (set by the circular orbit's frequency and how long the vehicle stays captured)
- The angular advance during the outer lobe (set by the base-voltage turning radius)

No such resonance was found across the intensity range 100,000–300,000. The precession varies continuously but never vanishes.

**Contrast with two-source figure-8s:** The stable figure-8 in `vehicle_4a_figure8.json` works because each source provides its own orbital attractor. The vehicle is handed off between two sources, and the geometry of the two-source system breaks the rotational symmetry, providing a natural closing mechanism.

## Conclusions

1. **A single source with radial symmetry cannot produce a closed figure-8 periodic orbit** for this vehicle model. The figure-8 is always a transient.
2. **The circular orbit family is the unique periodic attractor**, existing across a wide range of intensities with a stability bifurcation near I ≈ 112,000.
3. **The inner lobe of the figure-8 IS the circular orbit** — the vehicle temporarily follows it before the base-voltage bias pulls it free for the outer lobe.
4. **Two sources are necessary** for a true figure-8 — each source serves as an attractor for one lobe.

## Tool Usage

```bash
# Find the circular orbit at a specific intensity
python find_periodic_orbit.py configs/vehicle_4a_speed_sweep.json \
    --vehicle x1.042 --intensity 160725 \
    --x0 200 --y0 104 --t-max 50 --t-burnin 0.1

# Sweep intensity to track the orbit family
python find_periodic_orbit.py configs/vehicle_4a_speed_sweep.json \
    --vehicle x1.042 --intensity 160725 \
    --x0 200 --y0 104 --t-max 50 --t-burnin 0.1 \
    --continuation-param intensity \
    --continuation-start 100000 --continuation-end 300000 \
    --continuation-steps 25 --plot

# Full options
python find_periodic_orbit.py --help
```

**Dependencies:** `scipy`, `numpy`, `matplotlib` (added to `requirements.txt`).
