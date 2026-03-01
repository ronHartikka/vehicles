"""Find figure-8 orbits near the circular orbit stability boundary.

Key insight: at beta=1.10 the orbit is too stable (|lambda|=0.32) — everything
gets captured. At beta≈1.40, |lambda|≈1.0 and the orbit is marginally stable.
Vehicles just outside the basin of attraction do CW excursions that may close
into figure-8 orbits.

Strategy: sweep beta near the stability transition AND starting distance.
"""

import math
import numpy as np
from scipy.integrate import solve_ivp

# Fixed parameters
peak = 100.0
vmax = 80.0
sigma = peak / (2.0 * math.sqrt(math.log(2)))
W = 12; d = 24; alpha = 0.3
B_R = 4.40


def gaussian_response(stim):
    diff = stim - peak
    return vmax * math.exp(-diff * diff / (2.0 * sigma * sigma))


def make_ode(intensity, b_left):
    def rhs(t, state):
        x, y, theta = state
        sl_x = x + d * math.cos(theta + alpha)
        sl_y = y + d * math.sin(theta + alpha)
        sr_x = x + d * math.cos(theta - alpha)
        sr_y = y + d * math.sin(theta - alpha)
        dl = math.sqrt(sl_x*sl_x + sl_y*sl_y)
        dr = math.sqrt(sr_x*sr_x + sr_y*sr_y)
        f_l = intensity / (dl*dl) if dl > 0.1 else intensity / 0.01
        f_r = intensity / (dr*dr) if dr > 0.1 else intensity / 0.01
        v_sl = gaussian_response(f_l)
        v_sr = gaussian_response(f_r)
        speed_l = max(0.0, b_left + v_sr)
        speed_r = max(0.0, B_R + v_sl)
        fwd = (speed_l + speed_r) / 2.0
        turn = (speed_r - speed_l) / W
        return [fwd * math.cos(theta), fwd * math.sin(theta), turn]
    return rhs


def find_orbit_radius(intensity, b_left, r_min=30, r_max=400):
    """Find r where R_curvature = r (tangential heading)."""
    r_vals = np.linspace(r_min, r_max, 3000)
    for i in range(len(r_vals) - 1):
        r = r_vals[i]
        dx = d * math.cos(alpha)
        dy_L = r - d * math.sin(alpha)
        dy_R = r + d * math.sin(alpha)
        r_L = math.sqrt(dx*dx + dy_L*dy_L)
        r_R = math.sqrt(dx*dx + dy_R*dy_R)
        f_L = intensity / (r_L*r_L)
        f_R = intensity / (r_R*r_R)
        v_sl = gaussian_response(f_L)
        v_sr = gaussian_response(f_R)
        sl = b_left + v_sr
        sr = B_R + v_sl
        diff = sr - sl
        if abs(diff) < 1e-12:
            continue
        R = W * (sl + sr) / (2.0 * diff)
        val = R - r

        r2 = r_vals[i+1]
        dx2 = d * math.cos(alpha)
        dy_L2 = r2 - d * math.sin(alpha)
        dy_R2 = r2 + d * math.sin(alpha)
        r_L2 = math.sqrt(dx2*dx2 + dy_L2*dy_L2)
        r_R2 = math.sqrt(dx2*dx2 + dy_R2*dy_R2)
        f_L2 = intensity / (r_L2*r_L2)
        f_R2 = intensity / (r_R2*r_R2)
        v_sl2 = gaussian_response(f_L2)
        v_sr2 = gaussian_response(f_R2)
        sl2 = b_left + v_sr2
        sr2 = B_R + v_sl2
        diff2 = sr2 - sl2
        if abs(diff2) < 1e-12:
            continue
        R2 = W * (sl2 + sr2) / (2.0 * diff2)
        val2 = R2 - r2

        if val * val2 < 0 and R > 0 and R2 > 0:  # CCW orbit crossing
            # Check stability: dR/dr < 1
            eps = 0.1
            # Use simple finite diff
            r_cross = r + (r2 - r) * abs(val) / (abs(val) + abs(val2))
            return r_cross
    return None


def simulate(intensity, b_left, r_start, t_max=800):
    rhs = make_ode(intensity, b_left)
    sol = solve_ivp(rhs, [0, t_max], [0.0, -r_start, 0.0],
                    method='RK45', rtol=1e-10, atol=1e-12, max_step=0.5)
    return sol


def analyze(sol, r_start):
    """Analyze trajectory: detect CW excursion, measure closure."""
    xs, ys = sol.y[0], sol.y[1]
    rs = np.sqrt(xs**2 + ys**2)
    phis = np.arctan2(ys, xs)

    r_min, r_max = rs.min(), rs.max()

    # Track cumulative phi change
    dphi = np.diff(phis)
    dphi = np.where(dphi > np.pi, dphi - 2*np.pi, dphi)
    dphi = np.where(dphi < -np.pi, dphi + 2*np.pi, dphi)
    cum_phi = np.cumsum(dphi)

    # CW excursion: look for ANY significant CW angular travel
    # (not necessarily 2π — a figure-8 lobe might be only ~π CW)
    min_cum = cum_phi.min()
    max_cw_deg = -min_cum * 180 / np.pi

    # Did the vehicle go far from source? (r_max > 2 * r_start means significant excursion)
    went_far = r_max > 1.5 * r_start

    # After any excursion, does the vehicle return near orbit radius?
    # Find the orbit radius for these params
    r_orbit = r_start  # approximate

    # Look for approach to orbit after peak distance
    idx_far = np.argmax(rs)
    if idx_far < len(rs) - 100:
        # Vehicle reached max distance, check if it comes back
        post_far_rs = rs[idx_far:]
        came_back = post_far_rs.min() < r_start * 0.9
    else:
        came_back = False

    # Closure: after the excursion, when the vehicle is back near starting phi (-π/2)
    # and heading is near starting heading (0), measure the mismatch
    best_q = 999.0
    best_info = {}

    if went_far and came_back:
        # Find the return point after the far excursion
        for i in range(idx_far, len(sol.t)):
            phi_err = abs(((phis[i] + np.pi/2 + np.pi) % (2*np.pi)) - np.pi)
            r_err = abs(rs[i] - r_start)
            if phi_err < 0.3 and r_err < r_start * 0.3:
                # Heading relative to tangent
                heading_rel = (sol.y[2][i] - phis[i] - np.pi/2) % (2*np.pi)
                if heading_rel > np.pi:
                    heading_rel -= 2*np.pi
                h_err = abs(heading_rel)
                q = math.sqrt((r_err/r_start)**2 + phi_err**2 + h_err**2)
                if q < best_q:
                    best_q = q
                    best_info = {'r_err': r_err, 'phi_err': phi_err,
                                 'h_err': h_err, 't': sol.t[i], 'r_ret': rs[i]}

    return {
        'r_min': r_min, 'r_max': r_max,
        'max_cw_deg': max_cw_deg,
        'went_far': went_far, 'came_back': came_back,
        'quality': best_q, 'info': best_info
    }


# ============================================================
# SWEEP
# ============================================================
print("=" * 95)
print("FIGURE-8 SEARCH: Sweeping beta near stability transition")
print("=" * 95)

# The key insight: at beta≈1.40, I=1,440,000, the orbit is marginally stable
# At beta>1.40, orbit is unstable and vehicles escape easily
# A figure-8 lives at the boundary

I = 1_440_000

print(f"\nIntensity I = {I:,}")
print(f"Sensor: gaussian, peak={peak}, Vmax={vmax}, sigma={sigma:.1f}")
print(f"B_R = {B_R}\n")

# First find orbit radii for each beta
print(f"{'beta':>6} {'B_L':>6} {'r_orbit':>8}")
print("-" * 25)
orbits = {}
for beta in np.arange(1.30, 1.55, 0.01):
    b_left = beta * B_R
    r_orb = find_orbit_radius(I, b_left)
    if r_orb:
        orbits[round(beta, 2)] = r_orb
        print(f"{beta:6.2f} {b_left:6.3f} {r_orb:8.1f}")

print(f"\n{'beta':>6} {'r_start':>8} {'r_min':>7} {'r_max':>7} {'CW_deg':>7} {'far?':>5} {'back?':>5} {'quality':>8} {'r_err':>7} {'t_ret':>7}")
print("-" * 95)

# For each beta, try several starting distances
best_candidates = []

for beta in [1.35, 1.38, 1.39, 1.40, 1.41, 1.42, 1.43, 1.45, 1.48, 1.50]:
    b_left = beta * B_R
    r_orb = find_orbit_radius(I, b_left)
    if not r_orb:
        continue

    for mult in [1.2, 1.3, 1.4, 1.5, 1.6, 1.8, 2.0, 2.5]:
        r_start = r_orb * mult
        sol = simulate(I, b_left, r_start, t_max=800)
        info = analyze(sol, r_start)

        q_str = f"{info['quality']:8.4f}" if info['quality'] < 100 else "    ----"
        r_err_str = f"{info['info'].get('r_err', 0):7.1f}" if info['info'] else "   ----"
        t_str = f"{info['info'].get('t', 0):7.1f}" if info['info'] else "   ----"

        mark = ""
        if info['went_far'] and info['came_back']:
            mark = " ← EXCURSION"
            if info['quality'] < 1.0:
                mark = " ★ FIGURE-8 CANDIDATE"

        print(f"{beta:6.2f} {r_start:8.1f} {info['r_min']:7.1f} {info['r_max']:7.1f} "
              f"{info['max_cw_deg']:7.1f} {'Y' if info['went_far'] else '.':>5} "
              f"{'Y' if info['came_back'] else '.':>5} {q_str} {r_err_str} {t_str}{mark}")

        if info['quality'] < 5.0:
            best_candidates.append((beta, r_start, info))

# Sort and print best
if best_candidates:
    best_candidates.sort(key=lambda x: x[2]['quality'])
    print(f"\n{'='*95}")
    print(f"TOP FIGURE-8 CANDIDATES")
    print(f"{'='*95}")
    for beta, r_start, info in best_candidates[:10]:
        print(f"  beta={beta:.2f}, r_start={r_start:.1f}, "
              f"quality={info['quality']:.4f}, r_range=[{info['r_min']:.0f}, {info['r_max']:.0f}], "
              f"return: r_err={info['info'].get('r_err',0):.1f} at t={info['info'].get('t',0):.1f}")
else:
    print("\nNo good figure-8 candidates found. The CW excursion may not close.")
    print("Try adjusting beta range or using arc method (matching GUI) instead of RK45.")
