"""Sensor response functions: stimulus → volts."""

import math
from .model import SensorDef

STIMULUS_UNIT_TO_FIELD_TYPE = {
    "K": "temperature",
    "lux": "light",
    "mol/m3": "chemical",
    "kPa": "oxygen",
    "ppm": "organic",
}


def compute_voltage(sensor_def: SensorDef, stimulus: float) -> float:
    """Apply sensor response function to stimulus, returning volts."""
    rf = sensor_def.response_function
    if rf.type == "linear":
        return rf.gain * stimulus
    elif rf.type == "threshold":
        return rf.max_voltage if stimulus >= rf.threshold else 0.0
    elif rf.type == "sigmoid":
        return rf.max_voltage / (1.0 + math.exp(-rf.gain * (stimulus - rf.midpoint)))
    elif rf.type == "logarithmic":
        return rf.gain * math.log(1.0 + stimulus)
    elif rf.type == "inverse":
        return rf.gain / (1.0 + stimulus)
    else:
        raise ValueError(f"Unknown response function: {rf.type}")
