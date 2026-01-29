"""Field evaluation: compute stimulus at any point from sources."""

import math
from .model import Point, Source, Field


def _exterior_falloff(source: Source, distance: float) -> float:
    if source.falloff == "inverse_square":
        return source.intensity / (distance * distance)
    elif source.falloff == "inverse_linear":
        return source.intensity / distance
    elif source.falloff == "constant":
        return source.intensity
    elif source.falloff == "gaussian":
        return source.intensity * math.exp(
            -distance * distance / (2.0 * source.sigma * source.sigma)
        )
    else:
        raise ValueError(f"Unknown falloff: {source.falloff}")


def source_contribution(point: Point, source: Source) -> float:
    """Compute stimulus contribution from a single source at a point."""
    dx = point.x - source.position.x
    dy = point.y - source.position.y
    distance = math.sqrt(dx * dx + dy * dy)

    if distance >= source.radius:
        return _exterior_falloff(source, distance)
    elif source.radius > 0:
        # Interior: linear from 0 at center to f(radius) at boundary
        boundary_value = _exterior_falloff(source, source.radius)
        return boundary_value * (distance / source.radius)
    else:
        return 0.0


def evaluate_field(point: Point, field: Field) -> float:
    """Total stimulus at a point from all sources in a field."""
    return sum(source_contribution(point, s) for s in field.sources)
