from __future__ import annotations

from typing import Literal, Sequence
from dataclasses import dataclass

from .fields import name_field, power_sensors_field, power_forecast_sensors_field


@dataclass
class LoadForecastConfig:
    """Forecast load element configuration."""

    element_type: Literal["load_forecast"] = "load_forecast"

    name: str = name_field("Load name")

    current_power: Sequence[str] = power_sensors_field("Sensor(s) providing current power consumption")
    forecast_sensors: Sequence[str] = power_forecast_sensors_field("Sensor(s) providing power consumption forecast")
