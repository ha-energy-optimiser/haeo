"""Forecast load element configuration for HAEO integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from .fields import name_field, power_forecast_field

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass
class ForecastLoadConfig:
    """Forecast load element configuration."""

    element_type: Literal["forecast_load"] = "forecast_load"

    name: str = name_field("Load name")

    forecast: Sequence[str] = power_forecast_field("Sensor(s) providing power consumption forecast")
