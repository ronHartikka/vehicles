"""Render sources, vehicles, trails, and field overlays."""

import math
from typing import Dict, List, Tuple, Optional

import pygame

from vehicles.model import Vehicle, Source, Field, Environment
from vehicles.simulation import VehicleStepResult
from .camera import Camera


DEFAULT_COLORS = {
    "temperature": (255, 80, 40),
    "light": (255, 240, 60),
    "chemical": (60, 200, 100),
}

VEHICLE_BODY_COLOR = (100, 160, 220)
VEHICLE_SELECTED_COLOR = (255, 220, 60)
SENSOR_COLOR = (220, 220, 220)
WHEEL_COLOR = (60, 60, 60)
TRAIL_COLOR = (100, 160, 220)

VEHICLE_PALETTE = [
    (100, 160, 220),  # blue
    (220, 100, 100),  # red
    (100, 220, 100),  # green
    (220, 180, 60),   # gold
    (180, 100, 220),  # purple
    (100, 220, 220),  # cyan
    (220, 140, 60),   # orange
    (220, 100, 180),  # pink
]


def draw_source(surface: pygame.Surface, camera: Camera, source: Source,
                color: Tuple[int, int, int]):
    sx, sy = camera.world_to_screen(source.position.x, source.position.y)
    radius_px = camera.world_to_screen_dist(source.radius)
    # Filled circle with slight transparency via outline
    pygame.draw.circle(surface, color, (sx, sy), radius_px)
    # Brighter center dot
    pygame.draw.circle(surface, (255, 255, 255), (sx, sy), max(2, radius_px // 4))


def draw_vehicle(surface: pygame.Surface, camera: Camera, vehicle: Vehicle,
                 selected: bool = False,
                 diagnostics: Optional[VehicleStepResult] = None,
                 body_color: Optional[Tuple[int, int, int]] = None):
    cx, cy = camera.world_to_screen(vehicle.position.x, vehicle.position.y)
    body_r = camera.world_to_screen_dist(vehicle.body_radius)

    # Body
    if selected:
        body_color = VEHICLE_SELECTED_COLOR
    elif body_color is None:
        body_color = VEHICLE_BODY_COLOR
    pygame.draw.circle(surface, body_color, (cx, cy), body_r)

    # Heading line
    hx = cx + int(body_r * 1.5 * math.cos(-vehicle.heading))
    hy = cy + int(body_r * 1.5 * math.sin(-vehicle.heading))
    pygame.draw.line(surface, (255, 255, 255), (cx, cy), (hx, hy), 2)

    # Voltage lookup for sensor brightness
    voltage_map = {}
    if diagnostics:
        for sr in diagnostics.sensor_readings:
            voltage_map[sr.mount_id] = sr.voltage

    # Sensors
    for mount in vehicle.sensor_mounts:
        wx = vehicle.position.x + mount.distance_from_center * math.cos(
            vehicle.heading + mount.angle_offset
        )
        wy = vehicle.position.y + mount.distance_from_center * math.sin(
            vehicle.heading + mount.angle_offset
        )
        sx, sy = camera.world_to_screen(wx, wy)
        # Brightness based on voltage (brighter = more voltage)
        v = voltage_map.get(mount.id, 0)
        brightness = min(255, int(80 + v * 10))
        dot_color = (brightness, brightness, brightness)
        pygame.draw.circle(surface, dot_color, (sx, sy), max(2, body_r // 3))

    # Wheels
    half_axle = vehicle.axle_width / 2.0
    for side, sign in [("left", 1), ("right", -1)]:
        wheel_angle = vehicle.heading + sign * math.pi / 2
        wx = vehicle.position.x + half_axle * math.cos(wheel_angle)
        wy = vehicle.position.y + half_axle * math.sin(wheel_angle)
        wsx, wsy = camera.world_to_screen(wx, wy)
        wheel_len = max(2, body_r // 2)
        # Draw as a short line perpendicular to axle (parallel to heading)
        dx = int(wheel_len * math.cos(-vehicle.heading))
        dy = int(wheel_len * math.sin(-vehicle.heading))
        pygame.draw.line(surface, WHEEL_COLOR, (wsx - dx, wsy - dy),
                         (wsx + dx, wsy + dy), max(1, body_r // 4))


def draw_trail(surface: pygame.Surface, camera: Camera,
               trail: List[Tuple[float, float]], color: Tuple[int, int, int]):
    if len(trail) < 2:
        return
    points = [camera.world_to_screen(x, y) for x, y in trail]
    n = len(points)
    for i in range(n - 1):
        alpha = 60 + int(195 * (i + 1) / n)
        c = (min(255, color[0]), min(255, color[1]), min(255, color[2]))
        # pygame doesn't support per-segment alpha easily, so just dim the color
        faded = (c[0] * alpha // 255, c[1] * alpha // 255, c[2] * alpha // 255)
        pygame.draw.line(surface, faded, points[i], points[i + 1], 2)


def draw_field_overlay(surface: pygame.Surface, camera: Camera,
                       field: Field, color: Tuple[int, int, int],
                       grid_size: int = 40):
    """Draw a coarse heat-map overlay for a field over the visible region."""
    from vehicles.fields import evaluate_field
    from vehicles.model import Point

    sw, sh = surface.get_size()
    cell_w = sw // grid_size
    cell_h = sh // grid_size
    if cell_w < 1 or cell_h < 1:
        return

    # Find max stimulus for normalization (sample a few points)
    max_stim = 0.01
    for gy in range(0, grid_size, 4):
        for gx in range(0, grid_size, 4):
            sx = gx * cell_w + cell_w // 2
            sy = gy * cell_h + cell_h // 2
            wx, wy = camera.screen_to_world(sx, sy)
            s = evaluate_field(Point(wx, wy), field)
            max_stim = max(max_stim, s)

    overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
    for gy in range(grid_size):
        for gx in range(grid_size):
            sx = gx * cell_w + cell_w // 2
            sy = gy * cell_h + cell_h // 2
            wx, wy = camera.screen_to_world(sx, sy)
            stimulus = evaluate_field(Point(wx, wy), field)
            intensity = min(1.0, stimulus / max_stim)
            alpha = int(intensity * 120)
            r = int(color[0] * intensity)
            g = int(color[1] * intensity)
            b = int(color[2] * intensity)
            rect = pygame.Rect(gx * cell_w, gy * cell_h, cell_w, cell_h)
            pygame.draw.rect(overlay, (r, g, b, alpha), rect)

    surface.blit(overlay, (0, 0))


CONTOUR_LEVELS = [0.1, 0.2, 0.5, 1, 2, 5, 10, 25, 50, 100, 150, 200, 400, 800, 1500]


def _contour_radius(source: Source, stimulus_level: float) -> Optional[float]:
    """Compute the distance from source center where stimulus equals the level.

    Returns None if the contour falls inside the source radius or the falloff
    type doesn't support analytic contours.
    """
    if stimulus_level <= 0:
        return None

    if source.falloff == "inverse_square":
        # stimulus = intensity / d^2  =>  d = sqrt(intensity / stimulus)
        d = math.sqrt(source.intensity / stimulus_level)
    elif source.falloff == "inverse_linear":
        # stimulus = intensity / d  =>  d = intensity / stimulus
        d = source.intensity / stimulus_level
    else:
        return None  # no simple analytic contour for constant/gaussian

    # Only draw contours outside the source body
    if d < source.radius:
        return None
    return d


def _dim_color(color: Tuple[int, int, int], factor: float = 0.4) -> Tuple[int, int, int]:
    return (int(color[0] * factor), int(color[1] * factor), int(color[2] * factor))


def draw_field_contours(surface: pygame.Surface, camera: Camera,
                        environment: Environment,
                        colors: Dict[str, Tuple[int, int, int]]):
    """Draw labeled stimulus contour circles around each source.

    Only draws analytic contours for single-source fields with
    inverse-square or inverse-linear falloff.
    """
    label_font = pygame.font.SysFont("monospace", 11)

    for field in environment.fields:
        if len(field.sources) != 1:
            continue  # analytic circles only valid for single-source fields

        source = field.sources[0]
        base_color = colors.get(field.type, (128, 128, 128))
        line_color = _dim_color(base_color, 0.5)
        sx, sy = camera.world_to_screen(source.position.x, source.position.y)

        for level in CONTOUR_LEVELS:
            r_world = _contour_radius(source, level)
            if r_world is None:
                continue

            r_px = camera.world_to_screen_dist(r_world)
            if r_px < 4 or r_px > 4000:
                continue

            pygame.draw.circle(surface, line_color, (sx, sy), r_px, 1)

            # Label at the right side of the contour — show distance
            label_x = sx + r_px + 3
            label_y = sy - 6
            if label_x < surface.get_width() - 40:
                label_surf = label_font.render(f"d={r_world:.0f}", True, line_color)
                surface.blit(label_surf, (label_x, label_y))


def draw_figure8_guide(surface: pygame.Surface, camera: Camera,
                       source: Source, peak_stimulus: float):
    """Draw a figure-8 guide around a source.

    The crossing point is at the peak-stimulus distance above the source.
    The inner lobe wraps around the source, the outer lobe extends away.
    """
    import math as _math

    R_peak = _math.sqrt(source.intensity / peak_stimulus)

    guide_color = (80, 80, 120)  # dim blue-gray

    # Inner lobe: centered on the source, radius = R_peak
    # Outer lobe: centered at 2*R_peak below source, radius = R_peak
    # Both circles meet at the crossing point (R_peak below source)
    inner_cx, inner_cy = camera.world_to_screen(
        source.position.x, source.position.y)
    inner_r_px = camera.world_to_screen_dist(R_peak)

    outer_cx, outer_cy = camera.world_to_screen(
        source.position.x, source.position.y + 2 * R_peak)
    outer_r_px = camera.world_to_screen_dist(R_peak)

    if 4 < inner_r_px < 4000:
        pygame.draw.circle(surface, guide_color, (inner_cx, inner_cy), inner_r_px, 1)
    if 4 < outer_r_px < 4000:
        pygame.draw.circle(surface, guide_color, (outer_cx, outer_cy), outer_r_px, 1)

    # Mark crossing point
    cross_sx, cross_sy = camera.world_to_screen(
        source.position.x, source.position.y + R_peak)
    pygame.draw.circle(surface, guide_color, (cross_sx, cross_sy), 4, 0)


def draw_distance_scale(surface: pygame.Surface, camera: Camera,
                        source: Source):
    """Draw a vertical distance scale to the right showing distance from source.

    The scale is drawn as a vertical ruler along the right edge, with tick marks
    and labels showing the distance from the source's horizontal line (y = source.y).
    """
    sw, sh = surface.get_size()
    margin_right = 60  # pixels from right edge
    scale_x = sw - margin_right

    label_font = pygame.font.SysFont("monospace", 16, bold=True)
    color = (180, 180, 200)
    line_color = (80, 80, 100)

    # Draw the vertical line
    pygame.draw.line(surface, line_color, (scale_x, 0), (scale_x, sh), 1)

    # Draw a horizontal reference line through the source
    _, src_sy = camera.world_to_screen(source.position.x, source.position.y)
    if 0 <= src_sy <= sh:
        pygame.draw.line(surface, (80, 80, 100), (scale_x - 15, src_sy),
                         (scale_x + 15, src_sy), 1)
        label = label_font.render("S", True, (200, 200, 220))
        surface.blit(label, (scale_x + 18, src_sy - 8))

    # Choose tick spacing based on zoom level
    # We want ticks roughly every 40-80 pixels apart
    pixels_per_unit = camera.zoom
    target_px = 60  # desired pixel spacing
    target_world = target_px / pixels_per_unit

    # Round to nice values: 10, 20, 50, 100, 200, 500, ...
    nice = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000]
    tick_world = nice[0]
    for n in nice:
        if n >= target_world:
            tick_world = n
            break
    else:
        tick_world = nice[-1]

    # Find visible y range in world coords
    _, wy_top = camera.screen_to_world(scale_x, 0)
    _, wy_bot = camera.screen_to_world(scale_x, sh)
    y_min = min(wy_top, wy_bot)
    y_max = max(wy_top, wy_bot)

    # Draw ticks at regular distance intervals from source
    source_y = source.position.y
    # Start from source_y and go up/down in tick_world steps
    d_min = int((y_min - source_y) / tick_world) - 1
    d_max = int((y_max - source_y) / tick_world) + 1

    for d_idx in range(d_min, d_max + 1):
        world_y = source_y + d_idx * tick_world
        dist = abs(d_idx * tick_world)
        _, sy = camera.world_to_screen(source.position.x, world_y)

        if sy < 0 or sy > sh:
            continue

        # Tick mark
        tick_len = 8 if d_idx % 5 == 0 else 4
        pygame.draw.line(surface, color, (scale_x - tick_len, sy),
                         (scale_x + tick_len, sy), 1)

        # Label (show distance, not y-coordinate)
        if d_idx != 0 and (d_idx % 2 == 0 or tick_world >= 50):
            label = label_font.render(f"{dist:.0f}", True, color)
            surface.blit(label, (scale_x + 12, sy - 8))
