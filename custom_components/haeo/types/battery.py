"""Battery element configuration for HAEO integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .fields import (
    battery_soc_field,
    battery_soc_sensor_field,
    energy_field,
    name_field,
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
    initial_charge_percentage: str = battery_soc_sensor_field("Sensor for current battery charge percentage")

    min_charge_percentage: float = battery_soc_field("Minimum charge percentage", default=10)
    max_charge_percentage: float = battery_soc_field("Maximum charge percentage", default=90)
    efficiency: float = percentage_field("Efficiency", default=99)

    max_charge_power: float | None = power_field("Maximum charging power rate in W", optional=True)
    max_discharge_power: float | None = power_field("Maximum discharging power rate in W", optional=True)
    charge_cost: float | None = price_field("Cost per kWh charged", optional=True)
    discharge_cost: float | None = price_field("Cost per kWh discharged", optional=True)
