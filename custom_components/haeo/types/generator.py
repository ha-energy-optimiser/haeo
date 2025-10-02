"""Generator element configuration for HAEO integration."""

from __future__ import annotations

from typing import Literal, Sequence
from dataclasses import dataclass

from .fields import power_forecast_sensors_field, name_field, price_field, boolean_field, power_sensors_field


@dataclass
class GeneratorConfig:
    """Generator element configuration."""

    element_type: Literal["generator"] = "generator"

    name: str = name_field("Generator name")

    power_sensor: Sequence[str] = power_sensors_field("Sensor providing current generation power")
    forecast_sensors: Sequence[str] = power_forecast_sensors_field("Sensor(s) providing generation forecast")
    curtailment: bool = boolean_field("Whether generation can be curtailed", default=True)

    price_production: float | None = price_field("Revenue per kWh generated", optional=True)
