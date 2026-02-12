"""Domain model dataclasses for Braitenberg Vehicles simulation."""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple


@dataclass
class Point:
    x: float
    y: float


@dataclass
class Source:
    position: Point
    intensity: float
    radius: float
    falloff: str  # "inverse_square", "inverse_linear", "constant", "gaussian"
    sigma: float = 1.0  # only used for gaussian


@dataclass
class Field:
    type: str  # "temperature", "light", "chemical"
    sources: List[Source]


@dataclass
class Environment:
    fields: List[Field]


@dataclass
class ResponseFunction:
    type: str  # "linear", "threshold", "sigmoid", "logarithmic", "inverse"
    gain: float = 1.0
    threshold: float = 0.0
    midpoint: float = 0.0
    max_voltage: float = 10.0


@dataclass
class SensorDef:
    """Reusable sensor definition (catalog part)."""
    name: str
    stimulus_unit: str  # "K", "lux", "mol/m3"
    response_function: ResponseFunction


@dataclass
class SensorMount:
    """A sensor installed on a vehicle at a specific position."""
    id: str
    sensor_name: str  # references a SensorDef by name
    side: str  # "left", "right", "center"
    angle_offset: float  # radians from vehicle heading
    distance_from_center: float


@dataclass
class Motor:
    id: str
    side: str  # "left", "right"
    gain: float  # speed per volt
    max_speed: float
    base_voltage: float = 0.0  # resting input voltage before connections


@dataclass
class Connection:
    from_sensor: str  # SensorMount.id
    to_motor: str  # Motor.id
    weight: float


@dataclass
class Vehicle:
    name: str
    position: Point
    heading: float  # radians, 0=east, pi/2=north
    body_radius: float
    axle_width: float
    sensor_mounts: List[SensorMount]
    motors: List[Motor]
    connections: List[Connection]


@dataclass
class SimulationConfig:
    dt: float = 0.05
    method: str = "euler"  # "euler" or "arc"


@dataclass
class ViewConfig:
    center: Point = field(default_factory=lambda: Point(0.0, 0.0))
    zoom: float = 1.0
    window_width: int = 800
    window_height: int = 600


@dataclass
class ScenarioConfig:
    """Top-level object loaded from JSON."""
    environment: Environment
    sensor_defs: Dict[str, SensorDef]
    vehicles: List[Vehicle]
    simulation: SimulationConfig
    view: ViewConfig
    colors: Dict[str, Tuple[int, int, int]]
