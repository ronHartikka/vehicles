"""Explore whether adding base_voltage to Vehicle 3a enables orbiting.

Plots angular velocity curves for several base_voltage values.
"""

import numpy as np
import matplotlib.pyplot as plt

# Vehicle 3a parameters
I = 50_000        # source intensity
sensor_gain = 50.0  # inverse response gain
w = 1.0           # connection weight
g = 1.0           # motor gain
W = 12.0          # axle_width
d_s = 8.0         # sensor distance_from_center
alpha = 0.3       # sensor angle_offset (radians)
sigma = 1.0       # +1 = source to right (CW orbit)
max_speed = 150.0

# Range of R values
R = np.linspace(20, 300, 2000)

# Sensor distance squared
Q_L = R**2 + 2 * sigma * R * d_s * np.sin(alpha) + d_s**2
Q_R = R**2 - 2 * sigma * R * d_s * np.sin(alpha) + d_s**2

# Stimulus
S_L = I / Q_L
S_R = I / Q_R

# Inverse response voltage
V_L = sensor_gain / (1.0 + S_L)
V_R = sensor_gain / (1.0 + S_R)

# Wheel orbit radii
R_left_wheel = R + W / 2
R_right_wheel = R - W / 2

# Try several base_voltage values
base_voltages = [0, 10, 25, 50, 100, 200]

fig, axes = plt.subplots(2, 3, figsize=(15, 9), sharex=True, sharey='row')

for idx, B in enumerate(base_voltages):
    ax = axes[idx // 3, idx % 3]

    v_left = np.clip(g * (B + w * V_L), 0, max_speed)
    v_right = np.clip(g * (B + w * V_R), 0, max_speed)

    omega_left = v_left / R_left_wheel
    omega_right = v_right / R_right_wheel

    # Find crossings
    diff = omega_left - omega_right
    crossings = []
    for i in range(len(diff) - 1):
        if diff[i] * diff[i + 1] < 0:
            Rc = R[i] - diff[i] * (R[i + 1] - R[i]) / (diff[i + 1] - diff[i])
            crossings.append(Rc)

    ax.plot(R, omega_left, label='left (outer)', color='tab:blue')
    ax.plot(R, omega_right, label='right (inner)', color='tab:red')

    for Rc in crossings:
        omega_c = np.interp(Rc, R, omega_left)
        ax.axvline(Rc, color='gray', linestyle='--', alpha=0.5)
        ax.plot(Rc, omega_c, 'ko', markersize=6)
        ax.annotate(f'R={Rc:.1f}', (Rc, omega_c),
                    textcoords="offset points", xytext=(5, 8), fontsize=9)

    n_cross = len(crossings)
    ax.set_title(f'B = {B}  ({n_cross} crossing{"s" if n_cross != 1 else ""})')
    ax.grid(True, alpha=0.3)
    if idx == 0:
        ax.legend(fontsize=8)

    cross_info = ", ".join(f"R={Rc:.1f}" for Rc in crossings) if crossings else "none"
    print(f"B = {B:>5}: crossings = {cross_info}")

fig.suptitle('Vehicle 3a Orbit Condition vs. base_voltage', fontsize=14)
fig.supxlabel('R (source-to-vehicle distance)')
fig.supylabel('Angular velocity (v / R_wheel)')
plt.tight_layout()
plt.savefig('docs/orbit_condition_3a_base_voltage.png', dpi=150)
print(f"\nSaved plot to docs/orbit_condition_3a_base_voltage.png")
plt.show()
