"""Plot angular velocity of each wheel vs. orbit radius R.

The orbit condition is satisfied where the two curves cross.
Uses Vehicle 3a (love) parameters — inverse response, no base_voltage.
"""

import numpy as np
import matplotlib.pyplot as plt

# Vehicle 3a parameters
I = 50_000        # source intensity
sensor_gain = 50.0  # inverse response gain
B = 0.0           # motor base_voltage (none for 3a)
w = 1.0           # connection weight
g = 1.0           # motor gain
W = 12.0          # axle_width
d_s = 8.0         # sensor distance_from_center
alpha = 0.3       # sensor angle_offset (radians)
sigma = 1.0       # +1 = source to right (CW orbit)
max_speed = 150.0

# Range of R values to plot
R = np.linspace(20, 300, 2000)

# Sensor distance squared (Q_L and Q_R)
Q_L = R**2 + 2 * sigma * R * d_s * np.sin(alpha) + d_s**2
Q_R = R**2 - 2 * sigma * R * d_s * np.sin(alpha) + d_s**2

# Stimulus (inverse-square)
S_L = I / Q_L
S_R = I / Q_R

# Inverse response voltage: V(S) = gain / (1 + S)
V_L = sensor_gain / (1.0 + S_L)
V_R = sensor_gain / (1.0 + S_R)

# Wheel speeds (clamped to max_speed)
v_left = np.clip(g * (B + w * V_L), 0, max_speed)
v_right = np.clip(g * (B + w * V_R), 0, max_speed)

# Wheel orbit radii
R_left_wheel = R + W / 2    # outer wheel (CW, source to right)
R_right_wheel = R - W / 2   # inner wheel

# Angular velocities
omega_left = v_left / R_left_wheel
omega_right = v_right / R_right_wheel

# Find crossing point(s)
diff = omega_left - omega_right
crossings = []
for i in range(len(diff) - 1):
    if diff[i] * diff[i + 1] < 0:
        # Linear interpolation
        R_cross = R[i] - diff[i] * (R[i + 1] - R[i]) / (diff[i + 1] - diff[i])
        crossings.append(R_cross)

# Plot
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

# Top: angular velocities
ax1.plot(R, omega_left, label='left wheel (outer)', color='tab:blue')
ax1.plot(R, omega_right, label='right wheel (inner)', color='tab:red')
for Rc in crossings:
    omega_at_cross = np.interp(Rc, R, omega_left)
    ax1.axvline(Rc, color='gray', linestyle='--', alpha=0.5)
    ax1.plot(Rc, omega_at_cross, 'ko', markersize=8)
    ax1.annotate(f'R = {Rc:.1f}', (Rc, omega_at_cross),
                 textcoords="offset points", xytext=(10, 10))
ax1.set_ylabel('Angular velocity (v / R_wheel)')
ax1.set_title('Orbit Condition: Vehicle 3a (inverse response, B=0)')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Bottom: wheel speeds and stimulus
ax2_twin = ax2.twinx()
ax2.plot(R, v_left, label='v_left', color='tab:blue')
ax2.plot(R, v_right, label='v_right', color='tab:red')
ax2.set_ylabel('Wheel speed')
ax2.set_xlabel('R (source-to-vehicle distance)')
ax2.legend(loc='upper left')
ax2.grid(True, alpha=0.3)

# Show stimulus on right axis
S_center = I / R**2
ax2_twin.plot(R, S_center, label='stimulus at center', color='tab:green',
              linestyle=':', alpha=0.7)
ax2_twin.set_ylabel('Stimulus at vehicle center', color='tab:green')
ax2_twin.legend(loc='upper right')

for Rc in crossings:
    ax2.axvline(Rc, color='gray', linestyle='--', alpha=0.5)

plt.tight_layout()
plt.savefig('docs/orbit_condition_3a.png', dpi=150)
print(f"Saved plot to docs/orbit_condition_3a.png")
if crossings:
    for Rc in crossings:
        S_at_cross = I / Rc**2
        print(f"Orbit radius R = {Rc:.2f}, stimulus at center = {S_at_cross:.1f}")
else:
    print("No crossings found — no orbit solution in this range.")
plt.show()
