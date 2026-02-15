# Braitenberg Vehicles Simulator

A simulator inspired by Valentino Braitenberg's book *Vehicles: Experiments in Synthetic Psychology*. Define simple vehicles with sensors and motors, wire them together, place them in environments with stimulus sources, and watch complex behaviors emerge.

## Quick Start

```bash
git clone https://github.com/ronHartikka/vehicles.git
cd vehicles
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py configs/vehicle_2a_fear.json
```

The simulation starts **paused**. Press **Space** to run.

## What This Is

Braitenberg showed that vehicles with just sensors and motors can exhibit behaviors that *look* like fear, aggression, love, and exploration -- depending only on how the sensors are wired to the motors.

This simulator lets you:

- **Define sensors** that convert environmental stimulus (heat, light, etc.) into voltage
- **Define environments** with stimulus sources and configurable falloff functions
- **Wire vehicles** by connecting sensors to motors with weights
- **Watch the behavior** emerge in a real-time 2D simulation

Everything is configured via JSON files -- no code changes needed to create new vehicles or environments.

## Controls

| Key | Action |
|-----|--------|
| Space | Play / Pause |
| S | Step one time increment (while paused) |
| R | Reset (reload config file) |
| L | Load a different config file |
| +/- | Speed up / slow down |
| T | Toggle vehicle trail |
| F | Toggle field intensity overlay |
| C | Toggle field contour lines |
| Z / X | Zoom in / out |
| Arrows | Pan the view |
| H | Re-center view on selected vehicle |
| Q / Esc | Quit |

**Mouse:** Click a vehicle to select it and see live diagnostics. Right-drag to pan. Scroll to zoom.

## How It Works

Each simulation step:

1. Each sensor reads the stimulus at its position in the environment
2. The sensor converts stimulus to **voltage** (all sensors output volts)
3. Voltages flow through weighted **connections** to motors
4. Each motor converts its input voltage to a **wheel speed**
5. Differential drive kinematics update the vehicle's position and heading

```
Field (Kelvin, lux, ...) --> Sensor (V/K, V/lux) --> Volts --> Connection (weight) --> Motor (speed/V) --> Wheel Speed
```

The key insight: **same hardware, different wiring, different behavior.**

| Wiring | Weight | Behavior |
|--------|--------|----------|
| Uncrossed (ipsilateral) | + | Fear -- turns away from source |
| Crossed (contralateral) | + | Aggression -- turns toward source |
| Uncrossed (ipsilateral) | - | Love -- approaches, slows near source |
| Crossed (contralateral) | - | Explorer -- avoids, slows near source |

## Included Configs

| File | Vehicle Name | Wiring | Response | Behavior |
|------|-------------|--------|----------|----------|
| `vehicle_2a_fear.json` | fearful-1 | uncrossed | linear | Fear |
| `vehicle_2a_1_fear.json` | fearful-1 | uncrossed | linear | Fear (closer start) |
| `vehicle_2b_aggression.json` | aggressive-1 | crossed | linear | Aggression |
| `vehicle_3a_love.json` | love-1 | uncrossed | inverse | Love |
| `vehicle_3b_explorer.json` | explorer-1 | crossed | inverse | Explorer |
| `vehicle_4a.json` | vehicle-4a | uncrossed | bell | Orbits source |

## Configuration

Scenarios are defined in JSON files. See `configs/vehicle_2a_fear.json` for a complete example.

A config file defines:

- **Environment** -- fields and sources with position, intensity, radius, and falloff
- **Sensors** -- reusable definitions with stimulus type and response function
- **Vehicles** -- sensor mounts, motors, and the connections between them
- **View** -- initial camera position and zoom

## Requirements

- Python 3.10+
- pygame-ce

## Project Structure

```
configs/           JSON scenario files
vehicles/          Simulation engine (pure Python, no pygame dependency)
gui/               Pygame rendering and controls
specs/             Design specifications
main.py            Entry point
```

## License

This project is for educational and personal use.
