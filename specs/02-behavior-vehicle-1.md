# Vehicle 1 - Behavior Specification

## Overview

Vehicle 1 is the simplest Braitenberg vehicle: one sensor, one motor, straight-line motion. Speed varies with stimulus intensity.

---

## Configuration

| Parameter | Type | Description |
|-----------|------|-------------|
| `position` | (x, y) | Initial position in world coordinates |
| `heading` | radians | Direction of travel (0 = east, π/2 = north) |
| `K` | number | Gain factor: how strongly stimulus affects speed |
| `field_type` | string | What the sensor responds to (e.g., "temperature") |

---

## Behavior

### Step 1: Read Stimulus

The sensor reads the total stimulus at the vehicle's position:

```
stimulus = Σ source.intensity × falloff(distance_to_source)
```

Where the sum is over all sources of the configured field type.

### Step 2: Compute Speed

```
speed = K × stimulus
```

Notes:
- If K > 0: vehicle speeds up in high-stimulus regions
- If K < 0: vehicle slows down in high-stimulus regions (requires rethinking - speed can't be negative?)

**Open question**: Should speed be clamped to [0, max_speed]? Negative speed could mean reverse, or we could take absolute value.

### Step 3: Update Position

```
new_x = x + speed × cos(heading) × dt
new_y = y + speed × sin(heading) × dt
```

Where `dt` is the simulation time step.

Heading remains constant - Vehicle 1 cannot turn.

---

## Behavior Variants

Braitenberg describes two variants based on whether more stimulus means more or less speed:

| Variant | Effect | Behavior |
|---------|--------|----------|
| 1a | More stimulus → more speed | Rushes through hot zones, lingers in cold |
| 1b | More stimulus → less speed | Lingers in hot zones, rushes through cold |

Variant 1b could be modeled as:
```
speed = max_speed - K × stimulus
```
or
```
speed = K / (1 + stimulus)
```

---

## Example Scenario

**Environment**: A single heat source at (100, 100) with inverse-square falloff.

**Vehicle 1a**: Starts at (50, 50), heading east (0 radians), K = 1.0

As it approaches the heat source, stimulus increases, so it speeds up. It zooms past the hot zone quickly. Once past, stimulus decreases, it slows down.

**Vehicle 1b**: Same setup, but speed = 10 - K × stimulus (clamped to 0)

As it approaches heat, it slows down. It may stop entirely if stimulus is high enough. It "likes" the warmth.

---

## Open Questions

1. How to handle K < 0 or resulting negative speeds?
2. Should there be a max_speed clamp?
3. What happens at environment boundaries? (stop, wrap, bounce?)

---

## Next Steps

- [ ] Resolve open questions
- [ ] Define Vehicle 2 behavior (two sensors, two motors, turning)
