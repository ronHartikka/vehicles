# Vehicle 2 - Behavior Specification

## Overview

Vehicle 2 has two sensors and two motors. Each sensor outputs a voltage based on stimulus. Connections wire sensor voltages to motors. The two motors drive left and right wheels independently, producing both forward motion and turning.

Vehicle 2 is where Braitenberg's key insight emerges: the same hardware with different wiring produces radically different behavior.

---

## Configuration

| Parameter | Type | Description |
|-----------|------|-------------|
| `position` | (x, y) | Initial position in world coordinates |
| `heading` | radians | Initial direction (0 = east, π/2 = north) |
| `axle_width` | number | Distance between left and right wheels |
| `sensor_left` | Sensor reference | Sensor mounted on left side |
| `sensor_right` | Sensor reference | Sensor mounted on right side |
| `motor_left` | Motor | Left wheel motor |
| `motor_right` | Motor | Right wheel motor |
| `connections` | list of Connection | Wiring from sensors to motors |

---

## Signal Chain

```
                          ┌─── connection ──→ motor_left  ──→ left wheel
sensor_left  ──→ volts ──┤
                          └─── connection ──→ motor_right ──→ right wheel

                          ┌─── connection ──→ motor_left  ──→ left wheel
sensor_right ──→ volts ──┤
                          └─── connection ──→ motor_right ──→ right wheel
```

Each motor sums the voltages arriving from all connections feeding it.

---

## Step 1: Read Stimulus

Each sensor reads the total stimulus at its position:

```
stimulus_L = Σ source.intensity × falloff(distance(source, sensor_left_position))
stimulus_R = Σ source.intensity × falloff(distance(source, sensor_right_position))
```

Sensor positions are computed from the vehicle's position, heading, and mount offsets.

## Step 2: Compute Sensor Voltages

Each sensor applies its response function:

```
voltage_L = sensor_left.response(stimulus_L)    [V]
voltage_R = sensor_right.response(stimulus_R)    [V]
```

## Step 3: Compute Motor Input Voltages

Each motor sums its weighted inputs:

```
motor_left_voltage  = Σ (weight × voltage) for all connections to motor_left    [V]
motor_right_voltage = Σ (weight × voltage) for all connections to motor_right   [V]
```

## Step 4: Compute Wheel Speeds

Each motor converts voltage to speed:

```
speed_L = motor_left.response(motor_left_voltage)     [distance/time]
speed_R = motor_right.response(motor_right_voltage)    [distance/time]
```

## Step 5: Differential Drive Kinematics

Two wheels at different speeds produce both translation and rotation:

```
forward_speed = (speed_L + speed_R) / 2
turn_rate     = (speed_R - speed_L) / axle_width     [radians/time]
```

Convention: when speed_R > speed_L, the vehicle turns left (counter-clockwise).
This is standard differential drive: the faster wheel is on the outside of the turn.

### Position Update

```
heading += turn_rate × dt
x += forward_speed × cos(heading) × dt
y += forward_speed × sin(heading) × dt
```

(For large dt or fast turning, a circular arc integration would be more accurate, but for small dt this Euler integration is sufficient.)

---

## Wiring Patterns

### Vehicle 2a: Ipsilateral (uncrossed)

```
sensor_left  ──→ motor_left     (weight = +1)
sensor_right ──→ motor_right    (weight = +1)
```

**Behavior: Fear / Cowardice**

Source is to the left → left sensor gets more stimulus → left motor goes faster → right wheel dominates less → vehicle turns right (away from source). As it faces away, both sensors read lower → it slows down. If source is straight ahead, both sensors equal → drives straight toward it but speeds up, overshoots, and curves away.

Net effect: **turns away from stimulus source, accelerates as it flees.**

### Vehicle 2b: Contralateral (crossed)

```
sensor_left  ──→ motor_right    (weight = +1)
sensor_right ──→ motor_left     (weight = +1)
```

**Behavior: Aggression**

Source is to the left → left sensor gets more stimulus → right motor goes faster → vehicle turns left (toward source). As it faces the source, both sensors equalize → drives straight at it. Speed increases as it approaches.

Net effect: **turns toward stimulus source, accelerates as it approaches.**

---

## Worked Example

**Environment**: Single heat source at (200, 100), intensity 1000, inverse-square falloff.

**Vehicle 2a** (ipsilateral, fear):
- Position: (100, 100), heading: 0 (east, toward source)
- Sensors: linear, gain = 1.0 V/K, mounted left and right at ±15° from heading
- Motors: linear, gain = 0.1 distance/V, max_speed = 5.0
- Axle width: 10

At start, left sensor is slightly closer to source than right sensor (due to mount angle):
- stimulus_L ≈ stimulus_R (nearly equal, both facing source)
- Both motors get similar voltage → drives nearly straight toward source
- As it gets closer, any slight asymmetry amplifies
- It curves away and accelerates past the source

**Vehicle 2b** (contralateral, aggression):
- Same setup but crossed wiring
- Any asymmetry steers it toward the source
- Drives straight at the source, accelerating

---

## Design Notes

- **Same hardware, different wiring**: 2a and 2b use identical sensors and motors. Only the connections differ. This is the central point of Braitenberg's Chapter 2.

- **Sensor placement matters**: The sensors must be spatially separated (left/right) for differential stimulus to produce turning. If both sensors were at the center, they'd read the same value and the vehicle could never turn.

- **Positive weights only (for now)**: Vehicle 2 uses positive connection weights. Negative weights (inhibition) come in Vehicle 3.

---

## Open Questions

1. How far apart should sensors be mounted by default? Relative to body_radius?
2. Should we visualize the sensor readings and motor voltages in the GUI?
