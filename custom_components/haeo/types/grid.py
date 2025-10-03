"""Grid element configuration for HAEO integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .fields import name_field, power_field, price_live_forecast_field


@dataclass
class GridConfig:
    """Grid element configuration."""

    element_type: Literal["grid"] = "grid"

    name: str = name_field("Grid connection name")

    import_price: dict[str, Any] = price_live_forecast_field("Import price configuration (live sensor + forecast)")
    export_price: dict[str, Any] = price_live_forecast_field("Export price configuration (live sensor + forecast)")

    import_limit: float | None = power_field("Maximum import power in W", optional=True)
    export_limit: float | None = power_field("Maximum export power in W", optional=True)
