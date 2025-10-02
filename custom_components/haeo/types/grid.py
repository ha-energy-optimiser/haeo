"""Grid element configuration for HAEO integration."""

from __future__ import annotations

from typing import Literal, Sequence
from dataclasses import dataclass

from .fields import name_field, power_field, price_sensors_field, price_forecast_sensors_field


@dataclass
class GridConfig:
    """Grid element configuration."""

    element_type: Literal["grid"] = "grid"

    name: str = name_field("Grid connection name")

    price_import_sensor: Sequence[str] = price_sensors_field("Sensor for current import price")
    price_export_sensor: Sequence[str] = price_sensors_field("Sensor for current export price")

    price_import_forecast_sensor: Sequence[str] = price_forecast_sensors_field("Sensor(s) for import price forecast")
    price_export_forecast_sensor: Sequence[str] = price_forecast_sensors_field("Sensor(s) for export price forecast")

    import_limit: float | None = power_field("Maximum import power in W", optional=True)
    export_limit: float | None = power_field("Maximum export power in W", optional=True)
