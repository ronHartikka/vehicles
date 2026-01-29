# Main Loop Specification

## Overview

The simulation main loop advances the state of each vehicle through discrete time steps. The goal of each iteration is to compute the displacement of each wheel over the interval `dt`, then update the vehicle's position and heading accordingly.

---

## Loop Structure

```
repeat every dt:
    for each vehicle:
        1. Compute stimulus at each sensor position
        2. Compute sensor voltages
        3. Compute motor input voltages (via connections)
        4. Compute wheel speeds
        5. Compute wheel displacements
        6. Update vehicle position and heading
```

---

## Step-by-Step

### 1. Compute Stimulus at Each Sensor Position

Each mounted sensor has a world position derived from the vehicle's position, heading, and mount offset:

```
sensor_world_x = vehicle.x + mount.distance × cos(vehicle.heading + mount.angle_offset)
sensor_world_y = vehicle.y + mount.distance × sin(vehicle.heading + mount.angle_offset)
```

For each sensor, sum contributions from all sources of the matching field type:

```
stimulus = Σ source_contribution(sensor_world_position, source)
```

Where `source_contribution` applies the source's falloff function (with the interior linear transition for distance < source.radius).

### 2. Compute Sensor Voltages

Each sensor applies its response function to the stimulus:

```
voltage = sensor.response_function(stimulus)    [V]
```

### 3. Compute Motor Input Voltages

For each motor, sum weighted voltages from all connections feeding it:

```
motor_voltage = Σ connection.weight × voltage[connection.from_sensor]    [V]
```

### 4. Compute Wheel Speeds

Each motor converts its input voltage to a wheel speed:

```
wheel_speed = motor.response(motor_voltage)    [distance/time]
```

### 5. Compute Wheel Displacements

```
d_left  = speed_left  × dt    [distance]
d_right = speed_right × dt    [distance]
```

These two values are the primary output of the loop body.

### 6. Update Position and Heading

Two approaches, equivalent in the limit of small dt:

#### 6a. Euler Method (simple, approximate)

```
d_forward = (d_left + d_right) / 2
d_heading = (d_right - d_left) / axle_width

heading += d_heading
x += d_forward × cos(heading)
y += d_forward × sin(heading)
```

Fast and simple. Adequate when `dt` is small relative to the turn rate.

#### 6b. Exact Arc Method

When wheel speeds differ, the vehicle traces a circular arc. This method computes the exact arc.

```
d_left  = speed_left  × dt
d_right = speed_right × dt

if d_left == d_right:
    # Straight line (no turning)
    x += d_left × cos(heading)
    y += d_left × sin(heading)
else:
    # Circular arc
    d_heading = (d_right - d_left) / axle_width
    R = axle_width × (d_left + d_right) / (2 × (d_right - d_left))

    # Center of rotation (ICC - Instantaneous Center of Curvature)
    icc_x = x - R × sin(heading)
    icc_y = y + R × cos(heading)

    # Rotate vehicle position around ICC
    x = icc_x + R × sin(heading + d_heading)
    y = icc_y - R × cos(heading + d_heading)
    heading += d_heading
```

More accurate for large dt or fast turns.

---

## Choosing dt

The time step `dt` controls the tradeoff between accuracy and computation:

- Smaller dt → more accurate, more computation per simulated second
- Larger dt → faster simulation, less accurate (Euler error grows)

For initial implementation, a fixed dt with the Euler method should be sufficient. The arc method is available if we find accuracy issues.

---

## Timing

The main loop needs two clocks:

- **Simulation time**: advances by `dt` each iteration. Determines physics.
- **Wall clock time**: real elapsed time. Determines animation frame rate.

A `speed` parameter controls the ratio:

```
simulation_time_per_frame = dt × speed_multiplier
```

This allows the user to speed up, slow down, or pause the simulation.

---

## Vehicle 1 (Special Case)

Vehicle 1 has one sensor and one motor (or equivalently, two motors at equal speed). The loop simplifies to:

```
stimulus = field_value_at(vehicle.position)
voltage = sensor.response(stimulus)
speed = motor.response(voltage)
displacement = speed × dt

x += displacement × cos(heading)
y += displacement × sin(heading)
# heading never changes
```

---

## Design Decisions

1. **Fixed dt.** Adaptive time stepping deferred until needed.
2. **Vehicles do not interact.** Update order doesn't matter.
3. **Evaluate field on demand at sensor positions only.** No precomputed grid. (A grid may be useful later for visualization, but the simulation doesn't need it.)
