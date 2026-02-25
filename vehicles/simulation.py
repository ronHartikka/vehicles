"""Simulation engine: advance vehicles through time steps."""

import math
from dataclasses import dataclass, field
from typing import List, Dict

from .model import Point, Vehicle, ScenarioConfig
from .fields import evaluate_field
from .sensors import compute_voltage, STIMULUS_UNIT_TO_FIELD_TYPE


@dataclass
class SensorReading:
    mount_id: str
    stimulus: float
    voltage: float


@dataclass
class MotorState:
    motor_id: str
    input_voltage: float
    speed: float


@dataclass
class VehicleStepResult:
    sensor_readings: List[SensorReading]
    motor_states: List[MotorState]


class Simulation:
    def __init__(self, config: ScenarioConfig):
        self.environment = config.environment
        self.sensor_defs = config.sensor_defs
        self.vehicles = config.vehicles
        self.dt = config.simulation.dt
        self.method = config.simulation.method
        self.time = 0.0
        self._field_lookup = {f.type: f for f in self.environment.fields}
        self.diagnostics: Dict[str, VehicleStepResult] = {}

    def step(self):
        """Advance all vehicles by one dt."""
        for vehicle in self.vehicles:
            result = self._step_vehicle(vehicle)
            self.diagnostics[vehicle.name] = result
        self.time += self.dt

    def _step_vehicle(self, v: Vehicle) -> VehicleStepResult:
        # 1. Compute sensor voltages
        sensor_voltages = {}
        readings = []
        for mount in v.sensor_mounts:
            wx = v.position.x + mount.distance_from_center * math.cos(
                v.heading + mount.angle_offset
            )
            wy = v.position.y + mount.distance_from_center * math.sin(
                v.heading + mount.angle_offset
            )
            sensor_def = self.sensor_defs[mount.sensor_name]
            field_type = STIMULUS_UNIT_TO_FIELD_TYPE[sensor_def.stimulus_unit]
            f = self._field_lookup.get(field_type)
            stimulus = evaluate_field(Point(wx, wy), f) if f else 0.0
            voltage = compute_voltage(sensor_def, stimulus)
            sensor_voltages[mount.id] = voltage
            readings.append(SensorReading(mount.id, stimulus, voltage))

        # 2. Compute motor input voltages (base_voltage + weighted sensor contributions)
        motor_lookup = {m.id: m for m in v.motors}
        motor_input = {m.id: m.base_voltage for m in v.motors}
        for conn in v.connections:
            motor_input[conn.to_motor] += conn.weight * sensor_voltages[conn.from_sensor]

        # 3. Compute wheel speeds
        motor_states = []
        wheel_speeds = {}
        for mid, voltage_in in motor_input.items():
            motor = motor_lookup[mid]
            speed = max(0.0, motor.gain * voltage_in)
            wheel_speeds[motor.side] = wheel_speeds.get(motor.side, 0.0) + speed
            motor_states.append(MotorState(mid, voltage_in, speed))

        # 4. Differential drive update
        speed_l = wheel_speeds.get("left", 0.0)
        speed_r = wheel_speeds.get("right", 0.0)

        if self.method == "arc":
            self._arc_update(v, speed_l, speed_r)
        else:
            self._euler_update(v, speed_l, speed_r)

        # Normalize heading to [0, 2*pi)
        v.heading = v.heading % (2.0 * math.pi)

        return VehicleStepResult(readings, motor_states)

    def _euler_update(self, v: Vehicle, speed_l: float, speed_r: float):
        d_left = speed_l * self.dt
        d_right = speed_r * self.dt
        d_forward = (d_left + d_right) / 2.0
        d_heading = (d_right - d_left) / v.axle_width
        v.heading += d_heading
        v.position.x += d_forward * math.cos(v.heading)
        v.position.y += d_forward * math.sin(v.heading)

    def _arc_update(self, v: Vehicle, speed_l: float, speed_r: float):
        d_left = speed_l * self.dt
        d_right = speed_r * self.dt
        if abs(d_left - d_right) < 1e-10:
            # Straight line
            v.position.x += d_left * math.cos(v.heading)
            v.position.y += d_left * math.sin(v.heading)
        else:
            d_heading = (d_right - d_left) / v.axle_width
            R = v.axle_width * (d_left + d_right) / (2.0 * (d_right - d_left))
            icc_x = v.position.x - R * math.sin(v.heading)
            icc_y = v.position.y + R * math.cos(v.heading)
            v.position.x = icc_x + R * math.sin(v.heading + d_heading)
            v.position.y = icc_y - R * math.cos(v.heading + d_heading)
            v.heading += d_heading
