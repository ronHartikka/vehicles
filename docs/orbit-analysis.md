# Orbital Behavior Analysis

## Circular Orbit Condition

A differential-drive vehicle orbits a source when both wheels maintain the same angular velocity around the source center. For a rigid body, all points share the same angular velocity, so:

```
v_left / R_left_wheel = v_right / R_right_wheel
```

where:
- `v_left`, `v_right` are the wheel speeds
- `R_left_wheel`, `R_right_wheel` are the distances from each wheel to the source center

### Geometry

With the vehicle center at distance `R` from the source and heading tangent to the orbit circle, the wheels lie along the radial direction (perpendicular to heading = along the axle):

```
R_outer_wheel = R + axle_width / 2
R_inner_wheel = R - axle_width / 2
```

Which wheel is outer/inner depends on orbit direction: source to the right (CW) makes the left wheel outer; source to the left (CCW) makes the right wheel outer.

### Sensor Positions

Sensors are at polar coordinates `(distance_from_center, angle_offset)` from the vehicle center, with angle measured from the heading. When the heading is tangent to the orbit, each sensor's distance from the source is (exact):

```
d_sensor = sqrt(R^2 + 2*sigma*R*d_s*sin(alpha) + d_s^2)
```

where:
- `d_s` is `distance_from_center`
- `alpha` is `angle_offset`
- `sigma = +1` for source to the right (CW orbit)
- `sigma = -1` for source to the left (CCW orbit)

Sanity checks (source to the right, sigma = +1):
- `alpha = +90°` (pure left, away from source): `d = R + d_s`
- `alpha = -90°` (pure right, toward source): `d = R - d_s`
- `alpha = 0` (straight ahead): `d = sqrt(R^2 + d_s^2)`

For Vehicle 4a (`d_s = 8`, `alpha = +/-0.3 rad`, source to the right):
- Left sensor (`alpha = +0.3`): slightly farther from source
- Right sensor (`alpha = -0.3`): slightly closer to source

### Wheel Speed Computation

The full signal chain from stimulus to wheel speed:

```
stimulus = field(d_sensor)                          # e.g. intensity / d^2
voltage  = response(stimulus)                       # e.g. bell curve
motor_in = base_voltage + connection_weight * voltage
speed    = gain * motor_in                          # clamped to max_speed
```

### Parameters That Determine Orbit Radius

| Parameter | Role |
|-----------|------|
| source intensity & falloff | Field strength at any distance |
| sensor angle_offset & distance_from_center | Where stimulus is sampled |
| sensor response_function (all its params) | Stimulus to voltage |
| connections (weights) | Which sensor drives which motor |
| motors base_voltage & gain | Voltage to wheel speed |
| vehicle axle_width | Wheel orbit radii = R +/- axle_width/2 |

Notes:
- `source::radius` only matters if the orbit approaches the source body.
- `motors::max_speed` only matters if the speed clamp is active. In the linear regime below max_speed, it doesn't affect the orbit radius.

## Observations

### Vehicle 4a

Config: `configs/vehicle_4a.json`

- Source: intensity=400000, falloff=inverse_square
- Sensor: bell response, peak_stimulus=100, max_voltage=50
- Motors: base_voltage=25, gain=1.0, max_speed=80
- Wiring: uncrossed (SL->ML, SR->MR), weight=1.0
- Axle width: 12, sensor distance: 8, sensor angle_offset: +/-0.3 rad

**Observation:** Vehicle orbits at approximately the stimulus=200 contour (d = sqrt(400000/200) ~ 44.7), not the stimulus=100 contour where the bell response peaks. The orbit radius is determined by the equal-angular-velocity condition, not by the peak of the sensor response.
