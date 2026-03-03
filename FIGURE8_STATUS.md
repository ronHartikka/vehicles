# Figure-8 Orbit Search - Status (Tabled)

## Conclusion

**The single-source symmetric figure-8 search is tabled.** Two fundamental obstacles:

### 1. Mirror symmetry is essentially impossible
The turning bias β = B_L/B_R gives the vehicle a fixed chirality — it always curves the same
direction. A mirror-symmetric figure-8 would require the vehicle to curve CW in one lobe and
CCW in the other (since the lobes are traversals in opposite global senses). The fixed β
prevents this. This system is unlike a planet+star (Kepler problem):

| Property | Kepler orbit | This vehicle |
|---|---|---|
| Force depends on | position only | position **and heading** |
| Time-reversal symmetry | yes | no (bias flips handedness) |
| Angular momentum | conserved | not conserved |
| Mirror-symmetric orbits | guaranteed | not available |

### 2. The confirmed closed orbit is NOT topologically a figure-8
The 2-lobe orbit (k=-0.0210, I=273205, B_L=5.0, B_R=4.0) has **14 self-intersection points**
per period — far from the single crossing of a true figure-8. The "2-lobe" label refers to
the Poincaré section topology (2 crossings of the y=-100 line per period), not the visual
shape. The orbit is better described as a **spirograph** or dense interlaced curve, with the
vehicle making multiple passes near the source each period.

Time is also not split evenly: outer arc ≈ 100 time units (62%), inner region ≈ 62 time
units (38%), with two distinct close-approach segments (d < 150 from source) per period.

## The Confirmed 2-Lobe Closed Orbit

**Config**: `configs/vehicle_4a_2lobe_closed_orbit.json`

| Parameter | Value |
|-----------|-------|
| B_L / B_R | 5.0 / 4.0 |
| Source intensity | 273205 |
| Gradient k | -0.0210 |
| Period | 162.04 time units |
| \|λ\| (Floquet) | 0.256 (strongly stable) |
| Self-intersections per period | 14 |
| Bounding box | x: [-132, 312], y: [-148, 228] |
| Starting point | x=-52.922, y=-100, θ=2.608 rad |

See [docs/closed-orbits.md](docs/closed-orbits.md) for full analysis.

## On Braitenberg's Figure 7

Braitenberg shows what appears to be a symmetric figure-8 for Vehicle 4a exposed to one
source, with two perpendicular lines of mirror symmetry. He says little about sources and
does not show the wiring. We introduced a linear gradient (which he does not forbid) and
found closed orbits — but not symmetric ones. Whether Braitenberg's figure depicts an
idealized schematic or a true periodic orbit for a specific wiring/parameter combination
remains an open question.
