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
   - `sensors.py` - Response functions (linear, threshold, sigmoid, logarithmic, inverse, bell)
   - `simulation.py` - Main loop step with differential drive kinematics
   - `config_loader.py` - JSON config loading
7. ✅ GUI (`gui/` package)
   - `camera.py` - World-to-screen transforms with pan/zoom
   - `renderer.py` - Sources, vehicles, trails, field overlay, field contours
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

### Vehicle 4 Configs (bell-curve response)

| File | Vehicle Name | Wiring | Response | Behavior |
|------|-------------|--------|----------|----------|
| `vehicle_4a.json` | vehicle-4a | uncrossed | bell (peak=100, max_V=50) | Orbits at R≈42.7 (stimulus≈219). A second solution at R≈50.9 (stimulus≈154) may be unstable. |

## Next Steps

1. Create `configs/vehicle_1.json` (single sensor, straight line)
2. Multi-vehicle scenario configs (multiple vehicles interacting with same sources)
3. Consider Vehicles 4+ continued (memory, learning, threshold logic)
4. Explore more orbital configurations (different asymmetric base_voltage ratios, multiple orbiting vehicles)
5. Test stability of the outer orbit solution (R≈50.9) — start vehicle at that distance
6. Parameter sensitivity analysis (how do orbit radius, speed, and stability depend on base_voltage difference and source intensity?)
7. Numerical contouring (marching squares) for multi-source fields

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
