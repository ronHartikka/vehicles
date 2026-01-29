"""World-to-screen coordinate transforms with pan and zoom."""

from typing import Tuple


class Camera:
    def __init__(self, center_x: float, center_y: float, zoom: float,
                 screen_w: int, screen_h: int):
        self.cx = center_x
        self.cy = center_y
        self.zoom = zoom
        self.screen_w = screen_w
        self.screen_h = screen_h

    def world_to_screen(self, wx: float, wy: float) -> Tuple[int, int]:
        sx = (wx - self.cx) * self.zoom + self.screen_w / 2
        sy = (self.cy - wy) * self.zoom + self.screen_h / 2  # flip Y
        return int(sx), int(sy)

    def screen_to_world(self, sx: int, sy: int) -> Tuple[float, float]:
        wx = (sx - self.screen_w / 2) / self.zoom + self.cx
        wy = self.cy - (sy - self.screen_h / 2) / self.zoom
        return wx, wy

    def world_to_screen_dist(self, d: float) -> int:
        """Convert a world-space distance to screen pixels."""
        return max(1, int(d * self.zoom))

    def pan(self, dx_pixels: float, dy_pixels: float):
        self.cx -= dx_pixels / self.zoom
        self.cy += dy_pixels / self.zoom

    def zoom_at(self, screen_x: int, screen_y: int, factor: float):
        """Zoom centered on a screen point."""
        wx, wy = self.screen_to_world(screen_x, screen_y)
        self.zoom *= factor
        self.zoom = max(0.1, min(self.zoom, 100.0))
        self.cx = wx - (screen_x - self.screen_w / 2) / self.zoom
        self.cy = wy + (screen_y - self.screen_h / 2) / self.zoom
