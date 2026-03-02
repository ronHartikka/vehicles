# Figure-8 Orbit Search - Current Status

## Latest Results (2026-02-27)

### Current Configuration
- **File**: `configs/vehicle_4a_figure8_sweep_ron.json`
- **β = 1.356** (constant across all vehicles)
- **k sweep**: 1.0000 to 1.0020 (6 vehicles, steps of 0.0004)
- **Starting position**: (0, -716) heading west
- **I = 1,440,000**, gaussian sensor, peak=100, Vmax=80
- **Reference orbit**: r=147 (orange circle)

### Vehicle Parameters
| k      | B_L   | B_R   |
|--------|-------|-------|
| 1.0000 | 5.966 | 4.400 |
| 1.0004 | 5.968 | 4.402 |
| 1.0008 | 5.971 | 4.404 |
| 1.0012 | 5.973 | 4.405 | ← **BEST (yellow)**
| 1.0016 | 5.976 | 4.407 |
| 1.0020 | 5.978 | 4.409 |

## Key Finding

**Yellow vehicle (k=1.0012)** produces the best figure-8 so far:
- ✓ Completes both lobes
- ✓ Returns very close to starting point
- ✗ **Problem**: Enters inside the circular orbit (r=147) during inner lobe

The trajectory is nearly closed but the inner lobe goes too close to the source.

## Recommendations for Next Step

### Option 1: Fine-tune k (Recommended)
**Keep β=1.356 constant, narrow the k sweep around 1.0012**

Try k = 1.0012 to 1.0020 (6 vehicles)
- Higher k → faster vehicle → less source influence → stays further from source
- Preserves outer lobe shape (β constant)
- Only adjusts inner lobe behavior
- Likely answer: k ≈ 1.0014 or 1.0015

### Option 2: Increase β
**Keep k=1.0012, increase β to ~1.36-1.37**

- Stronger CW bias → more resistance to source deflection
- Changes both inner and outer lobe curvature
- Outer lobe becomes tighter (smaller radius)

## Technical Context

**The k parameter** is a scale factor for both base voltages:
- B_L = k × 5.966
- B_R = k × 4.400
- β = B_L/B_R stays constant

**Why k matters for the inner lobe:**
1. Higher k → higher forward speed → less time near source
2. Higher k → sensor voltage becomes smaller fraction of total motor command
3. Both effects reduce source influence on trajectory

**Outer lobe curvature** (far from source):
- R_outer = W(β+1)/(2(β-1)) ≈ 33 units for β=1.356
- Independent of k (depends only on β)
- Actual spatial extent larger due to source influence even at r=200-300

## History

- Started with β=1.45, k=0.85-1.15 sweep
- Found β=1.356 better than β=1.45
- Narrowed to k=1.0-1.01
- Narrowed to k=1.0-1.002
- Current: k=1.0-1.002 found k=1.0012 as best candidate
