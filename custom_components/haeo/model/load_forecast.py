from typing import Sequence

from .element import Element


class LoadForecast(Element):
    """Forecast-based load entity for electrical system modeling."""

    def __init__(self, name: str, period: int, n_periods: int, current_power: float, forecast: Sequence[float]):
        """Initialize a forecast-based load.

        Args:
            name: Name of the load
            period: Time period in seconds
            n_periods: Number of periods
            current_power: Current power consumption value in watts
            forecast: Sequence of forecasted power consumption values in watts
        """
        if len(forecast) != n_periods:
            raise ValueError(f"forecast length ({len(forecast)}) must match n_periods ({n_periods})")

        # Combine current power with forecast
        power_consumption = [current_power, *forecast[:-1]]

        # Loads only consume power, they don't produce
        # For forecast loads, we want to ensure they consume the forecast amount therefore there are no variables here
        super().__init__(
            name=name,
            period=period,
            n_periods=n_periods,
            power_consumption=power_consumption,
        )
