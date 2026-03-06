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
    """Apply sensor response function to stimulus, returning volts.

    output_bias is added after the response function; the result can be negative.
    The motor clamps speed at zero, so negative values simply inhibit the motor.
    """
    rf = sensor_def.response_function
    if rf.type == "linear":
        raw = rf.gain * stimulus
    elif rf.type == "threshold":
        raw = rf.max_voltage if stimulus >= rf.threshold else 0.0
    elif rf.type == "sigmoid":
        raw = rf.max_voltage / (1.0 + math.exp(-rf.gain * (stimulus - rf.midpoint)))
    elif rf.type == "logarithmic":
        raw = rf.gain * math.log(1.0 + stimulus)
    elif rf.type == "inverse":
        raw = rf.gain / (1.0 + stimulus)
    elif rf.type == "bell":
        if stimulus <= 0 or stimulus >= 2 * rf.peak_stimulus:
            raw = 0.0
        else:
            normalized = (stimulus - rf.peak_stimulus) / rf.peak_stimulus
            raw = rf.max_voltage * (1.0 - normalized * normalized)
    elif rf.type == "gaussian":
        sigma = rf.sigma if rf.sigma > 0 else rf.peak_stimulus / (2.0 * math.sqrt(math.log(2)))
        diff = stimulus - rf.peak_stimulus
        raw = rf.max_voltage * math.exp(-diff * diff / (2.0 * sigma * sigma))
    elif rf.type == "triangular":
        if stimulus <= 0 or stimulus >= 2 * rf.peak_stimulus:
            raw = 0.0
        elif stimulus <= rf.peak_stimulus:
            raw = rf.max_voltage * stimulus / rf.peak_stimulus
        else:
            raw = rf.max_voltage * (2.0 - stimulus / rf.peak_stimulus)
    else:
        raise ValueError(f"Unknown response function: {rf.type}")

    return raw + rf.output_bias
