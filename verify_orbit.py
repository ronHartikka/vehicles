"""Verify circular orbit stability using high-precision integration (scipy).

Compares: exact ODE (RK45 adaptive), arc method, and Euler method.
Tracks distance from source over time to detect drift/precession.
"""

import math
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

# Parameters (same as config)
I = 2_250_000
peak_stimulus = 100.0
max_voltage = 80.0
sigma = peak_stimulus / (2.0 * math.sqrt(math.log(2)))
W = 12          # axle width
d = 24          # sensor distance from center
alpha = 0.3     # sensor angle offset
B_L = 6.16      # beta=1.40 * B_R
B_R = 4.40
source = (0.0, 0.0)


def gaussian_response(stim):
    diff = stim - peak_stimulus
    return max_voltage * math.exp(-diff * diff / (2.0 * sigma * sigma))


def compute_speeds(x, y, heading):
    """Compute (speed_L, speed_R) for vehicle at (x,y,heading)."""
    # Left sensor position
    sl_x = x + d * math.cos(heading + alpha)
    sl_y = y + d * math.sin(heading + alpha)
    # Right sensor position
    sr_x = x + d * math.cos(heading - alpha)
    sr_y = y + d * math.sin(heading - alpha)

    # Distance from sensors to source
    dl = math.sqrt((sl_x - source[0])**2 + (sl_y - source[1])**2)
    dr = math.sqrt((sr_x - source[0])**2 + (sr_y - source[1])**2)

    # Field (inverse square)
    f_l = I / (dl * dl) if dl > 0.1 else I / 0.01
    f_r = I / (dr * dr) if dr > 0.1 else I / 0.01

    # Sensor response
    v_sl = gaussian_response(f_l)
    v_sr = gaussian_response(f_r)

    # Crossed wiring: SL -> MR, SR -> ML
    speed_l = max(0.0, B_L + v_sr)
    speed_r = max(0.0, B_R + v_sl)

    return speed_l, speed_r


def ode_rhs(t, state):
    """Continuous ODE: d[x, y, theta]/dt"""
    x, y, theta = state
    sl, sr = compute_speeds(x, y, theta)
    forward_speed = (sl + sr) / 2.0
    turn_rate = (sr - sl) / W
    dx = forward_speed * math.cos(theta)
    dy = forward_speed * math.sin(theta)
    return [dx, dy, turn_rate]


def simulate_euler(x0, y0, theta0, dt, n_steps):
    """Euler method (matches simulation.py _euler_update)."""
    traj = [(0.0, x0, y0, theta0)]
    x, y, theta = x0, y0, theta0
    for i in range(n_steps):
        sl, sr = compute_speeds(x, y, theta)
        d_left = sl * dt
        d_right = sr * dt
        d_forward = (d_left + d_right) / 2.0
        d_heading = (d_right - d_left) / W
        theta += d_heading
        x += d_forward * math.cos(theta)
        y += d_forward * math.sin(theta)
        theta = theta % (2 * math.pi)
        traj.append(((i + 1) * dt, x, y, theta))
    return traj


def simulate_arc(x0, y0, theta0, dt, n_steps):
    """Arc method (matches simulation.py _arc_update)."""
    traj = [(0.0, x0, y0, theta0)]
    x, y, theta = x0, y0, theta0
    for i in range(n_steps):
        sl, sr = compute_speeds(x, y, theta)
        d_left = sl * dt
        d_right = sr * dt
        if abs(d_left - d_right) < 1e-10:
            x += d_left * math.cos(theta)
            y += d_left * math.sin(theta)
        else:
            d_heading = (d_right - d_left) / W
            R = W * (d_left + d_right) / (2.0 * (d_right - d_left))
            icc_x = x - R * math.sin(theta)
            icc_y = y + R * math.cos(theta)
            x = icc_x + R * math.sin(theta + d_heading)
            y = icc_y - R * math.cos(theta + d_heading)
            theta += d_heading
        theta = theta % (2 * math.pi)
        traj.append(((i + 1) * dt, x, y, theta))
    return traj


# Initial conditions: vehicle south of source, heading east
r_start = 187.18  # predicted equilibrium
x0, y0, theta0 = 0.0, -r_start, 0.0  # heading east

# Simulate for many orbits
# Period ≈ 16.4 time units, do 30 orbits = ~500 time units
t_end = 500.0
dt = 0.01

print(f"Starting at (0, {-r_start:.2f}), heading=0 (east)")
print(f"Predicted orbit radius: {r_start:.2f}")
print(f"Simulating {t_end:.0f} time units (~{t_end/16.4:.0f} orbits)\n")

# 1. High-precision ODE (ground truth)
print("Running RK45 (scipy, rtol=1e-10)...")
sol = solve_ivp(ode_rhs, [0, t_end], [x0, y0, theta0],
                method='RK45', rtol=1e-10, atol=1e-12,
                dense_output=True, max_step=0.5)
t_dense = np.linspace(0, t_end, 10000)
states = sol.sol(t_dense)
r_rk45 = np.sqrt(states[0]**2 + states[1]**2)
print(f"  Final distance from source: {r_rk45[-1]:.4f}")
print(f"  Min/Max distance: {r_rk45.min():.2f} / {r_rk45.max():.2f}")
print(f"  Drift: {r_rk45[-1] - r_start:.4f}")

# 2. Arc method
print("\nRunning arc method (dt=0.01)...")
traj_arc = simulate_arc(x0, y0, theta0, dt, int(t_end / dt))
r_arc = [math.sqrt(t[1]**2 + t[2]**2) for t in traj_arc[::100]]
t_arc = [t[0] for t in traj_arc[::100]]
print(f"  Final distance from source: {r_arc[-1]:.4f}")
print(f"  Min/Max distance: {min(r_arc):.2f} / {max(r_arc):.2f}")

# 3. Euler method
print("\nRunning Euler method (dt=0.01)...")
traj_euler = simulate_euler(x0, y0, theta0, dt, int(t_end / dt))
r_euler = [math.sqrt(t[1]**2 + t[2]**2) for t in traj_euler[::100]]
t_euler = [t[0] for t in traj_euler[::100]]
print(f"  Final distance from source: {r_euler[-1]:.4f}")
print(f"  Min/Max distance: {min(r_euler):.2f} / {max(r_euler):.2f}")

# Plot distance from source over time
fig, axes = plt.subplots(2, 1, figsize=(14, 10))

ax1 = axes[0]
ax1.plot(t_dense, r_rk45, 'b-', label='RK45 (ground truth)', linewidth=1.5)
ax1.plot(t_arc, r_arc, 'g--', label='Arc method dt=0.01', linewidth=1.5)
ax1.plot(t_euler, r_euler, 'r:', label='Euler dt=0.01', linewidth=1.5)
ax1.axhline(y=r_start, color='k', linestyle='-', alpha=0.3, label=f'r={r_start:.1f}')
ax1.set_xlabel('Time')
ax1.set_ylabel('Distance from source')
ax1.set_title('Orbit stability: distance from source over time')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Plot trajectory (x,y) for RK45
ax2 = axes[1]
ax2.plot(states[0], states[1], 'b-', linewidth=0.5, alpha=0.7, label='RK45')
# Also plot last few orbits of arc method
arc_x = [t[1] for t in traj_arc[-5000:]]
arc_y = [t[2] for t in traj_arc[-5000:]]
ax2.plot(arc_x, arc_y, 'g-', linewidth=0.5, alpha=0.7, label='Arc')
euler_x = [t[1] for t in traj_euler[-5000:]]
euler_y = [t[2] for t in traj_euler[-5000:]]
ax2.plot(euler_x, euler_y, 'r-', linewidth=0.5, alpha=0.7, label='Euler')
ax2.plot(0, 0, 'ko', markersize=8, label='Source')
circle = plt.Circle((0, 0), r_start, fill=False, color='gray', linestyle='--', alpha=0.5)
ax2.add_patch(circle)
ax2.set_aspect('equal')
ax2.set_xlabel('x')
ax2.set_ylabel('y')
ax2.set_title('Trajectory (last ~3 orbits)')
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('/Users/ronhartikka/Documents/Retirement Work/Engineer/vehicles/orbit_verification.png', dpi=150)
print("\nSaved orbit_verification.png")

# Check if orbit is truly stable or slowly precessing
print("\n--- Detailed RK45 orbit analysis ---")
# Sample distance at each orbit completion (every ~16.4 time units)
period = 2 * math.pi * r_start / 71.68  # approximate period
sample_times = np.arange(0, t_end, period)
for t in sample_times[:20]:
    state = sol.sol(t)
    r = math.sqrt(state[0]**2 + state[1]**2)
    angle = math.atan2(state[1], state[0])
    print(f"  t={t:7.1f}: r={r:.4f}, angle={math.degrees(angle):7.2f}°, heading={math.degrees(state[2]):7.2f}°")
