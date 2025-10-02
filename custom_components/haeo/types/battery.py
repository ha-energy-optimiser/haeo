"""Battery element configuration for HAEO integration."""

from __future__ import annotations

from typing import Literal
from dataclasses import dataclass

from .fields import (
    name_field,
    energy_field,
    battery_soc_sensor_field,
    battery_soc_field,
    percentage_field,
    power_field,
    price_field,
)


@dataclass
class BatteryConfig:
    """Battery element configuration."""

    element_type: Literal["battery"] = "battery"

    name: str = name_field("Battery name")

    capacity: float = energy_field("Battery capacity in Wh")
    current_charge: str = battery_soc_sensor_field("Sensor for current battery charge level")

    min_charge_percentage: float = battery_soc_field("Minimum charge percentage", default=10)
    max_charge_percentage: float = battery_soc_field("Maximum charge percentage", default=90)
    efficiency: float = percentage_field("Efficiency", default=99)

    max_charge_power: float | None = power_field("Maximum charging power rate in W", optional=True)
    max_discharge_power: float | None = power_field("Maximum discharging power rate in W", optional=True)
    charge_cost: float | None = price_field("Cost per kWh charged", optional=True)
    discharge_cost: float | None = price_field("Cost per kWh discharged", optional=True)
