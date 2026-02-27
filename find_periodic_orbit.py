"""Periodic orbit finder for Braitenberg vehicle trajectories.

Uses Poincare section, numerical shooting, and Floquet analysis to find
and characterize closed periodic orbits (e.g., figure-8 trajectories).

Usage:
    python find_periodic_orbit.py configs/vehicle_4a_speed_sweep.json \
        --vehicle x1.042 --x0 200 --y0 -159.7 --plot
"""

import sys
import os
import math
import argparse
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import fsolve

# Add project root to path so 'vehicles' package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vehicles.config_loader import load_config
from vehicles.model import Point
from vehicles.fields import evaluate_field
from vehicles.sensors import compute_voltage, STIMULUS_UNIT_TO_FIELD_TYPE


# ---------------------------------------------------------------------------
# ODE right-hand side
# ---------------------------------------------------------------------------

def make_ode_rhs(config, vehicle):
    """Build continuous ODE right-hand side for vehicle dynamics.

    Returns f(t, state) where state = [x, y, theta].
    Mirrors simulation.py _step_vehicle logic but returns continuous
    derivatives (true differential-drive kinematics).
    """
    field_lookup = {f.type: f for f in config.environment.fields}
    sensor_defs = config.sensor_defs

    # Pre-extract vehicle structure for fast access
    mounts = vehicle.sensor_mounts
    motors = vehicle.motors
    connections = vehicle.connections
    motor_lookup = {m.id: m for m in motors}
    axle_width = vehicle.axle_width

    def rhs(t, state):
        x, y, theta = state

        # 1. Sensor voltages
        sensor_voltages = {}
        for mount in mounts:
            wx = x + mount.distance_from_center * math.cos(theta + mount.angle_offset)
            wy = y + mount.distance_from_center * math.sin(theta + mount.angle_offset)
            sensor_def = sensor_defs[mount.sensor_name]
            field_type = STIMULUS_UNIT_TO_FIELD_TYPE[sensor_def.stimulus_unit]
            field = field_lookup.get(field_type)
            stimulus = evaluate_field(Point(wx, wy), field) if field else 0.0
            voltage = compute_voltage(sensor_def, stimulus)
            sensor_voltages[mount.id] = voltage

        # 2. Motor input voltages = base_voltage + weighted sensor contributions
        motor_input = {m.id: m.base_voltage for m in motors}
        for conn in connections:
            motor_input[conn.to_motor] += conn.weight * sensor_voltages[conn.from_sensor]

        # 3. Wheel speeds (no max_speed clamping, matching simulation.py)
        wheel_speeds = {}
        for mid, voltage_in in motor_input.items():
            motor = motor_lookup[mid]
            speed = max(0.0, motor.gain * voltage_in)
            wheel_speeds[motor.side] = wheel_speeds.get(motor.side, 0.0) + speed

        speed_l = wheel_speeds.get("left", 0.0)
        speed_r = wheel_speeds.get("right", 0.0)

        # 4. Continuous differential-drive dynamics
        v_forward = (speed_l + speed_r) / 2.0
        omega = (speed_r - speed_l) / axle_width

        return [v_forward * math.cos(theta),
                v_forward * math.sin(theta),
                omega]

    return rhs


# ---------------------------------------------------------------------------
# Poincare section events
# ---------------------------------------------------------------------------

def make_poincare_event(section_type="theta", section_value=0.0):
    """Create event function for Poincare section.

    section_type='theta': detects sin(theta - section_value) = 0,
        direction +1 (heading crosses section_value going CCW).
    section_type='y': detects y - section_value = 0,
        direction +1 (y increasing at crossing).
    """
    if section_type == "theta":
        def event(t, state):
            return math.sin(state[2] - section_value)
    else:  # 'y'
        def event(t, state):
            return state[1] - section_value

    event.terminal = True
    event.direction = 1
    return event


# ---------------------------------------------------------------------------
# Integration to Poincare section
# ---------------------------------------------------------------------------

def integrate_to_section(state0, rhs, event, t_max=10000.0,
                         rtol=1e-10, atol=1e-12, t_burnin=0.5,
                         n_crossings=1):
    """Integrate from state0 until the n-th Poincare section crossing.

    Phase 1: burn-in integration (t_burnin time units) without events
             to move off the section and avoid a spurious t=0 trigger.
    Phase 2: integrate with event detection until n_crossings crossings.

    n_crossings=1: standard (stop at first crossing).
    n_crossings=2: figure-8 mode (stop at second crossing).

    Returns (state_at_crossing, total_period, (sol_burnin, sol_main)).
    Raises RuntimeError if no crossing is found within t_max.
    """
    # Phase 1: burn-in (no events)
    sol_burnin = solve_ivp(rhs, [0, t_burnin], state0,
                           method='RK45', rtol=rtol, atol=atol,
                           max_step=1.0, dense_output=True)
    if sol_burnin.status != 0:
        raise RuntimeError(f"Burn-in integration failed: {sol_burnin.message}")

    state_after_burnin = sol_burnin.y[:, -1]

    if n_crossings == 1:
        # Simple case: stop at first crossing
        sol = solve_ivp(rhs, [0, t_max], state_after_burnin,
                        method='RK45', rtol=rtol, atol=atol,
                        max_step=1.0, events=event, dense_output=True)

        if sol.t_events[0].size == 0:
            raise RuntimeError(
                f"No Poincare section crossing found within t_max={t_max}. "
                f"Final state: ({sol.y[0,-1]:.2f}, {sol.y[1,-1]:.2f}, "
                f"{sol.y[2,-1]:.4f})")

        t_cross = sol.t_events[0][0]
        state_cross = sol.y_events[0][0]
        period = t_burnin + t_cross
        return state_cross, period, (sol_burnin, sol)
    else:
        # Multi-crossing: integrate without terminal event, collecting crossings
        event_nonterminal = lambda t, state: event(t, state)
        event_nonterminal.terminal = False
        event_nonterminal.direction = event.direction

        sol = solve_ivp(rhs, [0, t_max], state_after_burnin,
                        method='RK45', rtol=rtol, atol=atol,
                        max_step=1.0, events=event_nonterminal,
                        dense_output=True)

        n_found = sol.t_events[0].size
        if n_found < n_crossings:
            raise RuntimeError(
                f"Only found {n_found}/{n_crossings} crossings within "
                f"t_max={t_max}. "
                f"Final state: ({sol.y[0,-1]:.2f}, {sol.y[1,-1]:.2f}, "
                f"{sol.y[2,-1]:.4f})")

        t_cross = sol.t_events[0][n_crossings - 1]
        state_cross = sol.y_events[0][n_crossings - 1]
        period = t_burnin + t_cross
        return state_cross, period, (sol_burnin, sol)


# ---------------------------------------------------------------------------
# Return map and shooting
# ---------------------------------------------------------------------------

def return_map(free_vars, rhs, event, theta0=0.0, y0=0.0,
               section_type="theta", t_max=10000.0,
               rtol=1e-10, atol=1e-12, t_burnin=0.5,
               n_crossings=1):
    """Poincare return map.

    For theta-section: free_vars = (x, y), theta fixed → returns (x', y')
    For y-section: free_vars = (x, theta), y fixed → returns (x', theta')

    n_crossings: number of section crossings before returning.
      1 = standard (circle). 2 = figure-8 (two crossings per period).
    """
    if section_type == "y":
        x0, th0 = free_vars
        state0 = [x0, y0, th0]
    else:
        x0, y0_val = free_vars
        state0 = [x0, y0_val, theta0]

    state_cross, period, _ = integrate_to_section(
        state0, rhs, event, t_max, rtol, atol, t_burnin, n_crossings)

    if section_type == "y":
        return np.array([state_cross[0], state_cross[2]]), period
    else:
        return np.array([state_cross[0], state_cross[1]]), period


def shooting_residual(free_vars, rhs, event, theta0=0.0, y0=0.0,
                      section_type="theta", t_max=10000.0,
                      rtol=1e-10, atol=1e-12, t_burnin=0.5,
                      n_crossings=1):
    """Residual for shooting: F(q) = return_map(q) - q.

    For y-section with unwinding theta: compares theta mod 2pi.
    """
    q = np.array(free_vars)
    try:
        q_return, _ = return_map(free_vars, rhs, event, theta0, y0,
                                 section_type, t_max, rtol, atol, t_burnin,
                                 n_crossings)
        residual = q_return - q
        # For y-section, second variable is theta — reduce mod 2pi
        if section_type == "y":
            residual[1] = (residual[1] + math.pi) % (2 * math.pi) - math.pi
        return residual
    except RuntimeError as e:
        print(f"  Warning: integration failed: {e}")
        return np.array([1e6, 1e6])


def find_periodic_orbit(guess, rhs, event, theta0=0.0, y0=0.0,
                        section_type="theta", t_max=10000.0,
                        rtol=1e-10, atol=1e-12, t_burnin=0.5,
                        n_crossings=1, verbose=False):
    """Find periodic orbit using shooting method (fsolve).

    For theta-section: guess = (x, y)
    For y-section: guess = (x, theta)
    n_crossings: 1 for circle, 2 for figure-8.
    Returns (fixed_point, period, info_dict).
    """
    label = "(x, theta)" if section_type == "y" else "(x, y)"
    if verbose:
        print(f"  Initial guess {label}: ({guess[0]:.4f}, {guess[1]:.4f})")
        print(f"  n_crossings = {n_crossings}")
        r0 = shooting_residual(guess, rhs, event, theta0, y0,
                               section_type, t_max, rtol, atol, t_burnin,
                               n_crossings)
        print(f"  Initial residual: ({r0[0]:.6e}, {r0[1]:.6e}), "
              f"|r| = {np.linalg.norm(r0):.6e}")

    result, info, ier, msg = fsolve(
        shooting_residual, guess,
        args=(rhs, event, theta0, y0, section_type, t_max, rtol, atol,
              t_burnin, n_crossings),
        full_output=True)

    # Compute final residual and period
    final_residual = shooting_residual(
        result, rhs, event, theta0, y0, section_type,
        t_max, rtol, atol, t_burnin, n_crossings)
    try:
        _, period = return_map(result, rhs, event, theta0, y0,
                               section_type, t_max, rtol, atol, t_burnin,
                               n_crossings)
    except RuntimeError:
        period = float('nan')

    info_dict = {
        'fsolve_info': info,
        'fsolve_ier': ier,
        'fsolve_msg': msg,
        'residual': final_residual,
        'residual_norm': np.linalg.norm(final_residual),
    }

    if verbose:
        print(f"  fsolve status: {ier} - {msg}")
        print(f"  Fixed point {label}: ({result[0]:.6f}, {result[1]:.6f})")
        print(f"  Period: {period:.4f}")
        print(f"  Final residual: ({final_residual[0]:.6e}, "
              f"{final_residual[1]:.6e})")
        print(f"  |residual| = {info_dict['residual_norm']:.6e}")

    return result, period, info_dict


# ---------------------------------------------------------------------------
# Floquet analysis
# ---------------------------------------------------------------------------

def compute_floquet_multipliers(fixed_point, rhs, event, theta0=0.0,
                                y0=0.0, section_type="theta",
                                t_max=10000.0, rtol=1e-10, atol=1e-12,
                                t_burnin=0.5, n_crossings=1,
                                eps=1e-6, verbose=False):
    """Compute Floquet multipliers via finite-difference Jacobian of return map.

    Returns eigenvalues of the 2x2 Jacobian matrix at the fixed point.
    """
    q0 = np.array(fixed_point)
    f0, _ = return_map(q0, rhs, event, theta0, y0, section_type,
                       t_max, rtol, atol, t_burnin, n_crossings)

    J = np.zeros((2, 2))
    for j in range(2):
        dq = np.zeros(2)
        dq[j] = eps
        f_plus, _ = return_map(q0 + dq, rhs, event, theta0, y0,
                               section_type, t_max, rtol, atol, t_burnin,
                               n_crossings)
        f_minus, _ = return_map(q0 - dq, rhs, event, theta0, y0,
                                section_type, t_max, rtol, atol, t_burnin,
                                n_crossings)
        J[:, j] = (f_plus - f_minus) / (2 * eps)

    eigenvalues = np.linalg.eigvals(J)

    if verbose:
        print(f"\n  Jacobian of return map:")
        print(f"    [{J[0,0]:+.6f}  {J[0,1]:+.6f}]")
        print(f"    [{J[1,0]:+.6f}  {J[1,1]:+.6f}]")
        print(f"  Floquet multipliers: {eigenvalues}")
        for i, ev in enumerate(eigenvalues):
            print(f"    lambda_{i+1} = {ev:.6f}  |lambda_{i+1}| = {abs(ev):.6f}")
        stability = "stable" if all(abs(e) < 1 for e in eigenvalues) else "unstable"
        print(f"  Orbit is {stability}")

    return eigenvalues


# ---------------------------------------------------------------------------
# Parameter continuation
# ---------------------------------------------------------------------------

def continuation_sweep(fixed_point, config, vehicle, param_name,
                       param_start, param_end, param_steps,
                       section_type="theta", theta0=0.0, y0=0.0,
                       t_max=10000.0,
                       rtol=1e-10, atol=1e-12, t_burnin=0.5,
                       n_crossings=1, verbose=False):
    """Sweep a parameter and track the periodic orbit via continuation.

    param_name: 'intensity' or 'base_voltage_mult'
    Uses previous solution as initial guess for next parameter value.
    Returns list of result dicts.
    """
    param_values = np.linspace(param_start, param_end, param_steps)
    results = []
    current_guess = np.array(fixed_point)

    # Save original values for restoration
    original_intensity = config.environment.fields[0].sources[0].intensity
    original_base_voltages = [m.base_voltage for m in vehicle.motors]

    section_value = theta0 if section_type == "theta" else y0

    for i, pval in enumerate(param_values):
        if verbose:
            print(f"\n--- Continuation step {i+1}/{param_steps}: "
                  f"{param_name} = {pval:.4f} ---")

        # Modify parameter in-memory
        if param_name == 'intensity':
            config.environment.fields[0].sources[0].intensity = pval
        elif param_name == 'base_voltage_mult':
            for j, m in enumerate(vehicle.motors):
                m.base_voltage = original_base_voltages[j] * pval

        rhs = make_ode_rhs(config, vehicle)
        event = make_poincare_event(section_type, section_value)

        try:
            fp, period, info = find_periodic_orbit(
                current_guess, rhs, event, theta0, y0, section_type,
                t_max, rtol, atol, t_burnin, n_crossings,
                verbose=verbose)

            mults = compute_floquet_multipliers(
                fp, rhs, event, theta0, y0, section_type,
                t_max, rtol, atol, t_burnin, n_crossings,
                verbose=verbose)

            results.append({
                'param': pval,
                'fixed_point': fp.copy(),
                'period': period,
                'multipliers': mults,
                'residual_norm': info['residual_norm'],
                'converged': info['fsolve_ier'] == 1,
            })
            current_guess = fp  # use as next guess
        except Exception as e:
            if verbose:
                print(f"  Failed: {e}")
            results.append({
                'param': pval,
                'fixed_point': None,
                'period': None,
                'multipliers': None,
                'residual_norm': None,
                'converged': False,
            })

    # Restore original values
    config.environment.fields[0].sources[0].intensity = original_intensity
    for j, m in enumerate(vehicle.motors):
        m.base_voltage = original_base_voltages[j]

    return results


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def plot_results(fixed_point, period, rhs, event, theta0, config, vehicle,
                 rtol=1e-10, atol=1e-12, t_burnin=0.5,
                 section_type="theta", y0=0.0,
                 continuation_results=None):
    """Plot the periodic orbit and optional continuation results."""
    import matplotlib.pyplot as plt

    # Reconstruct initial state from fixed_point + section type
    if section_type == "y":
        state0 = [fixed_point[0], y0, fixed_point[1]]
    else:
        state0 = [fixed_point[0], fixed_point[1], theta0]
    t_total = period + 10.0
    sol = solve_ivp(rhs, [0, t_total], state0,
                    method='RK45', rtol=rtol, atol=atol,
                    max_step=1.0, dense_output=True)

    t_plot = np.linspace(0, min(period, sol.t[-1]), 5000)
    y_plot = sol.sol(t_plot)

    source_pos = config.environment.fields[0].sources[0].position

    n_panels = 3 if continuation_results else 2
    fig, axes = plt.subplots(1, n_panels, figsize=(6 * n_panels, 6))

    # Panel 1: trajectory in x-y plane
    ax = axes[0]
    ax.plot(y_plot[0], y_plot[1], 'b-', linewidth=0.8, label='Orbit')
    ax.plot(fixed_point[0], fixed_point[1], 'ro', markersize=8,
            label=f'Section point ({fixed_point[0]:.2f}, {fixed_point[1]:.2f})')
    ax.plot(source_pos.x, source_pos.y, 'r*', markersize=15, label='Source')
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.set_title(f'Periodic Orbit  (T = {period:.2f})')
    ax.set_aspect('equal')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # Panel 2: theta(t)
    ax = axes[1]
    ax.plot(t_plot, y_plot[2], 'g-', linewidth=0.8)
    ax.set_xlabel('t')
    ax.set_ylabel('theta (rad)')
    ax.set_title('Heading vs Time')
    ax.grid(True, alpha=0.3)

    # Panel 3: continuation sweep
    if continuation_results is not None:
        ax = axes[2]
        converged = [r for r in continuation_results if r['converged']]
        if converged:
            params = [r['param'] for r in converged]
            mults_max = [max(abs(r['multipliers'])) for r in converged]
            ax.plot(params, mults_max, 'b.-')
            ax.axhline(y=1.0, color='r', linestyle='--', alpha=0.5,
                       label='|lambda| = 1')
            ax.set_xlabel('Parameter')
            ax.set_ylabel('max |Floquet multiplier|')
            ax.set_title('Stability vs Parameter')
            ax.legend()
            ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('periodic_orbit.png', dpi=150, bbox_inches='tight')
    print(f"\n  Plot saved to periodic_orbit.png")
    plt.show()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Find periodic orbits of Braitenberg vehicles '
                    'via Poincare section and shooting.')
    parser.add_argument('config', help='Path to JSON config file')
    parser.add_argument('--vehicle', default=None,
                        help='Vehicle name to analyze (default: first)')
    parser.add_argument('--x0', type=float, default=None,
                        help='Initial x guess (default: from config)')
    parser.add_argument('--y0', type=float, default=None,
                        help='Initial y guess (default: from config)')
    parser.add_argument('--theta0', type=float, default=0.0,
                        help='Heading at Poincare section (default: 0 = east)')
    parser.add_argument('--section', choices=['theta', 'y'], default='theta',
                        help='Poincare section type (default: theta)')
    parser.add_argument('--section-value', type=float, default=None,
                        help='Section value (default: theta0 for theta, '
                             'y0 for y)')
    parser.add_argument('--t-max', type=float, default=10000.0,
                        help='Max integration time (default: 10000)')
    parser.add_argument('--rtol', type=float, default=1e-10,
                        help='Relative tolerance (default: 1e-10)')
    parser.add_argument('--atol', type=float, default=1e-12,
                        help='Absolute tolerance (default: 1e-12)')
    parser.add_argument('--continuation-param',
                        choices=['intensity', 'base_voltage_mult'],
                        help='Parameter to sweep for continuation')
    parser.add_argument('--continuation-start', type=float,
                        help='Start value for continuation sweep')
    parser.add_argument('--continuation-end', type=float,
                        help='End value for continuation sweep')
    parser.add_argument('--continuation-steps', type=int, default=20,
                        help='Number of steps in continuation (default: 20)')
    parser.add_argument('--intensity', type=float, default=None,
                        help='Override source intensity')
    parser.add_argument('--gradient', type=float, default=None,
                        help='Add linear_gradient source with this intensity')
    parser.add_argument('--base-voltage-left', type=float, default=None,
                        help='Override left motor base voltage')
    parser.add_argument('--base-voltage-right', type=float, default=None,
                        help='Override right motor base voltage')
    parser.add_argument('--t-burnin', type=float, default=0.5,
                        help='Burn-in time to move off section (default: 0.5)')
    parser.add_argument('--n-crossings', type=int, default=1,
                        help='Section crossings per period: 1=circle, '
                             '2=figure-8 (default: 1)')
    parser.add_argument('--plot', action='store_true', help='Show plots')
    parser.add_argument('--verbose', action='store_true',
                        help='Verbose output')

    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Load config
    # ------------------------------------------------------------------
    config = load_config(args.config)

    # Override intensity if requested
    if args.intensity is not None:
        config.environment.fields[0].sources[0].intensity = args.intensity
        print(f"Intensity override: {args.intensity}")

    # Add gradient source if requested
    if args.gradient is not None:
        from vehicles.model import Source, Point as Pt
        source_pos = config.environment.fields[0].sources[0].position
        grad_source = Source(
            position=Pt(source_pos.x, source_pos.y),
            intensity=args.gradient,
            radius=0,
            falloff="linear_gradient",
        )
        config.environment.fields[0].sources.append(grad_source)
        print(f"Gradient source: k={args.gradient} centered at "
              f"({source_pos.x}, {source_pos.y})")

    # ------------------------------------------------------------------
    # Select vehicle
    # ------------------------------------------------------------------
    if args.vehicle:
        vehicle = None
        for v in config.vehicles:
            if v.name == args.vehicle:
                vehicle = v
                break
        if vehicle is None:
            names = [v.name for v in config.vehicles]
            print(f"Error: vehicle '{args.vehicle}' not found. "
                  f"Available: {names}")
            sys.exit(1)
    else:
        vehicle = config.vehicles[0]

    # Override base voltages if requested
    if args.base_voltage_left is not None:
        for m in vehicle.motors:
            if m.side == "left":
                m.base_voltage = args.base_voltage_left
    if args.base_voltage_right is not None:
        for m in vehicle.motors:
            if m.side == "right":
                m.base_voltage = args.base_voltage_right

    print(f"Vehicle: {vehicle.name}")
    print(f"  Motors: {[(m.id, m.base_voltage) for m in vehicle.motors]}")
    print(f"  Config position: ({vehicle.position.x}, {vehicle.position.y})")

    # ------------------------------------------------------------------
    # Set up initial guess and section
    # ------------------------------------------------------------------
    x0 = args.x0 if args.x0 is not None else vehicle.position.x
    y0 = args.y0 if args.y0 is not None else vehicle.position.y
    theta0 = args.theta0

    if args.section_value is not None:
        section_value = args.section_value
    elif args.section == 'y':
        section_value = y0
    else:
        section_value = theta0

    print(f"\nPoincare section: {args.section} = {section_value:.4f}, "
          f"direction = +1")

    # For y-section, initial guess is (x, theta); for theta-section, (x, y)
    if args.section == 'y':
        print(f"Initial guess (x, theta): ({x0:.4f}, {theta0:.4f}), "
              f"y_section = {section_value:.4f}")
    else:
        print(f"Initial guess (x, y): ({x0:.4f}, {y0:.4f}), "
              f"theta0 = {theta0:.4f}")

    # ------------------------------------------------------------------
    # Build ODE and event
    # ------------------------------------------------------------------
    rhs = make_ode_rhs(config, vehicle)
    event = make_poincare_event(args.section, section_value)

    # ------------------------------------------------------------------
    # Shooting
    # ------------------------------------------------------------------
    print(f"\n{'='*50}")
    print(f"  SHOOTING METHOD")
    print(f"{'='*50}")

    if args.section == 'y':
        guess = np.array([x0, theta0])
    else:
        guess = np.array([x0, y0])

    converged = False
    try:
        fixed_point, period, info = find_periodic_orbit(
            guess, rhs, event, theta0, section_value,
            args.section, args.t_max,
            args.rtol, args.atol, t_burnin=args.t_burnin,
            n_crossings=args.n_crossings, verbose=True)

        converged = info['fsolve_ier'] == 1
        if converged:
            print(f"\n  ** CONVERGED **")
        else:
            print(f"\n  ** DID NOT CONVERGE **")
            r = info['residual']
            precession = np.linalg.norm(r)
            print(f"  Precession per orbit: {precession:.6f} units")
            print(f"  Best residual: ({r[0]:.6e}, {r[1]:.6e})")

    except Exception as e:
        print(f"\n  Shooting failed: {e}")
        print("  Will plot initial trajectory instead.")
        fixed_point = guess
        period = args.t_max
        info = {'residual_norm': float('inf'), 'fsolve_ier': 0}

    # ------------------------------------------------------------------
    # Floquet analysis
    # ------------------------------------------------------------------
    multipliers = None
    if converged or info['residual_norm'] < 1.0:
        print(f"\n{'='*50}")
        print(f"  FLOQUET ANALYSIS")
        print(f"{'='*50}")
        try:
            multipliers = compute_floquet_multipliers(
                fixed_point, rhs, event, theta0, section_value,
                args.section, args.t_max,
                args.rtol, args.atol, t_burnin=args.t_burnin,
                n_crossings=args.n_crossings, verbose=True)
        except Exception as e:
            print(f"  Floquet analysis failed: {e}")

    # ------------------------------------------------------------------
    # Continuation sweep
    # ------------------------------------------------------------------
    continuation_results = None
    if (args.continuation_param
            and args.continuation_start is not None
            and args.continuation_end is not None):
        print(f"\n{'='*50}")
        print(f"  CONTINUATION SWEEP: {args.continuation_param}")
        print(f"{'='*50}")
        continuation_results = continuation_sweep(
            fixed_point, config, vehicle, args.continuation_param,
            args.continuation_start, args.continuation_end,
            args.continuation_steps,
            args.section, theta0, section_value, args.t_max,
            args.rtol, args.atol,
            t_burnin=args.t_burnin, n_crossings=args.n_crossings,
            verbose=args.verbose)

        # Print summary table
        v2_label = "theta" if args.section == "y" else "y"
        print(f"\n  {'Param':>12s} {'x':>10s} {v2_label:>10s} "
              f"{'Period':>10s} {'|lam|_max':>12s} {'Conv':>5s}")
        print(f"  {'-'*12} {'-'*10} {'-'*10} {'-'*10} {'-'*12} {'-'*5}")
        for r in continuation_results:
            if r['converged']:
                mmax = max(abs(r['multipliers']))
                print(f"  {r['param']:12.4f} {r['fixed_point'][0]:10.4f} "
                      f"{r['fixed_point'][1]:10.4f} {r['period']:10.2f} "
                      f"{mmax:12.6f} {'Y':>5s}")
            else:
                print(f"  {r['param']:12.4f} {'---':>10s} {'---':>10s} "
                      f"{'---':>10s} {'---':>12s} {'N':>5s}")

    # ------------------------------------------------------------------
    # Plot
    # ------------------------------------------------------------------
    if args.plot:
        plot_results(fixed_point, period, rhs, event, theta0,
                     config, vehicle, args.rtol, args.atol,
                     t_burnin=args.t_burnin,
                     section_type=args.section, y0=section_value,
                     continuation_results=continuation_results)


if __name__ == '__main__':
    main()
