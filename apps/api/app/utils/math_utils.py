from __future__ import annotations


def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    """Clamp *value* into [minimum, maximum]."""
    return max(minimum, min(value, maximum))
