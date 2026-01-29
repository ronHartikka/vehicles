# GUI Specification

## Overview

The GUI is a simulation viewer and controller built with Python and pygame. Configuration is defined in a file (JSON); the GUI loads it and runs the simulation. The GUI does not edit configurations - that's done in a text editor.

---

## Architecture

```
config.json  →  GUI application  →  simulation display + controls
```

- **Config file**: Defines environment, sources, sensors, vehicles, connections. Single source of truth.
- **GUI**: Loads config, runs simulation loop, renders the environment and vehicles, provides playback controls.

---

## Window Layout

```
┌──────────────────────────────────────────────────┐
│  Simulation View                                 │
│                                                  │
│    ○ source                                      │
│                          ▷ vehicle               │
│                                                  │
│                                                  │
│               ○ source                           │
│                                                  │
├──────────────────────────────────────────────────┤
│  Status Bar                                      │
│  [▶/❚❚] [Step] [Reset]  Speed: 1x   t=12.34    │
└──────────────────────────────────────────────────┘
```

### Simulation View (main area)

A camera into an unbounded 2D world. The world has no edges - vehicles can travel indefinitely in any direction. The view shows a rectangular region of the world determined by camera position and zoom level.

Renders:

- **Sources**: Drawn as circles at their radius. Color indicates field type (configurable). Brightness or size could indicate intensity.
- **Vehicles**: Drawn as a body (circle or triangle indicating heading) with visible sensor positions (small dots) and wheel positions.
- **Trail** (optional): Fading line showing the vehicle's recent path.
- **Field overlay** (optional, toggled): Heat-map style rendering of stimulus intensity across the visible region. Computed on a coarse grid covering the current viewport. Recomputed when the view changes (pan/zoom). For display only - not used by the simulation.

### Status Bar (bottom strip)

- **Play/Pause** button
- **Step** button: advance one dt while paused
- **Reset** button: reload config, restart simulation
- **Speed control**: multiplier for simulation speed (0.5x, 1x, 2x, 5x)
- **Simulation time** display

---

## Rendering Details

### Vehicle Rendering

```
        S_L     S_R          (sensors: small dots)
         \     /
          \   /
    W_L ──[body]── W_R       (body: circle with heading indicator)
```

- Body: filled circle of `body_radius`, with a line or triangle indicating heading direction.
- Sensors: small colored dots at their mount positions, relative to the vehicle. Color could indicate current voltage (e.g., brightness proportional to output).
- Wheels: short lines or small rectangles on left and right sides of the body at `axle_width / 2` from center.

### Source Rendering

- Circle with radius equal to `source.radius`.
- Color coded by field type (e.g., red for temperature, yellow for light).
- Label or tooltip with intensity value (optional).

### Trail Rendering

- A polyline of recent vehicle positions.
- Fades out over time (older positions more transparent).
- Toggled on/off by user.

### Field Overlay (optional, toggled)

- When enabled, renders a translucent heat map over the visible region.
- Computed on a coarse grid (e.g., 50x50 cells covering the viewport), recomputed when the view pans or zooms.
- Cached while the view is static and sources haven't changed.
- Color map: low stimulus → dark, high stimulus → bright, using field type color (configurable).

---

## Controls

### Keyboard

| Key | Action |
|-----|--------|
| Space | Toggle play/pause |
| S | Step one dt (while paused) |
| R | Reset simulation (reload config) |
| L | Load new config file |
| +/- | Increase/decrease speed |
| T | Toggle trail |
| F | Toggle field overlay |
| Z/X | Zoom in/out |
| Arrow keys | Pan the view |
| H | Re-center view on selected vehicle (or origin) |
| Esc/Q | Quit |

### Mouse

- **Click on vehicle**: Select it. Display its sensor voltages and motor speeds in an info panel.
- **Click on source**: Display its properties.
- **Scroll wheel**: Zoom in/out centered on cursor.
- **Middle-click drag** or **right-click drag**: Pan the view.

---

## Info Display (when vehicle selected)

A small overlay or sidebar showing live values for the selected vehicle:

```
Vehicle: "fearful-1"
  Sensor L:  stimulus = 3.42 K   voltage = 1.71 V
  Sensor R:  stimulus = 1.87 K   voltage = 0.94 V
  Motor L:   voltage = 1.71 V    speed = 0.17
  Motor R:   voltage = 0.94 V    speed = 0.09
  Heading:   0.34 rad (19.5°)
  Position:  (142.3, 98.7)
```

This is invaluable for understanding and debugging vehicle behavior.

---

## Config File Format

JSON. Structure mirrors the domain model:

```json
{
  "environment": {
    "fields": [
      {
        "type": "temperature",
        "sources": [
          {
            "position": [200, 100],
            "intensity": 1000,
            "radius": 15,
            "falloff": "inverse_square"
          }
        ]
      }
    ]
  },

  "sensors": {
    "heat-sensor-1": {
      "stimulus_unit": "K",
      "response_function": {
        "type": "linear",
        "gain": 1.0
      }
    }
  },

  "vehicles": [
    {
      "name": "fearful-1",
      "position": [100, 100],
      "heading": 0,
      "body_radius": 8,
      "axle_width": 12,
      "sensor_mounts": [
        {
          "id": "SL",
          "sensor": "heat-sensor-1",
          "side": "left",
          "angle_offset": 0.3,
          "distance_from_center": 8
        },
        {
          "id": "SR",
          "sensor": "heat-sensor-1",
          "side": "right",
          "angle_offset": -0.3,
          "distance_from_center": 8
        }
      ],
      "motors": [
        {
          "id": "ML",
          "side": "left",
          "max_speed": 5.0,
          "gain": 0.1
        },
        {
          "id": "MR",
          "side": "right",
          "max_speed": 5.0,
          "gain": 0.1
        }
      ],
      "connections": [
        { "from_sensor": "SL", "to_motor": "ML", "weight": 1.0 },
        { "from_sensor": "SR", "to_motor": "MR", "weight": 1.0 }
      ]
    }
  ],

  "simulation": {
    "dt": 0.05,
    "method": "euler"
  },

  "view": {
    "center": [200, 100],
    "zoom": 1.0,
    "window_width": 800,
    "window_height": 600
  },

  "colors": {
    "temperature": [255, 80, 40],
    "light": [255, 240, 60],
    "chemical": [60, 200, 100]
  }
}
```

### Sensor Definitions are Shared

Sensors are defined at the top level by name. Vehicles reference them by name in their sensor mounts. This way multiple vehicles can share sensor definitions.

---

## Startup

1. GUI launched with config file path as argument: `python vehicles.py config.json`
2. Loads and validates config.
3. Opens pygame window at the size specified in `view` config (default 800x600), centered on `view.center`.
4. Begins in paused state so user can see initial positions before running.

## Reloading

- **R** reloads the current config file and resets simulation state.
- **L** opens a file dialog to load a different config file. Simulation resets.
- In both cases the view resets to the config's initial view settings.

---

## Design Decisions

1. **Unbounded world.** The world has no size or boundaries. The `view` config specifies the initial camera position and zoom. The user can pan and zoom freely.
2. **Reload without restart.** R reloads current config; L loads a new file.
3. **Configurable colors.** Field type colors defined in the config file under `colors`. Defaults provided if omitted.
