# Sensor Specification

## Overview

A **Sensor** is a reusable component that converts environmental stimulus into voltage. Sensors are defined independently of vehicles. A vehicle references a sensor and specifies where it is mounted and how its output is connected.

All sensors output **volts**. What a sensor is sensitive to is determined by the units of its gain (e.g., V/K for temperature, V/lux for light). The value of the gain determines how sensitive it is.

This means all sensor outputs share a common currency (volts), making it physically meaningful to sum contributions from different sensors at a motor input.

---

## Signal Flow

```
Field stimulus   →   Sensor (gain in V/stimulus-unit)   →   Volts
     (Kelvin, lux, ...)         (V/K, V/lux, ...)            (V)
```

---

## Sensor Definition

| Property | Type | Description |
|----------|------|-------------|
| `name` | string | Unique identifier (e.g., "heat-sensor-low") |
| `stimulus_unit` | string | What this sensor responds to (e.g., "K", "lux") |
| `response_function` | ResponseFunction | Maps stimulus intensity to voltage output |

The `stimulus_unit` determines which field type the sensor reads from. The mapping between stimulus units and field types is:

| Stimulus Unit | Field Type |
|---------------|------------|
| K (Kelvin) | temperature |
| lux | light |
| mol/m³ | chemical |

(Additional mappings defined as needed.)

---

## Response Functions

A response function defines the relationship between stimulus intensity (input) and voltage output (V).

### Linear
```
voltage = gain × stimulus
```
| Parameter | Type | Units | Description |
|-----------|------|-------|-------------|
| `gain` | number | V/stimulus-unit | Sensitivity |

### Threshold
```
voltage = (stimulus >= threshold) ? max_voltage : 0
```
| Parameter | Type | Units | Description |
|-----------|------|-------|-------------|
| `threshold` | number | stimulus-unit | Level that triggers output |
| `max_voltage` | number | V | Output when triggered |

### Sigmoid
```
voltage = max_voltage / (1 + exp(-gain × (stimulus - midpoint)))
```
| Parameter | Type | Units | Description |
|-----------|------|-------|-------------|
| `gain` | number | 1/stimulus-unit | Steepness of the curve |
| `midpoint` | number | stimulus-unit | Stimulus at half output |
| `max_voltage` | number | V | Upper bound of output |

### Logarithmic
```
voltage = gain × log(1 + stimulus)
```
| Parameter | Type | Units | Description |
|-----------|------|-------|-------------|
| `gain` | number | V | Scale factor |

### Inverse
```
voltage = gain / (1 + stimulus)
```
| Parameter | Type | Units | Description |
|-----------|------|-------|-------------|
| `gain` | number | V | Voltage at zero stimulus |

This produces high voltage at low stimulus and low voltage at high stimulus - useful for Vehicle 1b-style "inhibitory" behavior without needing negative weights.

---

## Design Notes

- **Common currency**: All sensors output volts. This is what makes the system composable - a motor receives a sum of voltages and doesn't need to know whether they came from a heat sensor or a light sensor.

- **Gain defines sensitivity**: A sensor with gain 0.5 V/K and one with gain 3.0 V/K both sense temperature, but the second is six times more sensitive.

- **Sensor vs. Connection**: The sensor determines the voltage produced. The connection determines where that voltage goes and with what weight. These are separate concerns.

- **No position or wiring here**: Mount position and motor connections are properties of the vehicle, not the sensor. A sensor is like a part in a catalog; a vehicle is an assembly.

---

## Examples

```
Sensor:
  name: "heat-sensor-low"
  stimulus_unit: "K"
  response_function:
    type: linear
    gain: 0.5        # 0.5 V/K

Sensor:
  name: "heat-sensor-high"
  stimulus_unit: "K"
  response_function:
    type: linear
    gain: 3.0        # 3.0 V/K

Sensor:
  name: "light-sensor-sigmoid"
  stimulus_unit: "lux"
  response_function:
    type: sigmoid
    gain: 2.0        # 2.0 /lux
    midpoint: 5.0    # 5.0 lux
    max_voltage: 10.0  # 10.0 V
```

---

## Open Questions

1. Should a sensor have a `range` or `max_distance` beyond which it reads zero? Or is that purely a property of field falloff?
2. Should there be a `noise` parameter to add randomness to readings?
