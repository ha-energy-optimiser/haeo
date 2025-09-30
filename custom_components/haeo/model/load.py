from typing import Sequence

from .entity import Entity


class Load(Entity):
    """Load entity for electrical system modeling."""

    def __init__(self, name: str, period: int, n_periods: int, forecast: Sequence[float]):
        if len(forecast) != n_periods:
            raise ValueError(f"forecast length ({len(forecast)}) must match n_periods ({n_periods})")

        # Loads only consume power, they don't produce
        # Power consumption is positive (consuming power)
        # For loads, we want to ensure they consume the forecast amount therefore there are no variables here
        super().__init__(
            name=name,
            period=period,
            n_periods=n_periods,
            power_consumption=forecast,
        )
