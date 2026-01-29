# Vehicles Simulation - Domain Model Specification

## Overview

This document defines the core concepts for a Braitenberg Vehicles simulation.

---

## 1. Environment

An **Environment** is an unbounded 2D space containing one or more **Fields**. The world has no edges - vehicles can travel indefinitely. The GUI viewport determines which region is visible.

### Properties
- `fields`: list of Field

---

## 2. Field

A **Field** represents a spatial distribution of a stimulus type (e.g., light, heat, chemical).

### Properties
- `type`: FieldType (e.g., "light", "heat", "chemical")
- `sources`: list of Source

### Field Types
Fields are identified by a string type name. Sensors specify which field type they respond to.

---

## 3. Source

A **Source** emits a stimulus into its field. The stimulus intensity at any point is determined by the source's emission function.

### Properties
- `position`: Point (x, y)
- `intensity`: number (base intensity at the source)
- `radius`: number (source radius; no point sources)
- `falloff`: FalloffFunction

### Source Radius and Interior Field

Sources are not points. Each source has a `radius`. Inside the source radius, the field transitions to a linear falloff regardless of the exterior falloff law. This avoids singularities and is analogous to gravitational field strength inside a uniform sphere.

For a source with exterior falloff f(d):

```
if distance >= radius:
    stimulus = f(distance)              # normal exterior law
if distance < radius:
    stimulus = f(radius) × (distance / radius)   # linear interior
```

At `distance = radius`, both expressions agree: `f(radius)`. At `distance = 0`, stimulus is zero. The field is continuous everywhere and has a finite maximum at the source boundary.

### Falloff Functions (exterior, distance >= radius)
- `inverse_square`: intensity / distance²
- `inverse_linear`: intensity / distance
- `constant`: intensity (uniform field, no singularity issue)
- `gaussian`: intensity × exp(-distance² / (2σ²))

The total stimulus at a point is the sum of contributions from all sources of that field type.

---

## 4. Sensor (defined separately - see 03-sensor.md)

A **Sensor** is a reusable component defined independently of any vehicle. It specifies what field type it responds to and its response function (sensitivity, gain, curve shape). Think of it as a part in a catalog.

Full specification: `specs/03-sensor.md`

---

## 5. Vehicle

A **Vehicle** is a mobile agent that references sensors and defines how they are mounted and connected.

### Properties
- `position`: Point (x, y)
- `heading`: number (radians, 0 = east, π/2 = north)
- `body_radius`: number
- `sensor_mounts`: list of SensorMount
- `motors`: list of Motor (typically 2: left and right)
- `connections`: list of Connection

### Sensor Mount

A sensor mount places a sensor on the vehicle.

- `sensor`: reference to a Sensor definition (by name)
- `id`: string (unique within this vehicle, used by connections)
- `side`: "left" | "right" | "center"
- `angle_offset`: number (radians from vehicle heading)
- `distance_from_center`: number

---

## 6. Motor

A **Motor** drives a wheel, converting voltage to speed.

### Properties
- `id`: string (unique identifier)
- `side`: "left" | "right"
- `response`: MotorResponse (how voltage maps to speed)
- `max_speed`: number (speed units)

### Behavior

The motor receives the sum of voltages from all connections feeding it:

```
input_voltage = Σ (connection.weight × sensor.voltage)   [V]
speed = motor_response(input_voltage)                     [speed units]
```

### Motor Response Functions

Initially, motors respond linearly:
```
speed = clamp(motor_gain × input_voltage, 0, max_speed)
```
where `motor_gain` has units of speed/V.

Non-linear motor responses (threshold, sigmoid) may be added for later vehicles.

---

## 7. Connection

A **Connection** links a sensor to a motor with a weight.

### Properties
- `from_sensor`: Sensor.id
- `to_motor`: Motor.id
- `weight`: number (can be positive or negative)

### Classic Braitenberg Wiring Patterns
- **Ipsilateral (same-side)**: left sensor → left motor, right sensor → right motor
- **Contralateral (crossed)**: left sensor → right motor, right sensor → left motor

Combined with positive/negative weights, these produce the classic behaviors:
| Wiring | Weight | Behavior |
|--------|--------|----------|
| Ipsilateral | + | Fear (moves away from source) |
| Contralateral | + | Aggression (moves toward source fast) |
| Ipsilateral | - | Love (moves toward source, slows near it) |
| Contralateral | - | Explorer (moves away, slows near source) |

---

## 8. Simulation State

### Properties
- `environment`: Environment
- `vehicles`: list of Vehicle
- `time`: number (simulation time)

---

## Scope: Vehicles 1-3 (Initial Implementation)

The initial implementation covers Braitenberg's Vehicles 1-3:

| Vehicle | Sensors | Motors | Wiring | Response | Behavior |
|---------|---------|--------|--------|----------|----------|
| 1 | 1 | 1 | direct | linear | Speed varies with stimulus |
| 2a | 2 | 2 | ipsilateral | linear | Fear (flees source) |
| 2b | 2 | 2 | contralateral | linear | Aggression (attacks source) |
| 3a | 2 | 2 | ipsilateral | inhibitory | Love (approaches, slows) |
| 3b | 2 | 2 | contralateral | inhibitory | Explorer (avoids, slows) |

### Simplifying Assumptions (Vehicles 1-3)
- Sensors are point-like (no directionality)
- Single vehicle per simulation (no interaction)
- No obstacles

### Physics Model: Kinematic (not Dynamic)

Vehicles 1-3 use a **kinematic** model where speed is directly determined by sensor input:

```
speed = f(stimulus)
```

This means:
- No mass, no forces, no momentum
- Response is instantaneous
- Friction has no standard meaning (no force to oppose)

This is faithful to Braitenberg's spirit - the vehicles are thought experiments about sensor-motor relationships, not realistic physics simulations. If we later need friction or inertia, we can either:
- Reinterpret friction (as attenuation, threshold, or rate-limiting)
- Switch to a dynamic model with F=ma

For now, we stay kinematic.

---

## Future Extensions (Vehicles 4+)

These features may be added later to support more advanced vehicles:

- **Friction**: Braitenberg mentions friction as a property affecting vehicle movement. Could be implemented as a drag coefficient that reduces speed, or as a threshold below which motors produce no movement. Deferred until we determine if/how the book uses it.
- **Memory**: Internal state that persists across time steps
- **Threshold logic**: Binary activation based on stimulus levels
- **Habituation**: Decreased response to sustained stimulus
- **Learning**: Connection weights that change over time
- **Multiple vehicles**: Interaction, following, flocking
- **Directional sensors**: Cone of perception
- **Obstacles**: Walls, barriers that block stimulus

These are deferred until we implement vehicles that require them.

---

## Next Steps

- [ ] Define behavior specification (physics, movement equations)
- [ ] Define GUI specification
- [ ] Define file format for saving/loading configurations
