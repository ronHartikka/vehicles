#!/usr/bin/env python3
"""
find_figure8.py — Sweep starting distances to find the figure-8 boundary
just outside a stable circular orbit for a Braitenberg vehicle.

The vehicle has crossed wiring (SL->MR, SR->ML) with a Gaussian sensor
response, orbiting a point source at the origin. The stable CCW orbit
is at r≈170. We sweep starting distances from r=200..260 looking for
the starting distance where the vehicle completes exactly one full CW
excursion (the far lobe of a figure-8) and returns to close the loop.

Parameters:
  I = 2,250,000  (source intensity)
  peak_stimulus = 100
  max_voltage = 80
  sigma = peak / (2*sqrt(ln2))  (Gaussian sensor width)
  B_L = 4.84, B_R = 4.40  (base speeds)
  W = 12  (wheel separation)
  d = 24  (sensor offset from vehicle center)
  alpha = 0.3  (sensor angular offset from heading)

Usage:
  python find_figure8.py
"""

import numpy as np
from scipy.integrate import solve_ivp
import json
import os

# ─── Parameters ───────────────────────────────────────────────────────
I = 2_250_000          # source intensity
PEAK = 100.0           # peak stimulus for Gaussian response
VMAX = 80.0            # max voltage output
SIGMA = PEAK / (2.0 * np.sqrt(np.log(2)))  # ≈ 60.06
B_L = 4.84             # base speed, left wheel
B_R = 4.40             # base speed, right wheel
W = 12.0               # wheel separation
D_SENSOR = 24.0        # sensor distance from vehicle center
ALPHA = 0.3            # sensor angular offset (radians)

T_MAX = 500.0          # max integration time
R_SWEEP_LO = 200.0
R_SWEEP_HI = 260.0
R_STEP_COARSE = 1.0
R_STEP_FINE = 0.25


def gaussian_response(stim):
    """Gaussian sensor response: Vmax * exp(-(stim - peak)^2 / (2*sigma^2))"""
    return VMAX * np.exp(-((stim - PEAK) ** 2) / (2.0 * SIGMA ** 2))


def vehicle_ode(t, state):
    """ODE for a crossed-wiring Braitenberg vehicle near a point source."""
    x, y, theta = state

    # Sensor positions
    angle_L = theta + ALPHA
    angle_R = theta - ALPHA
    sx_L = x + D_SENSOR * np.cos(angle_L)
    sy_L = y + D_SENSOR * np.sin(angle_L)
    sx_R = x + D_SENSOR * np.cos(angle_R)
    sy_R = y + D_SENSOR * np.sin(angle_R)

    # Inverse-square field at each sensor
    r2_L = sx_L ** 2 + sy_L ** 2
    r2_R = sx_R ** 2 + sy_R ** 2
    stim_L = I / max(r2_L, 1.0)  # guard against division by zero
    stim_R = I / max(r2_R, 1.0)

    # Gaussian voltage responses
    V_L = gaussian_response(stim_L)
    V_R = gaussian_response(stim_R)

    # Crossed wiring: SL -> MR, SR -> ML
    speed_L = max(B_L + V_R, 0.0)
    speed_R = max(B_R + V_L, 0.0)

    # Differential drive kinematics
    fwd = (speed_L + speed_R) / 2.0
    dx = fwd * np.cos(theta)
    dy = fwd * np.sin(theta)
    dtheta = (speed_R - speed_L) / W

    return [dx, dy, dtheta]


def normalize_angle(a):
    """Normalize angle to (-pi, pi]."""
    return (a + np.pi) % (2.0 * np.pi) - np.pi


def simulate(r_start, t_max=T_MAX, dense=False):
    """
    Simulate a vehicle starting at (0, -r_start) heading east (theta=0).
    Returns the solution object from solve_ivp.
    """
    y0 = [0.0, -r_start, 0.0]  # (x, y, theta)
    sol = solve_ivp(
        vehicle_ode, [0, t_max], y0,
        method='RK45',
        rtol=1e-10, atol=1e-12,
        dense_output=dense,
        max_step=0.5,
    )
    return sol


def analyze_trajectory(sol, r_start):
    """
    Analyze a trajectory for figure-8 properties.

    Returns a dict with:
      - completed_cw_loop: bool
      - phi_total_cw: total CW angular travel (positive = CW)
      - r_min, r_max: distance extremes
      - closure_r_err: |r_return - r_start| at best return point
      - closure_heading_err: heading mismatch at best return point
      - closure_time: time of best return
      - return_quality: combined metric (lower = better figure-8)
    """
    xs, ys = sol.y[0], sol.y[1]
    thetas = sol.y[2]
    ts = sol.t

    rs = np.sqrt(xs ** 2 + ys ** 2)
    phis = np.arctan2(ys, xs)  # position angle around source

    r_min = np.min(rs)
    r_max = np.max(rs)

    # Track cumulative angular change in phi (position angle around source)
    # CW motion means phi is decreasing
    dphi = np.diff(phis)
    # Handle wraparound
    dphi = np.where(dphi > np.pi, dphi - 2 * np.pi, dphi)
    dphi = np.where(dphi < -np.pi, dphi + 2 * np.pi, dphi)
    cum_phi = np.cumsum(dphi)

    # Starting phi is atan2(-r_start, 0) = -pi/2
    # For a CW loop, cumulative phi should go negative (decrease) by ~2*pi
    # then come back up (CCW part of the orbit)

    # Find if there's a CW excursion: cum_phi goes below -2*pi at some point
    min_cum_phi = np.min(cum_phi)
    completed_cw_loop = min_cum_phi < -1.8 * np.pi  # nearly full CW loop

    # Total CW angular travel (most negative cumulative phi)
    phi_total_cw = -min_cum_phi  # positive value = CW radians

    # Look for return to starting region after the CW excursion
    # The starting state: position angle -pi/2, r = r_start, heading = 0
    # We want the vehicle to return near (0, -r_start) heading east after the loop

    # Find the time index where cumulative phi first reaches its minimum
    # (deepest CW point), then look for return after that
    idx_min_phi = np.argmin(cum_phi)

    best_closure = {
        'closure_r_err': 999.0,
        'closure_heading_err': 999.0,
        'closure_time': T_MAX,
        'return_quality': 999.0,
        'idx': -1,
    }

    if completed_cw_loop and idx_min_phi < len(ts) - 10:
        # Look for return: after the deepest CW point, when does the vehicle
        # come back near phi = -pi/2 and r ≈ r_start?
        for i in range(idx_min_phi + 1, len(ts)):
            # Position angle relative to start
            phi_err = abs(normalize_angle(phis[i] - (-np.pi / 2)))
            r_err = abs(rs[i] - r_start)

            # Heading: at the start it was 0 (east), tangent to CCW orbit
            # At return, the heading relative to position angle should be similar
            # For a CCW orbit at (0, -r), heading=0 means tangent CCW
            # We want heading relative to radial direction
            radial_angle = np.arctan2(ys[i], xs[i]) + np.pi  # angle from source to vehicle + pi = outward
            heading_rel = normalize_angle(thetas[i] - (phis[i] + np.pi / 2))
            # At start: theta=0, phi=-pi/2, so heading_rel = 0 - (-pi/2 + pi/2) = 0
            heading_err = abs(heading_rel)

            # Combined quality metric
            if phi_err < 0.5 and r_err < 50:  # only consider plausible returns
                quality = np.sqrt((r_err / r_start) ** 2 + phi_err ** 2 + heading_err ** 2)
                if quality < best_closure['return_quality']:
                    best_closure = {
                        'closure_r_err': r_err,
                        'closure_heading_err': heading_err,
                        'closure_phi_err': phi_err,
                        'closure_time': ts[i],
                        'return_quality': quality,
                        'idx': i,
                        'r_at_return': rs[i],
                        'phi_at_return': phis[i],
                        'heading_at_return': thetas[i],
                    }

    return {
        'completed_cw_loop': completed_cw_loop,
        'phi_total_cw_deg': np.degrees(phi_total_cw),
        'r_min': r_min,
        'r_max': r_max,
        **best_closure,
    }


def run_sweep():
    """Run the coarse + fine sweep and return sorted results."""
    print("=" * 90)
    print("BRAITENBERG FIGURE-8 FINDER")
    print("=" * 90)
    print(f"Source intensity I = {I:,.0f}")
    print(f"Peak stimulus = {PEAK}, Vmax = {VMAX}, sigma = {SIGMA:.4f}")
    print(f"Base speeds: B_L = {B_L}, B_R = {B_R}")
    print(f"Wheel sep W = {W}, Sensor dist d = {D_SENSOR}, Sensor angle alpha = {ALPHA}")
    print(f"Stable orbit at r ~ 170, sweeping r_start = {R_SWEEP_LO}..{R_SWEEP_HI}")
    print(f"Integration: RK45, rtol=1e-10, atol=1e-12, t_max={T_MAX}")
    print()

    # Phase 1: Coarse sweep
    print("Phase 1: Coarse sweep (step = {})".format(R_STEP_COARSE))
    print("-" * 90)

    results = []
    r_values_coarse = np.arange(R_SWEEP_LO, R_SWEEP_HI + 0.01, R_STEP_COARSE)

    header = (
        f"{'r_start':>8s}  {'CW?':>4s}  {'CW_deg':>8s}  "
        f"{'r_min':>7s}  {'r_max':>7s}  "
        f"{'dR':>7s}  {'dPhi':>6s}  {'dHdg':>6s}  "
        f"{'Quality':>8s}  {'t_ret':>6s}"
    )
    print(header)
    print("-" * 90)

    for r0 in r_values_coarse:
        sol = simulate(r0)
        if sol.status != 0 and sol.status != 1:
            print(f"{r0:8.1f}  FAILED (status={sol.status})")
            continue
        info = analyze_trajectory(sol, r0)
        cw_str = "YES" if info['completed_cw_loop'] else "no"
        q_str = f"{info['return_quality']:8.4f}" if info['return_quality'] < 100 else "    ----"
        dr_str = f"{info['closure_r_err']:7.2f}" if info['closure_r_err'] < 100 else "   ----"
        dphi_str = f"{info.get('closure_phi_err', 999):6.3f}" if info.get('closure_phi_err', 999) < 10 else "  ----"
        dhdg_str = f"{info['closure_heading_err']:6.3f}" if info['closure_heading_err'] < 10 else "  ----"
        t_str = f"{info['closure_time']:6.1f}" if info['closure_time'] < T_MAX else "  ----"

        print(
            f"{r0:8.1f}  {cw_str:>4s}  {info['phi_total_cw_deg']:8.1f}  "
            f"{info['r_min']:7.1f}  {info['r_max']:7.1f}  "
            f"{dr_str}  {dphi_str}  {dhdg_str}  "
            f"{q_str}  {t_str}"
        )
        results.append((r0, info))

    # Find the best candidates from coarse sweep
    cw_results = [(r0, info) for r0, info in results if info['completed_cw_loop']]

    if not cw_results:
        print("\nNo CW loops found in coarse sweep. Try wider range or longer t_max.")
        return results

    # Sort by return quality
    cw_results.sort(key=lambda x: x[1]['return_quality'])
    best_coarse = cw_results[0]
    print(f"\nBest coarse candidate: r_start = {best_coarse[0]:.1f}, quality = {best_coarse[1]['return_quality']:.4f}")

    # Phase 2: Fine sweep around the best candidate
    fine_center = best_coarse[0]
    fine_lo = max(R_SWEEP_LO, fine_center - 5.0)
    fine_hi = min(R_SWEEP_HI, fine_center + 5.0)

    print(f"\nPhase 2: Fine sweep around r = {fine_center:.1f} (step = {R_STEP_FINE})")
    print("-" * 90)
    print(header)
    print("-" * 90)

    fine_results = []
    r_values_fine = np.arange(fine_lo, fine_hi + 0.01, R_STEP_FINE)

    for r0 in r_values_fine:
        sol = simulate(r0)
        if sol.status != 0 and sol.status != 1:
            continue
        info = analyze_trajectory(sol, r0)
        cw_str = "YES" if info['completed_cw_loop'] else "no"
        q_str = f"{info['return_quality']:8.4f}" if info['return_quality'] < 100 else "    ----"
        dr_str = f"{info['closure_r_err']:7.2f}" if info['closure_r_err'] < 100 else "   ----"
        dphi_str = f"{info.get('closure_phi_err', 999):6.3f}" if info.get('closure_phi_err', 999) < 10 else "  ----"
        dhdg_str = f"{info['closure_heading_err']:6.3f}" if info['closure_heading_err'] < 10 else "  ----"
        t_str = f"{info['closure_time']:6.1f}" if info['closure_time'] < T_MAX else "  ----"

        print(
            f"{r0:8.2f}  {cw_str:>4s}  {info['phi_total_cw_deg']:8.1f}  "
            f"{info['r_min']:7.1f}  {info['r_max']:7.1f}  "
            f"{dr_str}  {dphi_str}  {dhdg_str}  "
            f"{q_str}  {t_str}"
        )
        fine_results.append((r0, info))

    # Combine and find overall best
    all_cw = [(r0, info) for r0, info in fine_results if info['completed_cw_loop']]
    if all_cw:
        all_cw.sort(key=lambda x: x[1]['return_quality'])
        best = all_cw[0]
    else:
        best = best_coarse

    print("\n" + "=" * 90)
    print("TOP 10 FIGURE-8 CANDIDATES (sorted by closure quality)")
    print("=" * 90)

    all_candidates = [(r0, info) for r0, info in results + fine_results if info['completed_cw_loop']]
    # Deduplicate by r_start (prefer fine results)
    seen = {}
    for r0, info in all_candidates:
        key = round(r0, 2)
        if key not in seen or info['return_quality'] < seen[key][1]['return_quality']:
            seen[key] = (r0, info)
    unique_candidates = sorted(seen.values(), key=lambda x: x[1]['return_quality'])

    print(f"{'Rank':>4s}  {'r_start':>8s}  {'CW_deg':>8s}  {'r_min':>7s}  {'r_max':>7s}  "
          f"{'dR':>7s}  {'dPhi':>6s}  {'Quality':>8s}  {'t_return':>8s}")
    print("-" * 90)
    for rank, (r0, info) in enumerate(unique_candidates[:10], 1):
        dr_str = f"{info['closure_r_err']:7.2f}" if info['closure_r_err'] < 100 else "   ----"
        dphi_str = f"{info.get('closure_phi_err', 999):6.3f}" if info.get('closure_phi_err', 999) < 10 else "  ----"
        q_str = f"{info['return_quality']:8.4f}" if info['return_quality'] < 100 else "    ----"
        t_str = f"{info['closure_time']:8.1f}" if info['closure_time'] < T_MAX else "    ----"
        print(
            f"{rank:4d}  {r0:8.2f}  {info['phi_total_cw_deg']:8.1f}  "
            f"{info['r_min']:7.1f}  {info['r_max']:7.1f}  "
            f"{dr_str}  {dphi_str}  {q_str}  {t_str}"
        )

    # Phase 3: Plot the best candidate
    print(f"\nBest figure-8 candidate: r_start = {best[0]:.2f}")
    print(f"  CW excursion: {best[1]['phi_total_cw_deg']:.1f} degrees")
    print(f"  r range: [{best[1]['r_min']:.1f}, {best[1]['r_max']:.1f}]")
    print(f"  Closure error: dR={best[1]['closure_r_err']:.2f}, quality={best[1]['return_quality']:.4f}")
    print(f"  Return time: {best[1]['closure_time']:.1f}")

    plot_best(best[0], unique_candidates[:6])

    # Write JSON config with top 6 candidates
    write_config(unique_candidates[:6])

    return unique_candidates


def plot_best(r_best, top_candidates):
    """Plot the trajectory of the best figure-8 candidate."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        print("\nMatplotlib not available — skipping plot.")
        return

    fig, axes = plt.subplots(1, 2, figsize=(18, 9))

    # Left panel: best trajectory
    ax = axes[0]
    sol = simulate(r_best, t_max=T_MAX)
    xs, ys = sol.y[0], sol.y[1]

    # Color by time
    points = np.array([xs, ys]).T.reshape(-1, 1, 2)
    from matplotlib.collections import LineCollection
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    lc = LineCollection(segments, cmap='viridis', linewidth=1.0)
    lc.set_array(sol.t[:-1])
    ax.add_collection(lc)
    plt.colorbar(lc, ax=ax, label='time')

    # Mark source, start, stable orbit
    ax.plot(0, 0, 'r*', markersize=15, label='Source')
    ax.plot(xs[0], ys[0], 'go', markersize=10, label=f'Start r={r_best:.1f}')
    theta_circ = np.linspace(0, 2 * np.pi, 200)
    ax.plot(170 * np.cos(theta_circ), 170 * np.sin(theta_circ), 'r--', alpha=0.3, label='Stable orbit r=170')

    ax.set_xlim(np.min(xs) - 50, np.max(xs) + 50)
    ax.set_ylim(np.min(ys) - 50, np.max(ys) + 50)
    ax.set_aspect('equal')
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.set_title(f'Best Figure-8 Candidate: r_start = {r_best:.2f}')
    ax.legend(loc='upper right', fontsize=8)
    ax.grid(True, alpha=0.3)

    # Right panel: r(t) for top candidates
    ax2 = axes[1]
    colors = plt.cm.tab10(np.linspace(0, 1, min(len(top_candidates), 6)))
    for idx, (r0, info) in enumerate(top_candidates[:6]):
        sol_i = simulate(r0, t_max=T_MAX)
        rs_i = np.sqrt(sol_i.y[0] ** 2 + sol_i.y[1] ** 2)
        ax2.plot(sol_i.t, rs_i, color=colors[idx], label=f'r={r0:.1f} (q={info["return_quality"]:.3f})')

    ax2.axhline(170, color='red', linestyle='--', alpha=0.5, label='Stable orbit r=170')
    ax2.set_xlabel('time')
    ax2.set_ylabel('distance from source')
    ax2.set_title('Distance vs Time for Top Candidates')
    ax2.legend(fontsize=7)
    ax2.grid(True, alpha=0.3)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    plot_path = os.path.join(script_dir, 'figure8_candidates.png')
    plt.tight_layout()
    plt.savefig(plot_path, dpi=150)
    print(f"\nPlot saved to: {plot_path}")
    plt.close()


def write_config(top_candidates):
    """Write a JSON config file with the top 6 candidates."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_dir = os.path.join(script_dir, 'configs')
    os.makedirs(config_dir, exist_ok=True)
    config_path = os.path.join(config_dir, 'vehicle_4a_figure8_sweep.json')

    colors = [
        [255, 0, 0],       # red
        [0, 200, 0],       # green
        [0, 100, 255],     # blue
        [255, 165, 0],     # orange
        [180, 0, 255],     # purple
        [0, 200, 200],     # cyan
    ]

    vehicles = []
    for idx, (r0, info) in enumerate(top_candidates[:6]):
        vehicles.append({
            "name": f"fig8_r{r0:.1f}",
            "x": 0.0,
            "y": -r0,
            "heading": 0.0,
            "sensor_type": "gaussian",
            "peak_stimulus": PEAK,
            "max_voltage": VMAX,
            "base_left": B_L,
            "base_right": B_R,
            "wiring": "crossed",
            "sensor_distance": D_SENSOR,
            "sensor_angle": ALPHA,
            "wheel_separation": W,
            "max_speed": 150,
            "method": "arc",
            "color": colors[idx % len(colors)],
            "trail": True,
        })

    config = {
        "description": "Figure-8 boundary sweep: 6 vehicles at promising starting distances near the escape/capture boundary",
        "source": {
            "x": 0,
            "y": 0,
            "intensity": I,
        },
        "view": {
            "center_x": 0,
            "center_y": -200,
            "zoom": 0.25,
        },
        "dt": 0.05,
        "vehicles": vehicles,
    }

    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    print(f"Config saved to: {config_path}")
    print(f"  Contains {len(vehicles)} vehicles at r_start = {[round(r0, 2) for r0, _ in top_candidates[:6]]}")


if __name__ == '__main__':
    run_sweep()
