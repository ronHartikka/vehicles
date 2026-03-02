#!/usr/bin/env python3
"""
Zero-curvature analysis for symmetric figure-8 orbits.

At perihelion P and aphelion A on the symmetry line L, heading ⊥ to L,
zero curvature requires G(r_P, I) = G(r_A, I), where:
    G(r, I) = V_SR(r,I) - V_SL(r,I)

This condition is independent of β = B_L/B_R.

Vehicle params: d=24, α=0.3, V_max=50, f_p=100, W=12, inverse-square source.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import brentq

# Vehicle parameters
d = 24.0        # sensor arm length
alpha = 0.3     # sensor angle offset (rad)
V_max = 50.0    # bell response max voltage
f_p = 100.0     # bell peak stimulus
W = 12.0        # axle width
sin_alpha = np.sin(alpha)  # ≈ 0.2955


def bell(f):
    """Bell sensor response (vectorized)."""
    f = np.asarray(f, dtype=float)
    result = np.zeros_like(f)
    mask = (f > 0) & (f < 2 * f_p)
    norm = (f[mask] - f_p) / f_p
    result[mask] = V_max * (1.0 - norm**2)
    return result


def G(r, I):
    """V_SR - V_SL when vehicle is at distance r from source, heading ⊥ to radial.

    Left sensor is closer to source (r_L < r_R), so typically V_SL > V_SR, G < 0.
    """
    r = np.asarray(r, dtype=float)
    r_L_sq = r**2 + d**2 - 2 * r * d * sin_alpha
    r_R_sq = r**2 + d**2 + 2 * r * d * sin_alpha
    f_L = I / np.maximum(r_L_sq, 1e-10)
    f_R = I / np.maximum(r_R_sq, 1e-10)
    return bell(f_R) - bell(f_L)


def G_scalar(r, I):
    """Scalar version of G for root-finding."""
    r_L_sq = r**2 + d**2 - 2 * r * d * sin_alpha
    r_R_sq = r**2 + d**2 + 2 * r * d * sin_alpha
    f_L = I / max(r_L_sq, 1e-10)
    f_R = I / max(r_R_sq, 1e-10)
    return float(bell(np.array([f_R]))[0] - bell(np.array([f_L]))[0])


def natural_turning_radius(beta):
    """Turning radius with no source. β = B_L/B_R > 1 for CW turning."""
    if abs(beta - 1.0) < 1e-10:
        return float('inf')
    return W * (1 + beta) / (2 * abs(beta - 1))


def find_pairs(I_val, r_range, n_points=2000):
    """Find all (r_P, r_A) pairs where G(r_P, I) = G(r_A, I).

    Returns list of (r_P, r_A, G_level) tuples.
    """
    r = np.linspace(r_range[0], r_range[1], n_points)
    g = G(r, I_val)

    # Find the minimum of G (most negative point)
    g_min_idx = np.argmin(g)
    g_min = g[g_min_idx]
    r_at_min = r[g_min_idx]

    if g_min >= 0:
        return [], r, g, r_at_min

    # Sweep levels from near 0 to near g_min
    n_levels = 100
    levels = np.linspace(g_min * 0.02, g_min * 0.98, n_levels)

    pairs = []
    for level in levels:
        # Find r_P < r_at_min where G(r_P) = level
        # Find r_A > r_at_min where G(r_A) = level
        g_shifted = g - level

        # Left side (r < r_at_min)
        left_mask = r < r_at_min
        r_left = r[left_mask]
        g_left = g_shifted[left_mask]

        # Right side (r > r_at_min)
        right_mask = r > r_at_min
        r_right = r[right_mask]
        g_right = g_shifted[right_mask]

        if len(r_left) < 2 or len(r_right) < 2:
            continue

        # Find sign changes
        sc_left = np.where(np.diff(np.sign(g_left)))[0]
        sc_right = np.where(np.diff(np.sign(g_right)))[0]

        if len(sc_left) == 0 or len(sc_right) == 0:
            continue

        try:
            # Rightmost left crossing = perihelion
            idx_l = sc_left[-1]
            r_P = brentq(lambda x: G_scalar(x, I_val) - level,
                         r_left[idx_l], r_left[idx_l + 1], xtol=1e-8)

            # Leftmost right crossing = aphelion
            idx_r = sc_right[0]
            r_A = brentq(lambda x: G_scalar(x, I_val) - level,
                         r_right[idx_r], r_right[idx_r + 1], xtol=1e-8)

            pairs.append((r_P, r_A, level))
        except (ValueError, IndexError):
            continue

    return pairs, r, g, r_at_min


def main():
    # ============================================================
    # Figure 1: G(r) curves for various I
    # ============================================================
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    r_plot = np.linspace(5, 500, 3000)
    I_values = [50_000, 100_000, 150_000, 200_000, 300_000, 500_000]

    ax = axes[0, 0]
    for I_val in I_values:
        g = G(r_plot, I_val)
        ax.plot(r_plot, g, label=f'I={I_val/1000:.0f}k')
    ax.axhline(0, color='k', linewidth=0.5)
    ax.set_xlabel('r (distance from source)')
    ax.set_ylabel('G(r) = V_SR − V_SL')
    ax.set_title('Sensor voltage difference (heading ⊥ radial)')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # ============================================================
    # Figure 2: Compatible (r_P, r_A) pairs
    # ============================================================
    ax2 = axes[0, 1]
    I_scan = [100_000, 150_000, 200_000, 250_000, 300_000, 400_000]

    all_results = {}
    for I_val in I_scan:
        pairs, r, g, r_min = find_pairs(I_val, (5, 500))
        all_results[I_val] = pairs
        if pairs:
            rP = [p[0] for p in pairs]
            rA = [p[1] for p in pairs]
            ax2.plot(rP, rA, '-', linewidth=2, label=f'I={I_val/1000:.0f}k')

    ax2.set_xlabel('r_P (perihelion distance)')
    ax2.set_ylabel('r_A (aphelion distance)')
    ax2.set_title('Compatible (r_P, r_A) pairs: G(r_P) = G(r_A)')
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3)

    # ============================================================
    # Figure 3: Required ΔB = B_L - B_R for each pair
    # ============================================================
    ax3 = axes[1, 0]
    for I_val in I_scan:
        pairs = all_results[I_val]
        if pairs:
            rP = [p[0] for p in pairs]
            delta_B = [-p[2] for p in pairs]  # B_L - B_R = -(B_R - B_L) = -G
            ax3.plot(rP, delta_B, '-', linewidth=2, label=f'I={I_val/1000:.0f}k')

    ax3.set_xlabel('r_P (perihelion distance)')
    ax3.set_ylabel('ΔB = B_L − B_R (required)')
    ax3.set_title('Required bias difference vs perihelion')
    ax3.legend(fontsize=8)
    ax3.grid(True, alpha=0.3)

    # ============================================================
    # Figure 4: Aphelion/perihelion ratio
    # ============================================================
    ax4 = axes[1, 1]
    for I_val in I_scan:
        pairs = all_results[I_val]
        if pairs:
            rP = [p[0] for p in pairs]
            ratio = [p[1] / p[0] for p in pairs]
            ax4.plot(rP, ratio, '-', linewidth=2, label=f'I={I_val/1000:.0f}k')

    ax4.set_xlabel('r_P (perihelion distance)')
    ax4.set_ylabel('r_A / r_P')
    ax4.set_title('Aphelion-to-perihelion ratio')
    ax4.legend(fontsize=8)
    ax4.grid(True, alpha=0.3)

    plt.suptitle('Zero-curvature conditions for figure-8 orbits\n'
                 f'd={d}, α={alpha}, V_max={V_max}, f_p={f_p}, inverse-square source',
                 fontsize=12, y=1.02)
    plt.tight_layout()
    plt.savefig('zero_curvature_solutions.png', dpi=150, bbox_inches='tight')
    print("Saved zero_curvature_solutions.png")

    # ============================================================
    # Print summary table
    # ============================================================
    print("\n" + "="*80)
    print("ZERO-CURVATURE SOLUTION SUMMARY")
    print("="*80)
    print(f"{'I':>10s}  {'r_P':>8s}  {'r_A':>8s}  {'r_A/r_P':>8s}  {'ΔB':>8s}  "
          f"{'β(B_R=4)':>8s}  {'R₀':>8s}")
    print("-"*80)

    # r where bell peaks: I/r² = f_p → r_peak = sqrt(I/f_p)
    for I_val in I_scan:
        pairs = all_results[I_val]
        if not pairs:
            print(f"{I_val:10.0f}  {'no solutions':>40s}")
            continue

        r_peak = np.sqrt(I_val / f_p)

        # Show a few representative pairs: tightest, middle, widest
        indices = [0, len(pairs)//4, len(pairs)//2, 3*len(pairs)//4, -1]
        for i, idx in enumerate(indices):
            rP, rA, g_level = pairs[idx]
            delta_B = -g_level  # B_L - B_R

            # β for a reference B_R = 4.0
            B_R_ref = 4.0
            beta_ref = 1 + delta_B / B_R_ref
            R0 = natural_turning_radius(beta_ref)

            prefix = f"{I_val:10.0f}" if i == 0 else " " * 10
            print(f"{prefix}  {rP:8.1f}  {rA:8.1f}  {rA/rP:8.2f}  {delta_B:8.3f}  "
                  f"{beta_ref:8.4f}  {R0:8.1f}")

        print(f"{'':10s}  r_peak = {r_peak:.1f}")
        print()

    # ============================================================
    # Figure 5: Detailed G(r) for I=220,000 (current config)
    # ============================================================
    fig2, ax5 = plt.subplots(1, 1, figsize=(10, 6))
    I_current = 220_000
    r_detail = np.linspace(5, 400, 3000)
    g_detail = G(r_detail, I_current)

    ax5.plot(r_detail, g_detail, 'b-', linewidth=2)
    ax5.axhline(0, color='k', linewidth=0.5)

    # Mark the minimum
    g_min_idx = np.argmin(g_detail)
    ax5.plot(r_detail[g_min_idx], g_detail[g_min_idx], 'rv', markersize=10,
             label=f'G_min = {g_detail[g_min_idx]:.2f} at r = {r_detail[g_min_idx]:.1f}')

    # Mark r_peak
    r_peak = np.sqrt(I_current / f_p)
    ax5.axvline(r_peak, color='orange', linestyle='--', alpha=0.7,
                label=f'r_peak = √(I/f_p) = {r_peak:.1f}')

    # Show a few example pairing levels
    pairs_220, _, _, _ = find_pairs(I_current, (5, 400))
    if pairs_220:
        for idx in [len(pairs_220)//4, len(pairs_220)//2, 3*len(pairs_220)//4]:
            rP, rA, level = pairs_220[idx]
            ax5.axhline(level, color='gray', linestyle=':', alpha=0.5)
            ax5.plot([rP, rA], [level, level], 'ro-', markersize=6)
            ax5.annotate(f'r_P={rP:.0f}, r_A={rA:.0f}',
                        xy=(rA, level), fontsize=8,
                        xytext=(rA + 10, level + 0.5))

    ax5.set_xlabel('r (distance from source)')
    ax5.set_ylabel('G(r) = V_SR − V_SL')
    ax5.set_title(f'G(r) for I = {I_current:,} with example (r_P, r_A) pairings')
    ax5.legend()
    ax5.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('G_detail_220k.png', dpi=150, bbox_inches='tight')
    print("Saved G_detail_220k.png")


if __name__ == '__main__':
    main()
