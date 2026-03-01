"""Refine circular orbit radius and verify stability."""

import math
import numpy as np

W = 12; d = 24; alpha = 0.3
peak_stimulus = 100.0; max_voltage = 80.0
sigma = peak_stimulus / (2.0 * math.sqrt(math.log(2)))
B_R = 4.40

# Recommended parameters
I = 2_250_000
beta = 1.40
B_L = beta * B_R


def gaussian_response(stimulus):
    diff = stimulus - peak_stimulus
    return max_voltage * math.exp(-diff * diff / (2.0 * sigma * sigma))


def speeds_at_radius(r):
    """Return (speed_L, speed_R, V_SL, V_SR, f_L, f_R) for vehicle at distance r."""
    dx = d * math.cos(alpha)
    dy_L = r - d * math.sin(alpha)
    dy_R = r + d * math.sin(alpha)
    r_L = math.sqrt(dx*dx + dy_L*dy_L)
    r_R = math.sqrt(dx*dx + dy_R*dy_R)
    f_L = I / (r_L*r_L)
    f_R = I / (r_R*r_R)
    V_SL = gaussian_response(f_L)
    V_SR = gaussian_response(f_R)
    speed_L = B_L + V_SR
    speed_R = B_R + V_SL
    return speed_L, speed_R, V_SL, V_SR, f_L, f_R


def R_curvature(r):
    sL, sR, _, _, _, _ = speeds_at_radius(r)
    diff = sR - sL
    if abs(diff) < 1e-15:
        return float('inf')
    return W * (sL + sR) / (2.0 * diff)


# Binary search for R(r) = r
r_lo, r_hi = 150.0, 250.0
for _ in range(100):
    r_mid = (r_lo + r_hi) / 2
    if R_curvature(r_mid) - r_mid > 0:
        r_lo = r_mid
    else:
        r_hi = r_mid

r_orbit = (r_lo + r_hi) / 2
print(f"Parameters: I={I}, beta={beta:.2f}, B_L={B_L:.3f}, B_R={B_R}")
print(f"Exact orbit radius: r = {r_orbit:.4f}")

sL, sR, V_SL, V_SR, f_L, f_R = speeds_at_radius(r_orbit)
print(f"\nAt orbit radius {r_orbit:.2f}:")
print(f"  Field at left sensor:  {f_L:.2f} K")
print(f"  Field at right sensor: {f_R:.2f} K")
print(f"  V_SL = {V_SL:.3f} V,  V_SR = {V_SR:.3f} V")
print(f"  speed_L = {sL:.3f},  speed_R = {sR:.3f}")
print(f"  Forward speed = {(sL+sR)/2:.3f}")
print(f"  Turn rate = {(sR-sL)/W:.5f} rad/t")
print(f"  R_curvature = {R_curvature(r_orbit):.4f}  (should ≈ {r_orbit:.4f})")
print(f"  Orbit period = {2*math.pi*r_orbit/((sL+sR)/2):.1f} time units")

# Check stability: dR/dr at orbit
eps = 0.01
dR_dr = (R_curvature(r_orbit + eps) - R_curvature(r_orbit - eps)) / (2*eps)
print(f"  dR/dr = {dR_dr:.4f}  (< 1 = stable)")

# Show R(r) at proposed starting distances
print(f"\nR(r) at various starting distances:")
print(f"{'r':>8} {'R(r)':>10} {'R-r':>10} {'will...':>15}")
for r in [140, 155, 170, 185, r_orbit, 195, 210, 230]:
    R = R_curvature(r)
    diff = R - r
    if abs(diff) < 0.1:
        action = "EQUILIBRIUM"
    elif diff > 0:
        action = "spiral outward"
    else:
        action = "spiral inward"
    print(f"{r:8.1f} {R:10.2f} {diff:10.2f} {action:>15}")
