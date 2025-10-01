"""Battery device configuration flow for HAEO integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.const import CONF_NAME


from ..const import (
    ELEMENT_TYPE_BATTERY,
    CONF_CAPACITY,
    CONF_CURRENT_CHARGE_SENSOR,
    CONF_MIN_CHARGE_PERCENTAGE,
    CONF_MAX_CHARGE_PERCENTAGE,
    CONF_MAX_CHARGE_POWER,
    CONF_MAX_DISCHARGE_POWER,
    CONF_EFFICIENCY,
    CONF_CHARGE_COST,
    CONF_DISCHARGE_COST,
    CONF_ELEMENT_TYPE,
)
from . import (
    validate_element_name,
    validate_percentage,
    validate_efficiency,
    validate_energy_value,
    validate_energy_sensor,
    validate_power_value,
    validate_price_sensors,
)

_LOGGER = logging.getLogger(__name__)


def get_battery_schema(current_config: dict[str, Any] | None = None, **kwargs) -> vol.Schema:
    """Get the battery configuration schema."""
    # Use current config values as defaults if provided, otherwise use standard defaults
    defaults = {
        CONF_NAME: None,
        CONF_CAPACITY: None,
        CONF_CURRENT_CHARGE_SENSOR: None,
        CONF_MIN_CHARGE_PERCENTAGE: 10,
        CONF_MAX_CHARGE_PERCENTAGE: 90,
        CONF_MAX_CHARGE_POWER: None,
        CONF_MAX_DISCHARGE_POWER: None,
        CONF_EFFICIENCY: 0.99,
        CONF_CHARGE_COST: None,
        CONF_DISCHARGE_COST: None,
    }
    if current_config:
        defaults.update(current_config)

    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=defaults[CONF_NAME]): vol.All(str, validate_element_name),
            vol.Required(CONF_CAPACITY, default=defaults[CONF_CAPACITY]): validate_energy_value,
            vol.Required(
                CONF_CURRENT_CHARGE_SENSOR, default=defaults[CONF_CURRENT_CHARGE_SENSOR]
            ): validate_energy_sensor,
            vol.Optional(CONF_MIN_CHARGE_PERCENTAGE, default=defaults[CONF_MIN_CHARGE_PERCENTAGE]): validate_percentage,
            vol.Optional(CONF_MAX_CHARGE_PERCENTAGE, default=defaults[CONF_MAX_CHARGE_PERCENTAGE]): validate_percentage,
            vol.Required(CONF_MAX_CHARGE_POWER, default=defaults[CONF_MAX_CHARGE_POWER]): validate_power_value,
            vol.Required(CONF_MAX_DISCHARGE_POWER, default=defaults[CONF_MAX_DISCHARGE_POWER]): validate_power_value,
            vol.Optional(CONF_EFFICIENCY, default=defaults[CONF_EFFICIENCY]): validate_efficiency,
            vol.Optional(CONF_CHARGE_COST, default=defaults[CONF_CHARGE_COST]): validate_price_sensors,
            vol.Optional(CONF_DISCHARGE_COST, default=defaults[CONF_DISCHARGE_COST]): validate_price_sensors,
        }
    )


def create_battery_participant(config: dict[str, Any]) -> dict[str, Any]:
    """Create a battery participant configuration."""
    return {
        CONF_ELEMENT_TYPE: ELEMENT_TYPE_BATTERY,
        **config,
    }
