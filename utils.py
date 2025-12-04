"""Shared utility helpers.

This module is intentionally small for now but gives us a central place for
small reusable helpers (math, random, serialization, etc.) as systems grow.
"""


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Clamp *value* to the inclusive range [minimum, maximum]."""

    return max(minimum, min(maximum, value))
