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
    elif rf.type == "bell":
        # Symmetric bell curve: zero at 0, peak at peak_stimulus, zero at 2*peak_stimulus
        # voltage = max_voltage * (1 - ((stimulus - peak) / peak)^2), clamped to >= 0
        if stimulus <= 0 or stimulus >= 2 * rf.peak_stimulus:
            return 0.0
        normalized = (stimulus - rf.peak_stimulus) / rf.peak_stimulus
        return rf.max_voltage * (1.0 - normalized * normalized)
    elif rf.type == "triangular":
        # Tent function: zero at 0, linear up to peak_stimulus, linear down to 2*peak_stimulus
        if stimulus <= 0 or stimulus >= 2 * rf.peak_stimulus:
            return 0.0
        if stimulus <= rf.peak_stimulus:
            return rf.max_voltage * stimulus / rf.peak_stimulus
        else:
            return rf.max_voltage * (2.0 - stimulus / rf.peak_stimulus)
    else:
        raise ValueError(f"Unknown response function: {rf.type}")
