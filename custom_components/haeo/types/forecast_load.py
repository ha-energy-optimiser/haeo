from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from .fields import name_field, power_forecast_field


@dataclass
class ForecastLoadConfig:
    """Forecast load element configuration."""

    element_type: Literal["forecast_load"] = "forecast_load"

    name: str = name_field("Load name")

    forecast: Sequence[str] = power_forecast_field("Sensor(s) providing power consumption forecast")
