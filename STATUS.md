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
   - `sensors.py` - Response functions (linear, threshold, sigmoid, logarithmic, inverse)
   - `simulation.py` - Main loop step with differential drive kinematics
   - `config_loader.py` - JSON config loading
7. ✅ GUI (`gui/` package)
   - `camera.py` - World-to-screen transforms with pan/zoom
   - `renderer.py` - Sources, vehicles, trails, field overlay
   - `app.py` - Pygame event loop, keyboard/mouse controls, status bar, info panel
8. ✅ Vehicle configs created and tested:

| File | Vehicle Name | Wiring | Response | Behavior |
|------|-------------|--------|----------|----------|
| `vehicle_2a_fear.json` | fearful-1 | uncrossed | linear | Fear |
| `vehicle_2a_1_fear.json` | fearful-1 | uncrossed | linear | Fear (closer start) |
| `vehicle_2b_aggression.json` | aggressive-1 | crossed | linear | Aggression |
| `vehicle_3a_love.json` | love-1 | uncrossed | inverse | Love |
| `vehicle_3b_explorer.json` | explorer-1 | crossed | inverse | Explorer |

9. ✅ Headless verification: Vehicle 2a veers away from heat source as expected
10. ✅ GUI tested interactively: all four behaviors confirmed visually

## Next Steps

1. Create `configs/vehicle_1.json` (single sensor, straight line)
2. Test aggressive vehicle charging a source and oscillating around its boundary
3. Multi-vehicle scenario configs
4. Consider Vehicles 4+ (memory, learning, threshold logic)

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
Field (K, lux) -> Sensor (V/K, V/lux) -> Volts -> Connection (weight) -> Volts -> Motor (speed/V) -> Speed
```

All sensors output volts. Voltages from different sensors can be summed at a motor.

### Key Design Decisions

- **Kinematic model**: Speed = f(stimulus). No mass, no forces, no inertia.
- **No point sources**: Inside source radius, field transitions to linear falloff (like gravity inside Earth).
- **Unbounded world**: No boundaries. Camera viewport determines what's visible.
- **Config-driven**: All parameters in JSON files. No code changes needed for new vehicle types.
- **Fixed dt with accumulator**: Simulation steps at exact dt regardless of frame rate.

### Python Environment

- Python 3.13
- pygame-ce 2.5.6
- Virtual environment in `.venv/`
- Install: `python3 -m venv .venv && source .venv/bin/activate && pip install pygame-ce`
