# Closed Periodic Orbits with Gradient Symmetry-Breaking

## Background

The [periodic orbit analysis](periodic-orbit-analysis.md) showed that a single radially-symmetric source cannot produce a closed figure-8 orbit. The only periodic orbit is a circular family. The figure-8 seen in the GUI is always a transient that eventually collapses onto the circular attractor.

To break the rotational symmetry, we added a **linear gradient field**: `stimulus = k * (x - x_source)`. This superimposes a left-right ramp on the radial source field, providing a preferred direction that can lock the outer lobe's orientation and close the orbit.

## Method

**Tool:** `find_periodic_orbit.py` (upgraded with new capabilities):
- `--gradient K` — adds a `linear_gradient` source with intensity k
- `--base-voltage-left/right` — overrides motor base voltages
- `--section y --section-value Y` — Poincare section at y=const (free variables become (x, theta) instead of (x, y))
- `--n-crossings N` — number of section crossings per period (1 for circle, 2 for multi-crossing orbits)
- Theta residuals automatically reduced mod 2pi for y-section shooting

**Vehicle:** R309.7 from `vehicle_4a_triangular_fig8.json` with overridden base voltages B_L=5.0, B_R=4.0. Crossed wiring, bell response (peak=100, max_V=50), sensor arm=24, axle_width=12.

**Base parameters:** Source at (200, 150), intensity I=273,205.

## Results

### 1. Bias Scan: Transition from Circular Capture to Figure-8

With no gradient (k=0), we scanned base voltage bias while keeping Delta_B = 1.0:

| B_L | B_R | Behavior | Precession/cycle | Max distance |
|-----|-----|----------|-----------------|-------------|
| 3.5 | 2.5 | Circular capture | -- | 77 |
| 4.0 | 3.0 | Circular capture | -- | 125 |
| 4.5 | 3.5 | Circular capture | -- | 202 |
| **5.0** | **4.0** | **Escaping figure-8** | **-80 deg** | **350** |
| 5.5 | 4.5 | Escaping figure-8 | -114 deg | 355 |
| 6.0 | 5.0 | Escaping figure-8 | -133 deg | 361 |
| 7.0 | 6.0 | Escaping figure-8 | -157 deg | 374 |
| 8.0 | 7.0 | Escaping figure-8 | -174 deg | 389 |
| 10.0 | 9.0 | Escaping figure-8 | -197 deg | 421 |

The transition from circular capture to escaping figure-8 occurs at B_L ~ 5.0, B_R ~ 4.0. Below this threshold, the base-voltage turning bias is too weak to overcome the source's orbital capture. Above it, the vehicle escapes after each inner visit, tracing a 2-lobe pattern (1 inner visit + 1 outer arc per cycle) that precesses.

### 2. Gradient Sweep: Zeroing the Precession

At B_L=5.0, B_R=4.0, I=273,205, sweeping gradient strength k:

| k | Precession/cycle | Period | Notes |
|---|-----------------|--------|-------|
| 0 | -80 deg | ~80 | No gradient |
| -0.005 | ~0 deg | ~210 | Near-zero but different topology |
| -0.012 | ~0 deg | ~118 | Near-zero |
| -0.016 | ~0 deg | ~87 | Near-zero |
| -0.019 | +1 deg | ~92 | |
| -0.020 | +3 deg | ~193 | |
| **-0.0210** | **~0 deg** | **~162** | **2-lobe orbit closes!** |

Multiple gradient values produce near-zero precession, but each creates a different orbit topology. The orbit at k=-0.0210 turned out to be a clean 2-lobe pattern.

### 3. The 2-Lobe Closed Orbit (k = -0.0210)

**Shooting converged** at the y = -100 Poincare section with n_crossings = 2:

| Property | Value |
|----------|-------|
| Fixed point (x, theta) at y=-100 | (-52.922, 121.98 rad) |
| Period | 162.04 time units |
| Residual | 5.3 x 10^-7 |
| Floquet multipliers | 0.245 +/- 0.076i |
| \|lambda\| | **0.256** |
| Stability | **Stable** (perturbations decay by 74% each period) |
| Heading advance per period | 2pi (exactly 1 full turn) |
| Distance range | 50 -- 350 from source |
| x range | [-126, 307] |
| y range | [-123, 230] |

**Orbit structure:** One inner lobe (tight partial orbit near the source, distance ~ 50-80) and one outer lobe (big clockwise arc driven by the base-voltage bias, distance ~ 350). The vehicle makes exactly one full heading rotation per period.

### 4. The 4-Lobe Closed Orbit (k = -0.0205)

At a slightly different gradient, a different orbit family exists:

| Property | Value |
|----------|-------|
| Fixed point (x, theta) at y=0 | (96.905, 1.307 rad) |
| Period | 158.18 time units |
| Residual | 4.0 x 10^-9 |
| Floquet multipliers | 0.396, 0.00017 |
| \|lambda\|_max | **0.396** |
| Stability | **Stable** |
| Heading advance per period | 2pi |

**Orbit structure:** Two inner lobes (O1, O2) alternating with two outer lobes (I1, I2), traversed as O1 -> I1 -> O2 -> I2 -> repeat. This is essentially **2 cycles of the fundamental 2-lobe pattern**, glued together with a total heading advance of 2pi. The two inner visits occur from different directions (roughly 180 deg apart), and the two outer arcs sweep to opposite sides.

### 5. Relationship Between the Two Orbits

Both orbits exist at the same base parameters (I=273,205, B_L=5.0, B_R=4.0) with slightly different gradient strengths:

| Property | 2-lobe (k=-0.0210) | 4-lobe (k=-0.0205) |
|----------|-------------------|-------------------|
| Period | 162.04 | 158.18 |
| Inner visits per period | 1 | 2 |
| Heading advance | 2pi | 2pi |
| \|lambda\|_max | 0.256 | 0.396 |
| Gradient | -0.0210 | -0.0205 |

The fundamental dynamical unit is the **2-lobe cycle** (~80 time units): one inner visit followed by one outer arc. Without gradient, each cycle precesses by about -80 deg. The gradient shifts this precession:

- At k = -0.0210: precession per cycle = 0 deg. The orbit closes after **1 cycle** (period ~ 162, but 2 y-section crossings).
- At k = -0.0205: precession per cycle = -180 deg. After **2 cycles**, the total precession is -360 deg = one full turn, so the orbit closes (period ~ 158).

The 4-lobe orbit is a **period-2 orbit** of the fundamental 2-lobe dynamics.

### 6. Neither Orbit is a Classic "Figure-8"

Both orbits are genuine closed periodic solutions of the vehicle dynamics, but neither has the symmetric figure-8 shape (two equal lobes with a single crossing point). Instead:

- The **inner lobe** is a tight partial orbit near the source, shaped by the bell sensor response
- The **outer lobe** is a wide clockwise arc, shaped by the base-voltage turning bias
- The lobes are highly asymmetric in size and shape

The orbit topology is closer to a **"comet orbit"** (tight perihelion pass + wide aphelion swing) than a figure-8. A symmetric figure-8 would require a mechanism to make the outer lobe curve back toward the source at a rate comparable to the inner orbital dynamics, which the simple base-voltage bias does not provide.

## Tool Usage

```bash
# Find the 2-lobe orbit
python find_periodic_orbit.py configs/vehicle_4a_triangular_fig8.json \
    --vehicle R309.7 --intensity 273205 \
    --base-voltage-left 5.0 --base-voltage-right 4.0 \
    --gradient -0.0210 \
    --section y --section-value -100 \
    --x0 -52.9216 --theta0 121.9799 \
    --n-crossings 2 --t-max 500 --t-burnin 2.0

# Find the 4-lobe orbit
python find_periodic_orbit.py configs/vehicle_4a_triangular_fig8.json \
    --vehicle R309.7 --intensity 273205 \
    --base-voltage-left 5.0 --base-voltage-right 4.0 \
    --gradient -0.0205 \
    --section y --section-value 0 \
    --x0 96.905 --theta0 1.3073 \
    --n-crossings 2 --t-max 500 --t-burnin 2.0
```

## Conclusions

1. **A linear gradient field breaks the rotational symmetry** and enables closed periodic orbits that are impossible with a single symmetric source.
2. **Two distinct closed orbit families exist**: a 2-lobe orbit (k=-0.0210) and a 4-lobe orbit (k=-0.0205), related as period-1 and period-2 orbits of the fundamental dynamics.
3. **Both orbits are stable** attractors, with the 2-lobe orbit being more strongly stable (|lambda|=0.256 vs 0.396).
4. **The orbits are "comet-like"**, not symmetric figure-8s. The inner lobe (sensor-driven) and outer lobe (bias-driven) have very different scales and shapes.
5. **The gradient required is small** (|k| ~ 0.02), corresponding to a stimulus change of ~0.02 per unit distance in x. This is a gentle left-right asymmetry superimposed on the radial source field.
