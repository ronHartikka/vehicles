"""Main application: pygame event loop, simulation, rendering."""

import math
import sys
from typing import Optional, List, Tuple, Dict

import pygame

from vehicles.config_loader import load_config
from vehicles.model import ScenarioConfig, Vehicle
from vehicles.simulation import Simulation
from .camera import Camera
from . import renderer


STATUS_BAR_HEIGHT = 32
BG_COLOR = (20, 20, 30)
STATUS_BG = (40, 40, 50)
TEXT_COLOR = (200, 200, 200)
MAX_TRAIL_LENGTH = 3000


class App:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self._load_and_init()

    def _load_and_init(self):
        self.config = load_config(self.config_path)
        self.simulation = Simulation(self.config)

        pygame.init()
        vc = self.config.view
        self.screen_w = vc.window_width
        self.screen_h = vc.window_height + STATUS_BAR_HEIGHT
        self.screen = pygame.display.set_mode((self.screen_w, self.screen_h))
        pygame.display.set_caption("Braitenberg Vehicles")

        self.camera = Camera(
            vc.center.x, vc.center.y, vc.zoom,
            vc.window_width, vc.window_height,
        )

        self.font = pygame.font.SysFont("monospace", 14)
        self.info_font = pygame.font.SysFont("monospace", 13)

        self.running = True
        self.paused = True
        self.speed_multiplier = 1.0
        self.show_trail = False
        self.show_field_overlay = False
        self.show_contours = False
        self.selected_vehicle: Optional[str] = None
        self.trails: Dict[str, List[Tuple[float, float]]] = {
            v.name: [] for v in self.config.vehicles
        }
        self._panning = False
        self._pan_start = (0, 0)

        # Color lookup
        self.colors = dict(renderer.DEFAULT_COLORS)
        self.colors.update(self.config.colors)

    def _reset(self):
        """Reload config and reset simulation."""
        old_screen = self.screen
        self.config = load_config(self.config_path)
        self.simulation = Simulation(self.config)
        vc = self.config.view
        self.camera = Camera(
            vc.center.x, vc.center.y, vc.zoom,
            vc.window_width, vc.window_height,
        )
        self.selected_vehicle = None
        self.trails = {v.name: [] for v in self.config.vehicles}
        self.colors = dict(renderer.DEFAULT_COLORS)
        self.colors.update(self.config.colors)

    def run(self):
        clock = pygame.time.Clock()
        accumulator = 0.0

        while self.running:
            frame_dt = clock.tick(60) / 1000.0
            self._handle_events()

            if not self.paused:
                accumulator += frame_dt * self.speed_multiplier
                steps = 0
                while accumulator >= self.simulation.dt and steps < 20:
                    self.simulation.step()
                    self._record_trails()
                    accumulator -= self.simulation.dt
                    steps += 1

            self._render()

        pygame.quit()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                self._handle_key(event.key)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # left click
                    self._handle_click(event.pos)
                elif event.button == 3:  # right click - start pan
                    self._panning = True
                    self._pan_start = event.pos
                elif event.button == 4:  # scroll up
                    self.camera.zoom_at(event.pos[0], event.pos[1], 1.2)
                elif event.button == 5:  # scroll down
                    self.camera.zoom_at(event.pos[0], event.pos[1], 1.0 / 1.2)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 3:
                    self._panning = False

            elif event.type == pygame.MOUSEMOTION:
                if self._panning:
                    dx = event.pos[0] - self._pan_start[0]
                    dy = event.pos[1] - self._pan_start[1]
                    self.camera.pan(dx, dy)
                    self._pan_start = event.pos

            elif event.type == pygame.MOUSEWHEEL:
                mx, my = pygame.mouse.get_pos()
                if event.y > 0:
                    self.camera.zoom_at(mx, my, 1.2)
                elif event.y < 0:
                    self.camera.zoom_at(mx, my, 1.0 / 1.2)

    def _handle_key(self, key: int):
        if key == pygame.K_SPACE:
            self.paused = not self.paused
        elif key == pygame.K_s:
            if self.paused:
                self.simulation.step()
                self._record_trails()
        elif key == pygame.K_r:
            self._reset()
        elif key == pygame.K_l:
            self._load_new_file()
        elif key in (pygame.K_EQUALS, pygame.K_PLUS):
            self.speed_multiplier = min(32.0, self.speed_multiplier * 2)
        elif key == pygame.K_MINUS:
            self.speed_multiplier = max(0.125, self.speed_multiplier / 2)
        elif key == pygame.K_t:
            self.show_trail = not self.show_trail
        elif key == pygame.K_f:
            self.show_field_overlay = not self.show_field_overlay
        elif key == pygame.K_c:
            self.show_contours = not self.show_contours
        elif key == pygame.K_z:
            self.camera.zoom_at(self.screen_w // 2, self.camera.screen_h // 2, 1.3)
        elif key == pygame.K_x:
            self.camera.zoom_at(self.screen_w // 2, self.camera.screen_h // 2, 1.0 / 1.3)
        elif key == pygame.K_LEFT:
            self.camera.pan(-40, 0)
        elif key == pygame.K_RIGHT:
            self.camera.pan(40, 0)
        elif key == pygame.K_UP:
            self.camera.pan(0, -40)
        elif key == pygame.K_DOWN:
            self.camera.pan(0, 40)
        elif key == pygame.K_h:
            self._home_camera()
        elif key == pygame.K_RIGHTBRACKET:
            self._adjust_source_intensity(1.1)
        elif key == pygame.K_LEFTBRACKET:
            self._adjust_source_intensity(1.0 / 1.1)
        elif key in (pygame.K_ESCAPE, pygame.K_q):
            self.running = False

    def _handle_click(self, pos: Tuple[int, int]):
        wx, wy = self.camera.screen_to_world(pos[0], pos[1])
        best_dist = float("inf")
        best_name = None
        for v in self.simulation.vehicles:
            dx = wx - v.position.x
            dy = wy - v.position.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < v.body_radius * 2 and dist < best_dist:
                best_dist = dist
                best_name = v.name
        self.selected_vehicle = best_name

    def _adjust_source_intensity(self, factor: float):
        for field in self.simulation.environment.fields:
            for source in field.sources:
                source.intensity *= factor

    def _home_camera(self):
        if self.selected_vehicle:
            for v in self.simulation.vehicles:
                if v.name == self.selected_vehicle:
                    self.camera.cx = v.position.x
                    self.camera.cy = v.position.y
                    return
        self.camera.cx = self.config.view.center.x
        self.camera.cy = self.config.view.center.y

    def _load_new_file(self):
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            path = filedialog.askopenfilename(
                title="Load Vehicle Config",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            )
            root.destroy()
            if path:
                self.config_path = path
                self._reset()
        except Exception:
            pass  # tkinter not available or dialog cancelled

    def _record_trails(self):
        for v in self.simulation.vehicles:
            trail = self.trails.get(v.name)
            if trail is not None:
                trail.append((v.position.x, v.position.y))
                if len(trail) > MAX_TRAIL_LENGTH:
                    trail.pop(0)

    def _render(self):
        self.screen.fill(BG_COLOR)

        # Simulation view surface (above status bar)
        sim_surface = self.screen.subsurface(
            (0, 0, self.screen_w, self.screen_h - STATUS_BAR_HEIGHT)
        )

        # Field overlay
        if self.show_field_overlay:
            for field in self.simulation.environment.fields:
                color = self.colors.get(field.type, (128, 128, 128))
                renderer.draw_field_overlay(sim_surface, self.camera, field, color)

        # Field contours and figure-8 guide
        if self.show_contours:
            renderer.draw_field_contours(sim_surface, self.camera,
                                         self.simulation.environment, self.colors)
            # Draw figure-8 guide for single-source fields with bell/triangular sensors
            for sd in self.config.sensor_defs.values():
                if sd.response_function.type in ("bell", "triangular"):
                    for field in self.simulation.environment.fields:
                        for source in field.sources:
                            renderer.draw_figure8_guide(
                                sim_surface, self.camera, source,
                                sd.response_function.peak_stimulus)
                    break

        # Sources
        for field in self.simulation.environment.fields:
            color = self.colors.get(field.type, (128, 128, 128))
            for source in field.sources:
                renderer.draw_source(sim_surface, self.camera, source, color)

        # Trails
        if self.show_trail:
            for i, v in enumerate(self.simulation.vehicles):
                trail = self.trails.get(v.name, [])
                color = renderer.VEHICLE_PALETTE[i % len(renderer.VEHICLE_PALETTE)]
                renderer.draw_trail(sim_surface, self.camera, trail, color)

        # Vehicles
        for i, v in enumerate(self.simulation.vehicles):
            is_selected = (v.name == self.selected_vehicle)
            diag = self.simulation.diagnostics.get(v.name)
            color = renderer.VEHICLE_PALETTE[i % len(renderer.VEHICLE_PALETTE)]
            renderer.draw_vehicle(sim_surface, self.camera, v,
                                  selected=is_selected, diagnostics=diag,
                                  body_color=color)

        # Info panel
        if self.selected_vehicle:
            self._render_info_panel(sim_surface)

        # Status bar
        self._render_status_bar()

        pygame.display.flip()

    def _render_status_bar(self):
        bar_rect = pygame.Rect(0, self.screen_h - STATUS_BAR_HEIGHT,
                                self.screen_w, STATUS_BAR_HEIGHT)
        pygame.draw.rect(self.screen, STATUS_BG, bar_rect)

        state = "PAUSED" if self.paused else "RUNNING"
        speed_str = f"{self.speed_multiplier:.2g}x"
        time_str = f"t={self.simulation.time:.2f}"
        trail_str = "T:on" if self.show_trail else "T:off"
        field_str = "F:on" if self.show_field_overlay else "F:off"
        contour_str = "C:on" if self.show_contours else "C:off"

        # Show first source intensity
        intensity_str = ""
        for field in self.simulation.environment.fields:
            if field.sources:
                intensity_str = f"  I={field.sources[0].intensity:.0f}"
                break

        text = f" {state}  |  Speed: {speed_str}  |  {time_str}{intensity_str}  |  {trail_str}  {field_str}  {contour_str}  |  [/]:intensity  Space:play  R:reset  Q:quit"
        surf = self.font.render(text, True, TEXT_COLOR)
        self.screen.blit(surf, (8, self.screen_h - STATUS_BAR_HEIGHT + 8))

    def _render_info_panel(self, surface: pygame.Surface):
        v = None
        for veh in self.simulation.vehicles:
            if veh.name == self.selected_vehicle:
                v = veh
                break
        if not v:
            return

        diag = self.simulation.diagnostics.get(v.name)
        lines = [f"Vehicle: {v.name}"]
        lines.append(f"  Position: ({v.position.x:.1f}, {v.position.y:.1f})")
        lines.append(f"  Heading:  {v.heading:.2f} rad ({math.degrees(v.heading):.1f} deg)")

        if diag:
            for sr in diag.sensor_readings:
                lines.append(f"  Sensor {sr.mount_id}: stim={sr.stimulus:.3f}  V={sr.voltage:.3f}")
            for ms in diag.motor_states:
                lines.append(f"  Motor {ms.motor_id}:  Vin={ms.input_voltage:.3f}V  spd={ms.speed:.3f}")

        # Draw background panel
        line_h = 18
        panel_w = 360
        panel_h = len(lines) * line_h + 12
        panel_x = surface.get_width() - panel_w - 10
        panel_y = 10

        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill((0, 0, 0, 160))
        surface.blit(panel_surf, (panel_x, panel_y))

        for i, line in enumerate(lines):
            text_surf = self.info_font.render(line, True, TEXT_COLOR)
            surface.blit(text_surf, (panel_x + 8, panel_y + 6 + i * line_h))
