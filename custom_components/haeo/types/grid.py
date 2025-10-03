"""Grid element configuration for HAEO integration."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from .fields import name_field, power_field, price_forecast_field, price_sensors_field


@dataclass
class GridConfig:
    """Grid element configuration."""

    element_type: Literal["grid"] = "grid"

    name: str = name_field("Grid connection name")

    import_price: Sequence[str] = price_sensors_field("Sensor for current import price")
    export_price: Sequence[str] = price_sensors_field("Sensor for current export price")

    import_price_forecast: Sequence[str] = price_forecast_field("Sensor(s) for import price forecast")
    export_price_forecast: Sequence[str] = price_forecast_field("Sensor(s) for export price forecast")

    import_limit: float | None = power_field("Maximum import power in W", optional=True)
    export_limit: float | None = power_field("Maximum export power in W", optional=True)
