from __future__ import annotations

from typing import Literal, Sequence
from dataclasses import dataclass

from .fields import name_field, power_field, power_forecast_field


@dataclass
class LoadForecastConfig:
    """Forecast load element configuration."""

    element_type: Literal["load_forecast"] = "load_forecast"

    name: str = name_field("Load name")

    current_power: float = power_field("Current power consumption in watts")
    forecast: Sequence[str] = power_forecast_field("Sensor(s) providing power consumption forecast")
