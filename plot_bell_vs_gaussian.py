"""
Plot the bell and gaussian sensor response functions together,
with FWHM-matched parameters, to visually compare their shapes.
"""

import numpy as np
import matplotlib.pyplot as plt

# Parameters
peak_stimulus = 100.0
max_voltage = 50.0
sigma = peak_stimulus / (2.0 * np.sqrt(np.log(2)))  # ~0.6006 * peak_stimulus

# Stimulus range
stimulus = np.linspace(0, 250, 1000)

# --- Bell response ---
# V = max_voltage * (1 - ((stimulus - peak_stimulus) / peak_stimulus)^2)
# Clamped to 0 outside [0, 2 * peak_stimulus]
bell = max_voltage * (1.0 - ((stimulus - peak_stimulus) / peak_stimulus) ** 2)
bell = np.clip(bell, 0.0, None)

# --- Gaussian response ---
# V = max_voltage * exp(-(stimulus - peak_stimulus)^2 / (2 * sigma^2))
gaussian = max_voltage * np.exp(
    -((stimulus - peak_stimulus) ** 2) / (2.0 * sigma**2)
)

# --- Plot ---
fig, ax = plt.subplots(figsize=(10, 6))

ax.plot(stimulus, bell, label="Bell", linewidth=2)
ax.plot(stimulus, gaussian, label="Gaussian", linewidth=2)

# Half-max dashed line to confirm FWHM match
half_max = max_voltage / 2.0
ax.axhline(y=half_max, color="gray", linestyle="--", linewidth=1, label=f"Half-max ({half_max:.0f} V)")

ax.set_xlabel("Stimulus")
ax.set_ylabel("Voltage (V)")
ax.set_title("Bell vs Gaussian (FWHM-matched)")
ax.legend()
ax.grid(True, alpha=0.3)

output_path = "/Users/ronhartikka/Documents/Retirement Work/Engineer/vehicles/bell_vs_gaussian.png"
fig.savefig(output_path, dpi=150, bbox_inches="tight")
print(f"Saved plot to {output_path}")

plt.close(fig)
