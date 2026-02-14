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

### Wheel Speed as a Function of R

The goal is to express each wheel's speed purely in terms of the
source-to-vehicle-center distance `R` and the vehicle/source parameters.

**Notation:**

| Symbol | Meaning |
|--------|---------|
| `R` | distance from source to vehicle center (the unknown) |
| `I` | source intensity |
| `d_s` | sensor distance_from_center |
| `alpha` | sensor angle_offset |
| `sigma` | orbit direction (+1 CW, -1 CCW) |
| `p` | bell peak_stimulus |
| `V_max` | bell max_voltage |
| `B` | motor base_voltage |
| `w` | connection weight |
| `g` | motor gain |
| `W` | axle_width |

**Step 1 — Stimulus.** For inverse-square falloff, the square root in
the sensor distance formula gets squared away, giving a clean rational
function of R:

```
Q_L = R^2 + 2*sigma*R*d_s*sin(alpha) + d_s^2
Q_R = R^2 - 2*sigma*R*d_s*sin(alpha) + d_s^2

S_L = I / Q_L
S_R = I / Q_R
```

`Q_L` and `Q_R` are quadratics in R. The stimulus is rational in R.

**Step 2 — Bell response voltage.** The bell curve can be rewritten as:

```
V(S) = V_max * S * (2p - S) / p^2
```

Substituting S = I/Q (for either sensor):

```
V = V_max * I * (2p*Q - I) / (p^2 * Q^2)
```

The numerator `(2p*Q - I)` is quadratic in R. The denominator `Q^2` is
degree 4 in R. So V is a rational function of R.

**Step 3 — Wheel speed.** For uncrossed wiring (SL->ML, SR->MR):

```
v_left  = g * (B + w * V(S_L))
v_right = g * (B + w * V(S_R))
```

The gain `g` cancels in the orbit condition, so effectively:

```
v_left  = B + w * V_max * I * (2p*Q_L - I) / (p^2 * Q_L^2)
v_right = B + w * V_max * I * (2p*Q_R - I) / (p^2 * Q_R^2)
```

### Solving for the Orbit Radius

**Step 4 — Wheel orbit radii:**

```
R_outer = R + W/2
R_inner = R - W/2
```

**Step 5 — Orbit condition** (for CW orbit, left wheel is outer):

```
v_left / (R + W/2) = v_right / (R - W/2)
```

Cross-multiplying:

```
v_left * (R - W/2) = v_right * (R + W/2)
```

**Step 6 — Clear denominators.** Multiply both sides by `Q_L^2 * Q_R^2`
to eliminate all fractions. Define `k = w * V_max * I / p^2`:

```
(B*Q_L^2 + k*(2p*Q_L - I)) * Q_R^2 * (R - W/2)
    = (B*Q_R^2 + k*(2p*Q_R - I)) * Q_L^2 * (R + W/2)
```

Degree analysis:
- `B*Q_L^2` is degree 4 in R
- `k*(2p*Q_L - I)` is degree 2 in R
- So `(B*Q_L^2 + k*(2p*Q_L - I))` is degree 4
- Times `Q_R^2` (degree 4) times `(R - W/2)` (degree 1) = degree 9

However, the leading terms (`B*R^4 * R^4 * R = B*R^9`) are identical
on both sides and cancel. The result is a **polynomial of degree 8 in R**.

**Conclusion:** No closed-form solution exists — polynomials of degree 5
and above have no general algebraic solution (Abel-Ruffini theorem).
The orbit radius must be found numerically or graphically.

### Practical Approaches

- **Numerical root-finding:** Substitute specific parameter values into the
  degree-8 polynomial and solve for positive real roots.
- **Graphical:** Plot `v_left(R) / (R + W/2)` and `v_right(R) / (R - W/2)`
  vs. R. The orbit radius is where the curves cross.

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
- `motors::max_speed` only matters if the speed clamp is active. In the
  linear regime below max_speed, it doesn't affect the orbit radius.

## Observations

### Vehicle 4a

Config: `configs/vehicle_4a.json`

- Source: intensity=400000, falloff=inverse_square
- Sensor: bell response, peak_stimulus=100, max_voltage=50
- Motors: base_voltage=25, gain=1.0, max_speed=80
- Wiring: uncrossed (SL->ML, SR->MR), weight=1.0
- Axle width: 12, sensor distance: 8, sensor angle_offset: +/-0.3 rad

**Observation:** Vehicle orbits at approximately the stimulus=200 contour (d = sqrt(400000/200) ~ 44.7), not the stimulus=100 contour where the bell response peaks. The orbit radius is determined by the equal-angular-velocity condition, not by the peak of the sensor response.
