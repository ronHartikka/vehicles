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
                 diagnostics: Optional[VehicleStepResult] = None):
    cx, cy = camera.world_to_screen(vehicle.position.x, vehicle.position.y)
    body_r = camera.world_to_screen_dist(vehicle.body_radius)

    # Body
    body_color = VEHICLE_SELECTED_COLOR if selected else VEHICLE_BODY_COLOR
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
        alpha = int(255 * (i + 1) / n)
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
