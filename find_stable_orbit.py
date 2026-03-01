"""Find truly stable circular orbit by computing Floquet multipliers.

Uses rotational symmetry: in polar coords (r, psi) where psi = heading - phi - pi/2
is the heading relative to tangent, a circular orbit is a fixed point.

Sweeps beta and intensity, computing the 2x2 Jacobian eigenvalues to find
parameter combinations where the orbit is asymptotically stable.
"""

import math
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq

# Vehicle geometry
W = 12; d = 24; alpha = 0.3
peak_stimulus = 100.0; max_voltage = 80.0
sigma = peak_stimulus / (2.0 * math.sqrt(math.log(2)))
B_R = 4.40
source = (0.0, 0.0)


def gaussian_response(stim):
    diff = stim - peak_stimulus
    return max_voltage * math.exp(-diff * diff / (2.0 * sigma * sigma))


def compute_speeds(x, y, heading, intensity, b_left):
    sl_x = x + d * math.cos(heading + alpha)
    sl_y = y + d * math.sin(heading + alpha)
    sr_x = x + d * math.cos(heading - alpha)
    sr_y = y + d * math.sin(heading - alpha)
    dl = math.sqrt((sl_x - source[0])**2 + (sl_y - source[1])**2)
    dr_val = math.sqrt((sr_x - source[0])**2 + (sr_y - source[1])**2)
    f_l = intensity / (dl * dl) if dl > 0.1 else intensity / 0.01
    f_r = intensity / (dr_val * dr_val) if dr_val > 0.1 else intensity / 0.01
    v_sl = gaussian_response(f_l)
    v_sr = gaussian_response(f_r)
    speed_l = max(0.0, b_left + v_sr)
    speed_r = max(0.0, B_R + v_sl)
    return speed_l, speed_r


def make_ode(intensity, b_left):
    def rhs(t, state):
        x, y, theta = state
        sl, sr = compute_speeds(x, y, theta, intensity, b_left)
        fwd = (sl + sr) / 2.0
        turn = (sr - sl) / W
        return [fwd * math.cos(theta), fwd * math.sin(theta), turn]
    return rhs


def find_orbit_radius(intensity, b_left, r_min=30, r_max=500):
    """Find r where R_curvature = r for tangential heading."""
    def residual(r):
        # Vehicle at (0, -r) heading east, source at origin
        # This is the tangential configuration
        sl, sr = compute_speeds(0.0, -r, 0.0, intensity, b_left)
        diff = sr - sl
        if abs(diff) < 1e-15:
            return 1e6
        R = W * (sl + sr) / (2.0 * diff)
        return R - r

    # Scan for sign changes
    r_vals = np.linspace(r_min, r_max, 2000)
    crossings = []
    prev = residual(r_vals[0])
    for r in r_vals[1:]:
        curr = residual(r)
        if not (math.isinf(curr) or math.isnan(curr) or math.isinf(prev) or math.isnan(prev)):
            if prev * curr < 0:
                try:
                    r_eq = brentq(residual, r - (r_vals[1]-r_vals[0]), r, xtol=1e-10)
                    # Check radial stability: dR/dr < 1
                    eps = 0.01
                    dR_dr = (residual(r_eq + eps) + r_eq + eps - residual(r_eq - eps) - r_eq + eps) / (2*eps)
                    # residual = R - r, so d(residual)/dr = dR/dr - 1. If dR/dr < 1, d(res)/dr < 0, which means
                    # residual goes from + to - (since we crossed zero). Check sign of prev vs curr:
                    crossings.append((r_eq, dR_dr))
                except:
                    pass
        prev = curr
    return crossings


def check_orbit_stability(intensity, b_left, r_orbit, n_orbits=5):
    """Compute Floquet multipliers by integrating perturbed orbits.

    Returns (multipliers, orbit_speed, period).
    multipliers: eigenvalues of the monodromy matrix (2x2).
    """
    rhs = make_ode(intensity, b_left)

    # Estimate period from speeds at equilibrium
    sl, sr = compute_speeds(0.0, -r_orbit, 0.0, intensity, b_left)
    fwd_speed = (sl + sr) / 2.0
    period_est = 2 * math.pi * r_orbit / fwd_speed

    # Integrate nominal orbit for one period using angle tracking
    # We'll detect when the vehicle completes one full orbit (position angle returns to start)
    def angle_event(t, state):
        x, y, theta = state
        phi = math.atan2(y, x)
        return phi + math.pi / 2  # zero when phi = -pi/2 (south)

    angle_event.direction = -1  # crossing from + to -  (going CW in angle? No, CCW.)
    # For CCW orbit starting at phi=-pi/2: phi increases, passes through 0, pi/2, pi, wraps to -pi,
    # approaches -pi/2 from below. So phi + pi/2 goes from 0, increases, wraps, approaches 0 from below.
    # We want direction = +1 (crossing from - to +, i.e., phi crossing -pi/2 from below)
    angle_event.direction = 1
    angle_event.terminal = True

    # Integrate with burn-in to avoid triggering at t=0
    state0 = [0.0, -r_orbit, 0.0]  # south, heading east

    # Phase 1: burn-in (quarter orbit)
    sol1 = solve_ivp(rhs, [0, period_est * 0.3], state0,
                     method='RK45', rtol=1e-11, atol=1e-13, max_step=0.5)
    state_burn = sol1.y[:, -1]

    # Phase 2: integrate until return to section
    sol2 = solve_ivp(rhs, [0, period_est * 1.5], state_burn,
                     method='RK45', rtol=1e-11, atol=1e-13, max_step=0.5,
                     events=angle_event)

    if not sol2.t_events[0].size:
        return None, fwd_speed, period_est

    period_actual = sol1.t[-1] + sol2.t_events[0][0]
    state_return = sol2.y_events[0][0]
    r_return = math.sqrt(state_return[0]**2 + state_return[1]**2)

    # Now compute Jacobian via finite differences
    # Perturb initial conditions in r and psi (heading offset from tangent)
    eps_r = 0.01
    eps_psi = 1e-5

    def integrate_one_orbit(x0, y0, theta0):
        """Integrate from (x0, y0, theta0) for one orbit, return (r_final, psi_final)."""
        s0 = [x0, y0, theta0]
        s1 = solve_ivp(rhs, [0, period_est * 0.3], s0,
                       method='RK45', rtol=1e-11, atol=1e-13, max_step=0.5)
        sb = s1.y[:, -1]
        s2 = solve_ivp(rhs, [0, period_est * 1.5], sb,
                       method='RK45', rtol=1e-11, atol=1e-13, max_step=0.5,
                       events=angle_event)
        if not s2.t_events[0].size:
            return None
        sf = s2.y_events[0][0]
        r_f = math.sqrt(sf[0]**2 + sf[1]**2)
        phi_f = math.atan2(sf[1], sf[0])
        psi_f = sf[2] - phi_f - math.pi/2  # heading relative to tangent
        return (r_f, psi_f)

    # Nominal
    nom = integrate_one_orbit(0.0, -r_orbit, 0.0)
    if nom is None:
        return None, fwd_speed, period_est

    # Perturb r+
    rp = integrate_one_orbit(0.0, -(r_orbit + eps_r), 0.0)
    # Perturb r-
    rm = integrate_one_orbit(0.0, -(r_orbit - eps_r), 0.0)
    # Perturb psi+
    pp = integrate_one_orbit(0.0, -r_orbit, eps_psi)
    # Perturb psi-
    pm = integrate_one_orbit(0.0, -r_orbit, -eps_psi)

    if any(x is None for x in [rp, rm, pp, pm]):
        return None, fwd_speed, period_est

    # Jacobian of return map: d(r', psi') / d(r, psi)
    # J[0,0] = dr'/dr, J[0,1] = dr'/dpsi
    # J[1,0] = dpsi'/dr, J[1,1] = dpsi'/dpsi
    J = np.array([
        [(rp[0] - rm[0]) / (2*eps_r), (pp[0] - pm[0]) / (2*eps_psi)],
        [(rp[1] - rm[1]) / (2*eps_r), (pp[1] - pm[1]) / (2*eps_psi)],
    ])

    eigenvalues = np.linalg.eigvals(J)

    return eigenvalues, fwd_speed, period_actual


print("=" * 90)
print("Searching for stable circular orbits (|Floquet multipliers| < 1)")
print(f"Vehicle: W={W}, d={d}, alpha={alpha}")
print(f"Sensor: gaussian, peak={peak_stimulus}, Vmax={max_voltage}, sigma={sigma:.1f}")
print(f"B_R = {B_R}")
print("=" * 90)

print(f"\n{'beta':>6} {'I':>10} {'r_orbit':>8} {'speed':>7} {'period':>7} {'|λ1|':>8} {'|λ2|':>8} {'STABLE':>7}")
print("-" * 75)

stable_results = []

for beta in np.arange(1.10, 1.80, 0.05):
    b_left = beta * B_R
    for r_target in [80, 100, 120, 150, 200]:
        intensity = peak_stimulus * r_target * r_target
        crossings = find_orbit_radius(intensity, b_left)

        for r_eq, dR_dr in crossings:
            if r_eq < 40 or r_eq > 400:
                continue
            if dR_dr > 1.0:  # skip radially unstable
                continue

            result = check_orbit_stability(intensity, b_left, r_eq)
            if result[0] is None:
                continue

            eigenvalues, speed, period = result
            mags = sorted(abs(eigenvalues))

            is_stable = all(abs(ev) < 1.0 for ev in eigenvalues)
            marker = "YES ★" if is_stable else ""

            print(f"{beta:6.2f} {intensity:10.0f} {r_eq:8.2f} {speed:7.1f} {period:7.1f} "
                  f"{mags[0]:8.4f} {mags[1]:8.4f} {marker:>7}")

            if is_stable:
                stable_results.append({
                    'beta': beta, 'I': intensity, 'B_L': b_left,
                    'r_orbit': r_eq, 'speed': speed, 'period': period,
                    'eigenvalues': eigenvalues, 'max_mult': max(abs(eigenvalues))
                })

print("\n" + "=" * 90)
if stable_results:
    print(f"Found {len(stable_results)} stable orbits!")
    stable_results.sort(key=lambda r: r['max_mult'])
    for r in stable_results[:10]:
        print(f"  beta={r['beta']:.2f}, I={r['I']:.0f}, r={r['r_orbit']:.1f}, "
              f"speed={r['speed']:.1f}, period={r['period']:.1f}, "
              f"|λ|_max={r['max_mult']:.4f}")
    best = stable_results[0]
    print(f"\nMOST STABLE: beta={best['beta']:.2f}, I={best['I']:.0f}, r={best['r_orbit']:.1f}")
    print(f"  B_L={best['B_L']:.3f}, B_R={B_R}")
    print(f"  Eigenvalues: {best['eigenvalues']}")
else:
    print("No fully stable orbits found. Closest to stability:")
    # Would need to collect all results and show closest
    print("Try narrower parameter ranges or different max_voltage/sigma.")
