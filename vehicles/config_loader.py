"""Load a JSON config file into domain model objects."""

import json
from .model import (
    Point, Source, Field, Environment,
    ResponseFunction, SensorDef, SensorMount,
    Motor, Connection, Vehicle,
    SimulationConfig, ViewConfig, ScenarioConfig,
)


def load_config(path: str) -> ScenarioConfig:
    with open(path) as f:
        data = json.load(f)

    # Environment
    fields = []
    for fd in data["environment"]["fields"]:
        sources = [
            Source(
                position=Point(*s["position"]),
                intensity=s["intensity"],
                radius=s["radius"],
                falloff=s["falloff"],
                sigma=s.get("sigma", 1.0),
            )
            for s in fd["sources"]
        ]
        fields.append(Field(type=fd["type"], sources=sources))
    environment = Environment(fields=fields)

    # Sensor definitions
    sensor_defs = {}
    for name, sd in data["sensors"].items():
        rf_data = sd["response_function"]
        rf = ResponseFunction(
            type=rf_data["type"],
            gain=rf_data.get("gain", 1.0),
            threshold=rf_data.get("threshold", 0.0),
            midpoint=rf_data.get("midpoint", 0.0),
            max_voltage=rf_data.get("max_voltage", 10.0),
            peak_stimulus=rf_data.get("peak_stimulus", 100.0),
        )
        sensor_defs[name] = SensorDef(
            name=name,
            stimulus_unit=sd["stimulus_unit"],
            response_function=rf,
        )

    # Vehicles
    vehicles = []
    for vd in data["vehicles"]:
        mounts = [
            SensorMount(
                id=m["id"],
                sensor_name=m["sensor"],
                side=m["side"],
                angle_offset=m["angle_offset"],
                distance_from_center=m["distance_from_center"],
            )
            for m in vd["sensor_mounts"]
        ]
        motors = [
            Motor(
                id=m["id"],
                side=m["side"],
                gain=m["gain"],
                max_speed=m["max_speed"],
                base_voltage=m.get("base_voltage", 0.0),
            )
            for m in vd["motors"]
        ]
        connections = [
            Connection(
                from_sensor=c["from_sensor"],
                to_motor=c["to_motor"],
                weight=c["weight"],
            )
            for c in vd["connections"]
        ]
        vehicles.append(Vehicle(
            name=vd["name"],
            position=Point(*vd["position"]),
            heading=vd["heading"],
            body_radius=vd["body_radius"],
            axle_width=vd["axle_width"],
            sensor_mounts=mounts,
            motors=motors,
            connections=connections,
        ))

    # Simulation config
    sim_data = data.get("simulation", {})
    sim_config = SimulationConfig(
        dt=sim_data.get("dt", 0.05),
        method=sim_data.get("method", "euler"),
    )

    # View config
    vw = data.get("view", {})
    view_config = ViewConfig(
        center=Point(*vw.get("center", [0, 0])),
        zoom=vw.get("zoom", 1.0),
        window_width=vw.get("window_width", 800),
        window_height=vw.get("window_height", 600),
    )

    # Colors
    colors_raw = data.get("colors", {})
    colors = {k: tuple(v) for k, v in colors_raw.items()}

    return ScenarioConfig(
        environment=environment,
        sensor_defs=sensor_defs,
        vehicles=vehicles,
        simulation=sim_config,
        view=view_config,
        colors=colors,
    )
