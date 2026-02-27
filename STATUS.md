# Braitenberg Vehicles Simulator - Status

## Current Status

Vehicles 2 and 3 implemented and tested. All four classic Braitenberg behaviors (fear, aggression, love, explorer) working via config files. GUI functional with playback controls, pan/zoom, trails, field overlay, and live vehicle diagnostics.

## What We've Done

1. ✅ Domain model specification (sensors, fields, sources, vehicles, connections)
2. ✅ Sensor specification (voltage-based signal chain: stimulus -> V -> motor)
3. ✅ Vehicle 2 behavior specification (differential drive, ipsilateral/contralateral wiring)
4. ✅ Main loop specification (fixed dt, Euler and arc integration methods)
5. ✅ GUI specification (pygame, config file driven, unbounded world with camera)
6. ✅ Simulation engine (`vehicles/` package - pure Python, no pygame dependency)
   - `model.py` - Domain dataclasses
   - `fields.py` - Source falloff with interior linear transition (no point sources)
   - `sensors.py` - Response functions (linear, threshold, sigmoid, logarithmic, inverse, bell, triangular)
   - `simulation.py` - Main loop step with differential drive kinematics
   - `config_loader.py` - JSON config loading
7. ✅ GUI (`gui/` package)
   - `camera.py` - World-to-screen transforms with pan/zoom
   - `renderer.py` - Sources, vehicles, trails, field overlay, field contours, figure-8 guide
   - `app.py` - Pygame event loop, keyboard/mouse controls, status bar, info panel
8. ✅ Vehicle configs created and tested:

### Vehicle 2 Configs (excitatory connections)

| File | Vehicle Name | Wiring | Response | Behavior |
|------|-------------|--------|----------|----------|
| `vehicle_2a_fear.json` | fearful-1 | uncrossed | linear | Fear |
| `vehicle_2a_1_fear.json` | fearful-1 | uncrossed | linear | Fear (closer start) |
| `vehicle_2b_aggression.json` | aggressive-1 | crossed | linear | Aggression |

### Vehicle 3 Configs (inhibitory connections via inverse response)

| File | Vehicle Name | Wiring | Response | Behavior |
|------|-------------|--------|----------|----------|
| `vehicle_3a_love.json` | love-1 | uncrossed | inverse | Love |
| `vehicle_3b_explorer.json` | explorer-1 | crossed | inverse | Explorer |

### Vehicle 3C Configs (true inhibition via base_voltage)

| File | Vehicle Name | Description |
|------|-------------|-------------|
| `vehicle_3c_love.json` | love-1 | Single temp source, base_voltage=10 (symmetric), uncrossed inhibitory (-1.0 weights). Demonstrates true inhibition. |

### Vehicle 3C "Values" Configs (4 sensor types)

These configs implement Braitenberg's "Vehicle with Values" - a vehicle with 4 different sensor types, each with different wiring patterns:

| Stimulus | Wiring | Weight | Behavior | Color |
|----------|--------|--------|----------|-------|
| Light (lux) | uncrossed | +1.0 | Fear | Yellow |
| Temperature (K) | uncrossed | -1.0 | Love | Red |
| Oxygen (kPa) | crossed | -1.0 | Explorer | Blue |
| Organic (ppm) | crossed | +1.0 | Aggression | Green |

| File | Position | Heading | Base Voltages | Notes |
|------|----------|---------|---------------|-------|
| `vehicle_3c_values.json` | (0, 120) | 0 | 15/15 | Reference config, all sources at 40000 |
| `vehicle_3c_values_blue.json` | (120, 120) | 0 | 15/15 | Temp source moved near light source |
| `vehicle_3c_values_green.json` | (0, 100) | 1.0 | 15/15 | Different start angle |
| `vehicle_3c_values_yellow.json` | (80, 120) | -0.15 | 65/65 | High base voltage, asymmetric organic wiring (0/1.0), max_speed=180 |
| `vehicle_3c_values_red.json` | (150, 180) | 0 | 25/15 | **Asymmetric base voltages** - produces curved path |

### Orbiting Configs (asymmetric base_voltage discovery)

Discovery: Asymmetric base voltages (ML=25, MR=15) create stable orbital behavior around sources. The vehicle naturally curves due to the differential in base speeds, and the Fear response to light creates a stable attractor orbit.

| File | Heading | Intensities | Notes |
|------|---------|-------------|-------|
| `vehicle_3c_values_orbits_yellow_1.json` | 0 | All 40000 | Orbit around yellow (light) source |
| `vehicle_3c_values_orbits_yellow_2.json` | 1 | All 40000 | Different initial heading, same orbit |
| `vehicle_3c_values_orbits_yellow_3.json` | 2 | All 40000 | Different initial heading, same orbit |
| `vehicle_3c_values_orbits_yellow_4.json` | 2 | Light=1600000, others=0 | **Only light source active at high intensity. Orbit radius scales with intensity!** |

Key findings:
- Orbit radius increases with source intensity
- Orbits are stable attractors - vehicle converges to same orbit from different initial headings
- The asymmetric base_voltage creates a natural turning bias that, combined with the Fear response, produces circular motion

9. ✅ Headless verification: Vehicle 2a veers away from heat source as expected
10. ✅ GUI tested interactively: all four behaviors confirmed visually
11. ✅ Vehicle 3C with base_voltage enables true inhibition (negative weights reduce motor input from a positive baseline)
12. ✅ Vehicle 3C "Values" with 4 sensor types demonstrates emergent behavior from competing drives
13. ✅ Discovered orbital behavior with asymmetric base_voltages - orbit radius scales with source intensity
14. ✅ Vehicle 4a: bell-curve sensor response (peak_stimulus, max_voltage). Vehicle orbits where equal-angular-velocity condition is met for both wheels. See [docs/orbit-analysis.md](docs/orbit-analysis.md).
15. ✅ Field contour overlay (C key): draws labeled iso-stimulus circles around single-source fields. Supports inverse-square and inverse-linear falloff. Contour levels: 25, 50, 100, 150, 200, 400.
16. ✅ Orbit radius derivation: the orbit condition yields a degree-8 polynomial — no closed-form solution. Graphical analysis confirms two crossings for Vehicle 4a (R≈42.7 and R≈50.9). The observed orbit at stimulus≈200 matches the inner solution. See [docs/orbit-analysis.md](docs/orbit-analysis.md) and [docs/orbit_condition_4a.png](docs/orbit_condition_4a.png).
17. ✅ Confirmed outer orbit (R≈50.9) is unstable: two-vehicle test (`vehicle_4a_both_orbits_try.json`) shows both inner and outer starting positions converge to the same inner orbit at R≈42.7. Stability is visible in the angular velocity plot: at the stable crossing (R≈42.7) the two curves have opposite slopes (scissor crossing — perturbations reverse the imbalance, self-correcting), while at the unstable crossing (R≈50.9) both slopes are the same sign (perturbations reinforce the imbalance, self-amplifying). The general criterion is the sign of `d/dR(omega_left - omega_right)` at the crossing: positive = stable, negative = unstable.

### Vehicle 4 Configs (bell-curve response)

| File | Vehicle Name | Wiring | Response | Behavior |
|------|-------------|--------|----------|----------|
| `vehicle_4a.json` | vehicle-4a | uncrossed | bell (peak=100, max_V=50) | Orbits at R≈42.7 (stimulus≈219) |
| `vehicle_4a_inner_orbit_try.json` | vehicle-4a | uncrossed | bell | Starts at R≈40, converges to inner orbit |
| `vehicle_4a_outer_orbit_try.json` | vehicle-4a | uncrossed | bell | Starts at R≈50.9 (outer solution), converges to inner orbit |
| `vehicle_4a_both_orbits_try.json` | vehicle-4a, vehicle-4a-outer | uncrossed | bell | Two vehicles: inner (R≈42.7) and outer (R≈50.9) start, both converge to same orbit |
| `vehicle_4a_bouncing_off.json` | vehicle-4a | uncrossed | bell (B=25) | Starts at R=30 heading east. Crawls through dead zone, gets flung SE on reaching bell zone, escapes. |
| `vehicle_4a_bouncing_approaches.json` | 3 vehicles | uncrossed | bell (B=5,10,25) | Head-on approaches from west at different offsets. All plunge into dead zone (stimulus>200), crawl on base_voltage. |
| `vehicle_4a_bouncing_glancing.json` | 3 vehicles | uncrossed | bell (B=5) | Glancing east approach past source at miss distances 50/60/70. Closest captured into orbit (stimulus≈250). Other two deflected NE, escape. No bounce-back observed. |
| `vehicle_4a_big_oval.json` | big oval try | uncrossed | bell (B=25) | **Oval orbit around two sources.** Separation=60 (<orbital diameter). Vehicle orbits the pair as a single unit. |
| `vehicle_4a_figure8.json` | figure-8 | uncrossed | bell (B=25) | **Figure-8!** Two sources separated by 125 units. Vehicle orbits one source, gets handed off to the other, repeats. Stable figure-8 trajectory. |
| `vehicle_4a_figure8_crossed.json` | figure-8-crossed | crossed | bell (B=25) | Same two sources, crossed wiring. Escapes NE, no orbit or figure-8. Crossed wiring steers toward source in bell zone, which flings the vehicle out rather than capturing it. |
| `vehicle_4a_5_sources_line.json` | 5-source-orbiter | uncrossed | bell (B=25) | **Orbits a line of 5 sources.** Separation=60 each. Vehicle orbits the entire line in an elongated oval. |

**Bouncing behavior (Braitenberg's description):** Vehicle 4a "navigates toward the source, turns away when stimulus becomes strong, circles back." Not yet reproduced. The bell active zone (stimulus 0–200) is a narrow ring; direct approaches plunge through into the dead zone (stimulus>200, bell=0), and glancing approaches either get captured into orbit or escape after a single deflection. The missing ingredient may be a mechanism to curve the vehicle back after deflection — with symmetric base_voltages and no stimulus, the escaped vehicle just goes straight.

19. ✅ Two-source orbital behaviors. Separation determines the trajectory shape: at 60 units (< orbital diameter ~85) the vehicle orbits both sources as a single unit in an oval; at 125 units (~1.5x orbital diameter) the vehicle produces a stable figure-8, orbiting each source in turn. Crossed wiring escapes rather than orbiting.
18. ✅ Vehicle 3a (inverse response) cannot orbit with symmetric base_voltages. Graphical analysis with B=0, 10, 25, 50, 100, 200 shows zero crossings — the inner wheel always has higher angular velocity. The monotonic inverse response cannot produce enough speed differential to overcome the inner wheel's geometric radius advantage. The bell curve's non-monotonicity is essential for orbiting with equal base_voltages. See [docs/orbit_condition_3a.png](docs/orbit_condition_3a.png) and [docs/orbit_condition_3a_base_voltage.png](docs/orbit_condition_3a_base_voltage.png). Vehicle 3 requires asymmetric base_voltages to orbit.
20. ✅ Triangular (tent) sensor response function added. Piecewise linear version of bell: rises linearly from 0 to max_voltage at peak_stimulus, falls linearly back to 0 at 2×peak_stimulus. Same qualitative shape as bell but with sharp peak.
21. ✅ Figure-8 guide overlay: when contours are enabled (C key) and a bell or triangular sensor is in use, two tangent circles are drawn around each source. Inner circle centered on source with radius = R_peak (the peak-stimulus distance), outer circle centered at 2×R_peak below source. They meet at the crossing point where the vehicle transitions between the two steering regimes.
22. Multi-vehicle triangular experiment (`vehicle_4a_triangular_multi.json`): 7 vehicles at starting distances R=45 to R=75 from source. First 2 (R=45, R=50) orbit the source. R=55 escapes ESE, rest escape ENE. Single-source figure-8 not yet achieved.
23. Figure-8 grid experiments (`vehicle_4a_triangular_fig8.json`): Systematic search for single-source figure-8 initial conditions with triangular response.
    - **2D grid (SE headings at crossing point)**: 4 distances × 3 headings (h=-0.3 to -0.8) starting north of source. 5 vehicles orbited, rest escaped south/east/NE. R73/h-0.8 made a ~90° turn before escaping — closest to interesting behavior.
    - **Cluster around R73/h-0.8**: 3×3 grid (R=71–75, h=-0.7 to -0.9). No figure-8.
    - **Bottom of inner lobe (heading west)**: 7 vehicles directly south of source at R=45–75, all heading west (h=π). R=45 and R=50 orbited. All others escaped (headings ranged NW to SW).
24. **Single-source figure-8 appears impossible with uncrossed wiring.** Steering analysis:

    Consider a vehicle with uncrossed wiring (SL→ML, SR→MR) and a non-monotonic response (bell/triangular). The triangular response has two zones separated by R_peak (the distance where stimulus = peak_stimulus):

    - **Closer than R_peak** (stimulus > peak_stimulus, voltage *drops* as you get closer): The inner sensor (closer to source) reads higher stimulus but gets *lower* voltage. The outer sensor gets *higher* voltage. With uncrossed wiring, the outer-side motor goes faster → vehicle steers **toward** the source. ✓ This is why the circular orbit works.

    - **Farther than R_peak** (stimulus < peak_stimulus, voltage *rises* as you get closer): The inner sensor (closer to source) reads higher stimulus and gets *higher* voltage. With uncrossed wiring, the source-side motor goes faster → vehicle steers **away** from the source. ✗ This is classic "fear" behavior.

    For a figure-8, the outer lobe requires the vehicle to curve *back toward* the source after passing R_peak. But beyond R_peak, uncrossed wiring always steers away. The vehicle escapes and never returns.

    Crossed wiring would fix the outer lobe (steers toward source beyond R_peak) but break the inner orbit (steers away from source inside R_peak). **No single wiring pattern can serve both lobes.**

    This explains why the two-source figure-8 works: each source provides its own orbit attractor (inside R_peak), and the "handoff" between sources replaces the need for an outer lobe around a single source.

25. ✅ Real-time source intensity control: `[` and `]` keys scale all source intensities by 1.1× / 0.91×. Displayed in status bar as `I=nnnnn`.
26. ✅ Asymmetric base_voltage experiments with uncrossed wiring (triangular response):
    - B=26/24 at R=200–400: vehicles orbit the source at close range. Farther vehicles repelled by source (fear behavior on ascending side).
    - B=25.5/24.5 at R=600: orbits source. R=800: orbit too tight.
    - Halved base_voltages to ~12.5 keeping same ratio. Orbit diameter from bias alone: R = W×(B_L+B_R)/(2×ΔB). For ΔB=0.1V, diameter ≈ 3000.
    - Key observation: **vehicles NOT orbiting the source are repelled by it** — confirming the ascending-side fear behavior from item 24.
27. ✅ Crossed wiring experiments with asymmetric base_voltage (triangular response):
    - Crossed wiring (SL→MR, SR→ML) reverses the steering: attracts toward source on ascending side, repels on descending side.
    - Vehicles dive toward source, accelerate hard, then get repelled on the descending side. Some bounce off but never return for a second pass.
    - With real-time intensity control: **vehicles always get captured into orbit regardless of how weak the source is made.** The crossed wiring attraction on the ascending side is inescapable.
    - Stuck between two extremes: uncrossed repels (never gets close enough), crossed attracts (always captured).
28. ✅ Zero-curvature derivation for figure-8 crossing condition:
    - Concept: a vehicle in circular orbit from base_voltage bias. Source approaches from infinity. At some critical distance, the sensor-induced curvature exactly cancels the bias curvature → zero curvature → straight-line crossing → figure-8.
    - Formula: d_critical = [4 × max_V × I × d_s × sin(α) / (peak_S × ΔB)]^(1/3)
    - For R_orbit ≈ d_critical: ΔB ≈ 1.34, B_L ≈ 13.17, B_R ≈ 11.83, R_orbit ≈ 112.
    - Tested with these parameters and progressively larger distances (up to R=1600) and orbit diameters (up to ~896). With real-time intensity tweaking, can get a vehicle to deflect ~1/4 around the source on one pass, but the deflection weakens on subsequent passes. No stable figure-8 achieved at these parameters.
29. ✅ Per-vehicle trail colors: each vehicle gets a distinct color (blue, red, green, gold, purple, cyan, orange, pink) for both body and trail. Trail length increased to 60000 steps. Max speed increased to 512x (200 steps/frame).
30. **✅ SINGLE-SOURCE FIGURE-8 ACHIEVED!** The breakthrough came from pushing parameters to extremes:
    - **Very small base_voltage bias**: B_L=1.26675, B_R=1.23325 (ΔB=0.0335). This gives a huge natural orbit radius (~4500), so the bias curvature is extremely gentle.
    - **Crossed wiring** (SL→MR, SR→ML)
    - **Reduced source intensity**: 273205 (400000 reduced by 4 presses of `[`, i.e. ÷1.1^4)
    - **Starting distance R=1280** south of source, heading west
    - **Triangular response** (peak_stimulus=100, max_voltage=50)
    - At these parameters the sensor voltages (up to 50V) massively dominate the tiny base_voltages (~1.25V). The bias provides just enough curvature to bring the vehicle back for a second pass after the source deflects it. The blue vehicle (R1280) traced a clear figure-8: one lobe wrapping around the source, a crossing near the source, and an outer lobe extending away before curving back. The other 5 vehicles at R=1300–1380 made single large loops of various sizes but did not close a figure-8 — confirming this is a narrow parameter window.
    - **Key insight**: the earlier attempts with larger base_voltage bias (ΔB=0.67–1.34) had orbits too tight relative to the source's influence range. The figure-8 requires the bias orbit to be *much* larger than the source's effective range, so the source acts as a small perturbation that creates the crossing, while the bias provides the large-scale return path.
    - **Second run (t=5879)**: continued the same config longer. The blue vehicle (R1280) did NOT repeat the figure-8 — on the next approach it made a single large loop without closing a second lobe. The other vehicles each made single large loops of various sizes, all crossing near the source. This is a "rosette" or "petal" pattern rather than a repeating figure-8. The figure-8 crossing from the first run may have been a one-time event rather than a stable orbit.
    - **Long run (t=42170, I=330578)**: All 6 vehicles converged to the same precessing rosette/petal orbit. Each vehicle makes large loops that cross near the source and slowly precess around it. This is a **stable attractor** — all initial conditions in the cluster converge to the same orbit shape regardless of starting distance. The loops do not wrap around the source; they pass near it, get deflected, and curve back via the bias. The source intensity drifted up slightly to 330578 during interactive adjustment.
    - **Observation**: The convergence to a common precessing rosette is encouraging. If the source deflection can be increased enough that one lobe wraps *around* the source (rather than just past it), the result would be a precessing figure-8. Even a precessing figure-8 (not closed) would demonstrate the Braitenberg figure 7 behavior.
    - **Next experiment to try**: cluster vehicles very tightly around R=1280 (e.g. spacing of 5 units) to probe whether slightly different initial conditions or source intensity can push a lobe to wrap around the source, producing a precessing figure-8.

31. ✅ Removed max_speed clamp from simulation (speed = max(0, gain × voltage), no ceiling). Reduced dt from 0.05 to 0.01 for smoother curves near source. Increased max simulation speed to 512x with 2000 steps/frame.
32. ✅ Switched from triangular to bell response to eliminate kinks from piecewise-linear transitions.
33. ✅ Crossed-wiring circular orbit confirmed: with symmetric base_voltages (B=1.0/1.0), crossed wiring, bell response, and increased sensor arm (distance_from_center=24), all 6 vehicles at R=150–400 converged to same counter-clockwise circular orbit at R≈75. Stable attractor.
34. **✅ SINGLE-SOURCE FIGURE-8 ACHIEVED — REPEATING!** See [docs/figure8_single_source.jpeg](docs/figure8_single_source.jpeg).
    - **Crossed wiring** (SL→MR, SR→ML)
    - **Bell response** (peak_stimulus=100, max_voltage=50) — smooth, no kinks
    - **Strong clockwise bias**: B_L=5.0, B_R=4.0 (ΔB=1.0, bias orbit radius ≈ 54)
    - **Large sensor arm**: distance_from_center=24 (radial sensor spread ≈ 14, exceeding axle width of 12)
    - **Source intensity**: 273205
    - The blue vehicle (R=500) makes repeated figure-8 loops: counter-clockwise around the source, breaks free, clockwise outer loop via bias, returns to source. Multiple passes visible.
    - **Key insights that led to this**:
      1. Sensor arm must be large enough (radial spread ≥ axle width) for sufficient steering differential
      2. Clockwise bias must be strong enough to pull vehicle out of the counter-clockwise source orbit
      3. The balance between bias curvature and source capture determines whether the vehicle escapes after each inner loop
    - **Path to discovery**: precessing rosette (tiny bias) → confirmed crossed-wiring circular orbit (symmetric base_voltage) → added strong clockwise bias → figure-8

35. ✅ **Periodic orbit analysis: single-source figure-8 is a transient, not a periodic orbit.** Built `find_periodic_orbit.py` — a Poincaré section + shooting method solver with Floquet stability analysis (`scipy.optimize.fsolve` + `scipy.integrate.solve_ivp`). Used it on the `x1.042` speed-sweep vehicle (crossed wiring, bell response, small base_voltage bias).
    - **Found the only periodic orbit: a stable circle** at radius ≈ 46 from source, period ≈ 6.7, converged to machine precision (residual 3×10⁻¹²).
    - **Continuation sweep** (I = 100,000–300,000): the circular orbit family exists across the full range. Stability bifurcation at I ≈ 112,000 — unstable below, stable above. Higher I → larger radius, stronger stability.
    - **Floquet multipliers** at I = 160,725: λ = −0.497 ± 0.089i, |λ| = 0.505. Perturbations halve each orbit — strongly stable.
    - **The figure-8 is a transient**: the inner lobe follows partial revolutions of this stable circle. The outer lobe is driven by base-voltage turning bias. Precession occurs because the radially-symmetric single source provides no mechanism to lock the outer lobe's orientation. The trajectory eventually collapses onto the circular orbit.
    - **Conclusion**: closed single-source figure-8 requires breaking rotational symmetry (e.g., two sources). See [docs/periodic-orbit-analysis.md](docs/periodic-orbit-analysis.md).
    - **New dependencies**: `scipy`, `numpy`, `matplotlib` added to `requirements.txt`.

### Vehicle 4 Triangular Configs

| File | Vehicle Name | Wiring | Response | Behavior |
|------|-------------|--------|----------|----------|
| `vehicle_4a_triangular.json` | triangular-orbit | uncrossed | triangular (peak=100, max_V=50) | Starts at R≈63, orbits source |
| `vehicle_4a_triangular_multi.json` | R=195..R=225 | uncrossed | triangular (peak=100, max_V=50) | 7 vehicles at different distances. First 2 orbit, rest escape. |
| `vehicle_4a_triangular_fig8.json` | R500–R3000 | crossed | bell (peak=100, max_V=50), B=5.0/4.0, I=273205, sensor_arm=24 | **Repeating figure-8!** Blue vehicle loops around source and back, multiple passes. |

## Next Steps

1. Characterize figure-8 stability and parameter sensitivity (how wide is the parameter window?)
2. Create `configs/vehicle_1.json` (single sensor, straight line)
3. Multi-vehicle scenario configs (multiple vehicles interacting with same sources)
4. Consider Vehicles 4+ continued (memory, learning, threshold logic)
6. Numerical contouring (marching squares) for multi-source fields

## How to Run

```bash
cd vehicles
source .venv/bin/activate
python main.py configs/vehicle_2a_fear.json
```

Starts paused. Press Space to run.

### Controls

| Key | Action |
|-----|--------|
| Space | Play/pause |
| S | Step one dt (while paused) |
| R | Reset (reload config) |
| L | Load new config file |
| +/- | Speed up/slow down |
| T | Toggle trail |
| F | Toggle field overlay |
| C | Toggle field contours |
| Z/X | Zoom in/out |
| Arrows | Pan |
| H | Home (center on selected vehicle) |
| [ / ] | Decrease/increase source intensity (×0.91 / ×1.1) |
| Q/Esc | Quit |

Mouse: Click to select vehicle (shows diagnostics). Right-drag to pan. Scroll to zoom.

## Important Info

### Architecture

```
vehicles/          Pure simulation engine (no pygame)
  model.py         Domain dataclasses
  fields.py        Field evaluation (falloff + interior linear transition)
  sensors.py       Stimulus -> volts response functions
  simulation.py    Main loop: step() with differential drive
  config_loader.py JSON -> domain objects

gui/               Pygame rendering and controls
  camera.py        World <-> screen coordinate transforms
  renderer.py      Draw sources, vehicles, trails, overlays
  app.py           Event loop, orchestration

configs/           JSON scenario files
specs/             Design specifications
```

### Signal Chain

```
Field (K, lux, kPa, ppm) -> Sensor (V/unit) -> Volts -> Connection (weight) -> Motor (base_voltage + weighted sum) -> Speed
```

All sensors output volts. Motor input = base_voltage + sum of (connection_weight × sensor_voltage). Speed clamped to [0, max_speed].

### Key Design Decisions

- **Kinematic model**: Speed = f(stimulus). No mass, no forces, no inertia.
- **No point sources**: Inside source radius, field transitions to linear falloff (like gravity inside Earth).
- **Unbounded world**: No boundaries. Camera viewport determines what's visible.
- **Config-driven**: All parameters in JSON files. No code changes needed for new vehicle types.
- **Fixed dt with accumulator**: Simulation steps at exact dt regardless of frame rate.
- **base_voltage for true inhibition**: Motors have a `base_voltage` parameter that sets resting input before sensor contributions. Negative connection weights subtract from this baseline, enabling true inhibitory behavior (Vehicle 3) without requiring inverse response functions.
- **Asymmetric base_voltage for curved motion**: Setting different base_voltages for left/right motors creates a constant turning bias, which combined with stimulus responses can produce orbital behavior.

### Python Environment

- Python 3.13
- pygame-ce 2.5.6
- Virtual environment in `.venv/`
- Install: `python3 -m venv .venv && source .venv/bin/activate && pip install pygame-ce`
