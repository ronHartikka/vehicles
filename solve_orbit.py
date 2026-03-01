"""Find exact circular orbit conditions for Braitenberg vehicles.

For a circular orbit of radius r: the instantaneous radius of curvature R
must equal r when the vehicle heading is tangent to the circle.

Scans intensity and beta to find stable circular orbits at various radii.
"""

import math
import numpy as np

# Vehicle geometry
W = 12          # axle width
d = 24          # sensor distance from center
alpha = 0.3     # sensor angle offset (radians)

# Sensor response
peak_stimulus = 100.0
max_voltage = 80.0
sigma = peak_stimulus / (2.0 * math.sqrt(math.log(2)))  # FWHM-matched

B_R = 4.40      # right motor base voltage (fixed)


def gaussian_response(stimulus):
    diff = stimulus - peak_stimulus
    return max_voltage * math.exp(-diff * diff / (2.0 * sigma * sigma))


def radius_of_curvature(r, I, B_L):
    """R for vehicle at distance r from source, heading tangent to CCW orbit.
    Vehicle heading east, source directly north at distance r.
    Positive R = CCW."""
    dx = d * math.cos(alpha)
    dy_L = r - d * math.sin(alpha)
    dy_R = r + d * math.sin(alpha)

    r_L = math.sqrt(dx * dx + dy_L * dy_L)
    r_R = math.sqrt(dx * dx + dy_R * dy_R)

    f_L = I / (r_L * r_L) if r_L > 0 else 1e12
    f_R = I / (r_R * r_R) if r_R > 0 else 1e12

    V_SL = gaussian_response(f_L)
    V_SR = gaussian_response(f_R)

    # Crossed wiring: SL -> MR, SR -> ML
    speed_L = B_L + V_SR
    speed_R = B_R + V_SL

    diff = speed_R - speed_L
    if abs(diff) < 1e-12:
        return float('inf')

    return W * (speed_L + speed_R) / (2.0 * diff)


def find_orbit_radius(I, B_L, r_min=20, r_max=500, n=5000):
    """Find where R(r) = r (circular orbit condition).
    Returns list of (r_orbit, dR_dr) tuples. dR/dr < 1 at crossing means stable."""
    r_values = np.linspace(r_min, r_max, n)
    crossings = []

    prev_r = r_values[0]
    R_prev = radius_of_curvature(prev_r, I, B_L)
    prev_val = R_prev - prev_r

    for r in r_values[1:]:
        R = radius_of_curvature(r, I, B_L)
        val = R - r

        if not (math.isinf(R) or math.isnan(R) or math.isinf(prev_val) or math.isnan(prev_val)):
            if prev_val * val < 0:
                # Linear interpolation for crossing point
                r_cross = prev_r + (r - prev_r) * abs(prev_val) / (abs(prev_val) + abs(val))

                # Compute dR/dr at crossing via finite differences
                eps = 0.1
                R_plus = radius_of_curvature(r_cross + eps, I, B_L)
                R_minus = radius_of_curvature(r_cross - eps, I, B_L)
                dR_dr = (R_plus - R_minus) / (2 * eps)

                # Stability: stable if dR/dr < 1 at crossing
                stable = dR_dr < 1.0

                crossings.append((r_cross, dR_dr, stable))

        prev_r = r
        R_prev = R
        prev_val = val

    return crossings


print("=" * 80)
print("Finding circular orbit conditions")
print(f"Vehicle: W={W}, d={d}, alpha={alpha:.1f}")
print(f"Sensor: gaussian, peak={peak_stimulus}, Vmax={max_voltage}, sigma={sigma:.1f}")
print(f"B_R = {B_R}")
print("=" * 80)

# Strategy: for a given beta, find what intensity gives a nice orbit
# The peak-response distance is r_peak = sqrt(I / peak_stimulus)
# We want the orbit to be near r_peak where the sensor gradient is meaningful

print("\n--- Sweeping beta and intensity ---")
print(f"{'beta':>6} {'B_L':>6} {'I':>10} {'r_peak':>7} {'r_orbit':>8} {'dR/dr':>7} {'stable':>7} {'speed':>7}")
print("-" * 70)

results = []

for beta in [1.30, 1.40, 1.50, 1.60]:
    B_L = beta * B_R
    # Try intensities that put peak at various distances
    for r_target in [60, 80, 100, 120, 150, 200]:
        I = peak_stimulus * r_target * r_target  # puts peak at r_target
        crossings = find_orbit_radius(I, B_L)
        for r_orb, dR_dr, stable in crossings:
            if r_orb > 30:  # skip tiny orbits
                # Compute orbit speed at this radius
                R = radius_of_curvature(r_orb, I, B_L)
                # Recompute speeds to get forward speed
                dx = d * math.cos(alpha)
                dy_L = r_orb - d * math.sin(alpha)
                dy_R = r_orb + d * math.sin(alpha)
                r_L = math.sqrt(dx*dx + dy_L*dy_L)
                r_R = math.sqrt(dx*dx + dy_R*dy_R)
                f_L = I / (r_L*r_L)
                f_R = I / (r_R*r_R)
                V_SL = gaussian_response(f_L)
                V_SR = gaussian_response(f_R)
                speed_L = B_L + V_SR
                speed_R = B_R + V_SL
                fwd_speed = (speed_L + speed_R) / 2.0

                print(f"{beta:6.2f} {B_L:6.2f} {I:10.0f} {r_target:7.1f} {r_orb:8.1f} {dR_dr:7.3f} {'YES' if stable else 'no':>7} {fwd_speed:7.1f}")
                results.append({
                    'beta': beta, 'B_L': B_L, 'I': I,
                    'r_orbit': r_orb, 'dR_dr': dR_dr, 'stable': stable,
                    'speed': fwd_speed, 'r_peak': r_target
                })

# Pick a good one: stable, reasonable radius, moderate speed
print("\n\n--- Best candidates (stable, r_orbit > 50) ---")
good = [r for r in results if r['stable'] and r['r_orbit'] > 50]
good.sort(key=lambda r: abs(r['dR_dr']))  # most strongly stable first

for r in good[:10]:
    print(f"  beta={r['beta']:.2f}, I={r['I']:.0f}, r_orbit={r['r_orbit']:.1f}, "
          f"dR/dr={r['dR_dr']:.3f}, speed={r['speed']:.1f}")

if good:
    best = good[0]
    print(f"\n\nRECOMMENDED:")
    print(f"  Intensity I = {best['I']:.0f}")
    print(f"  Beta = {best['beta']:.2f} (B_L = {best['B_L']:.3f}, B_R = {B_R})")
    print(f"  Circular orbit radius = {best['r_orbit']:.1f}")
    print(f"  dR/dr = {best['dR_dr']:.4f} (< 1 = stable)")
    print(f"  Forward speed = {best['speed']:.1f}")
    print(f"  Orbit period = {2*math.pi*best['r_orbit']/best['speed']:.1f} time units")
    print(f"  Peak-response distance = {best['r_peak']:.1f}")
