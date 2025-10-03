"""Generator element configuration for HAEO integration."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from .fields import boolean_field, name_field, power_forecast_field, price_field


@dataclass
class GeneratorConfig:
    """Generator element configuration."""

    element_type: Literal["generator"] = "generator"

    name: str = name_field("Generator name")

    forecast: Sequence[str] = power_forecast_field("Sensor(s) providing generation forecast")
    curtailment: bool = boolean_field("Whether generation can be curtailed", default=True)

    price_production: float | None = price_field("Revenue per kWh generated", optional=True)
