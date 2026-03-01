"""Plot radius of curvature vs distance from source.

Vehicle heading east, source to the north at distance r.
Crossed wiring: SL->MR, SR->ML. B_L > B_R gives CW bias.
Sensor attraction (CCW toward source) fights the bias.

Where R_curvature = r (diagonal line), we have a circular orbit.
Positive R = CCW (toward source). Negative R = CW (away from source).
"""

import math
import numpy as np
import matplotlib.pyplot as plt

# Current config parameters
I = 29000
peak_stimulus = 100
max_voltage = 80
sigma = peak_stimulus / (2.0 * math.sqrt(math.log(2)))  # FWHM-matched default
W = 12          # axle width
d = 24          # sensor distance from center
alpha = 0.3     # sensor angle offset
B_R = 4.40

betas = [1.50, 1.52, 1.54, 1.56, 1.58, 1.60]


def gaussian_response(stimulus):
    diff = stimulus - peak_stimulus
    return max_voltage * math.exp(-diff * diff / (2.0 * sigma * sigma))


def radius_of_curvature(r, B_L):
    """Radius of curvature for vehicle at distance r from source,
    heading east with source to the north.
    Positive R = CCW (curving toward source).
    """
    # Vehicle at origin heading east, source at (0, +r)
    # Left sensor at (d*cos(alpha), d*sin(alpha)) -- points NE, closer to source
    # Right sensor at (d*cos(-alpha), d*sin(-alpha)) -- points SE, farther from source
    dx = d * math.cos(alpha)

    # Distance from each sensor to source at (0, r)
    dy_L = r - d * math.sin(alpha)   # source is at +r, sensor at +d*sin(alpha)
    dy_R = r + d * math.sin(alpha)   # source is at +r, sensor at -d*sin(alpha)

    r_L = math.sqrt(dx * dx + dy_L * dy_L)
    r_R = math.sqrt(dx * dx + dy_R * dy_R)

    f_L = I / (r_L * r_L) if r_L > 0 else 1e12
    f_R = I / (r_R * r_R) if r_R > 0 else 1e12

    V_SL = gaussian_response(f_L)
    V_SR = gaussian_response(f_R)

    # Crossed wiring: SL -> MR, SR -> ML
    speed_L = B_L + V_SR    # left motor: higher base + right sensor
    speed_R = B_R + V_SL    # right motor: lower base + left sensor

    diff = speed_R - speed_L
    if abs(diff) < 1e-12:
        return float('inf')

    R = W * (speed_L + speed_R) / (2.0 * diff)
    return R


r_values = np.linspace(15, 300, 2000)

fig, ax = plt.subplots(figsize=(12, 8))

colors = plt.cm.viridis(np.linspace(0.1, 0.9, len(betas)))

for i, beta in enumerate(betas):
    B_L = beta * B_R
    R_values = [radius_of_curvature(r, B_L) for r in r_values]
    ax.plot(r_values, R_values, label=f'β={beta:.2f}', color=colors[i], linewidth=2)

# The circular orbit condition: R = r
ax.plot(r_values, r_values, 'k--', linewidth=2, label='R = r (circular orbit)')

# Also show R = -r for CW circular orbits (orbiting point to the south)
ax.plot(r_values, -r_values, 'k:', linewidth=1, alpha=0.3, label='R = −r')

ax.axhline(y=0, color='gray', linewidth=0.5)
ax.set_xlabel('Distance from source (r)', fontsize=14)
ax.set_ylabel('Radius of curvature (R)', fontsize=14)
ax.set_title(f'R(r): Where R = r → circular orbit\n'
             f'I={I}, Vmax={max_voltage}, σ={sigma:.1f}, B_R={B_R}',
             fontsize=14)
ax.set_xlim(15, 300)
ax.set_ylim(-300, 300)
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3)

# Mark intersections
for i, beta in enumerate(betas):
    B_L = beta * B_R
    # Find where R(r) - r = 0
    prev_val = None
    for r in r_values:
        R = radius_of_curvature(r, B_L)
        val = R - r
        if prev_val is not None and not (math.isinf(R) or math.isnan(R)):
            if prev_val * val < 0:  # sign change
                ax.plot(r, r, 'o', color=colors[i], markersize=10, zorder=5)
        prev_val = val if not (math.isinf(R) or math.isnan(R)) else None

plt.tight_layout()
plt.savefig('/Users/ronhartikka/Documents/Retirement Work/Engineer/vehicles/curvature_vs_distance.png',
            dpi=150)
print("Saved curvature_vs_distance.png")

# Print intersection points
print("\nCircular orbit radii (R = r intersections):")
for beta in betas:
    B_L = beta * B_R
    crossings = []
    prev_r = r_values[0]
    prev_val = radius_of_curvature(prev_r, B_L) - prev_r
    for r in r_values[1:]:
        R = radius_of_curvature(r, B_L)
        val = R - r
        if not (math.isinf(R) or math.isnan(R) or math.isinf(prev_val) or math.isnan(prev_val)):
            if prev_val * val < 0:
                # Linear interpolation
                r_cross = prev_r + (r - prev_r) * abs(prev_val) / (abs(prev_val) + abs(val))
                crossings.append(r_cross)
        prev_r = r
        prev_val = val
    if crossings:
        print(f"  β={beta:.2f}: r = {', '.join(f'{c:.1f}' for c in crossings)}")
    else:
        print(f"  β={beta:.2f}: no intersection found")
