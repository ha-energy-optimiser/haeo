"""Grid device configuration flow for HAEO integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.const import CONF_NAME


from ..const import (
    CONF_PRICE_EXPORT_FORECAST_SENSORS,
    CONF_PRICE_IMPORT_FORECAST_SENSORS,
    ELEMENT_TYPE_GRID,
    CONF_IMPORT_LIMIT,
    CONF_EXPORT_LIMIT,
    CONF_PRICE_IMPORT_SENSOR,
    CONF_PRICE_EXPORT_SENSOR,
    CONF_ELEMENT_TYPE,
)
from . import validate_element_name, validate_power_value, validate_price_sensors


_LOGGER = logging.getLogger(__name__)


def get_grid_schema(current_config: dict[str, Any] | None = None, **kwargs) -> vol.Schema:
    """Get the grid configuration schema."""
    # Use current config values as defaults if provided, otherwise use standard defaults
    defaults = {
        CONF_NAME: vol.UNDEFINED,
        CONF_IMPORT_LIMIT: vol.UNDEFINED,
        CONF_EXPORT_LIMIT: vol.UNDEFINED,
        CONF_PRICE_IMPORT_SENSOR: vol.UNDEFINED,
        CONF_PRICE_EXPORT_SENSOR: vol.UNDEFINED,
        CONF_PRICE_IMPORT_FORECAST_SENSORS: vol.UNDEFINED,
        CONF_PRICE_EXPORT_FORECAST_SENSORS: vol.UNDEFINED,
    }
    if current_config:
        defaults.update(current_config)

    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=defaults[CONF_NAME]): validate_element_name,
            vol.Optional(CONF_IMPORT_LIMIT, default=defaults[CONF_IMPORT_LIMIT]): validate_power_value,
            vol.Optional(CONF_EXPORT_LIMIT, default=defaults[CONF_EXPORT_LIMIT]): validate_power_value,
            vol.Optional(CONF_PRICE_IMPORT_SENSOR, default=defaults[CONF_PRICE_IMPORT_SENSOR]): validate_price_sensors,
            vol.Optional(CONF_PRICE_EXPORT_SENSOR, default=defaults[CONF_PRICE_EXPORT_SENSOR]): validate_price_sensors,
            vol.Optional(
                CONF_PRICE_IMPORT_FORECAST_SENSORS, default=defaults[CONF_PRICE_IMPORT_FORECAST_SENSORS]
            ): validate_price_sensors,
            vol.Optional(
                CONF_PRICE_EXPORT_FORECAST_SENSORS, default=defaults[CONF_PRICE_EXPORT_FORECAST_SENSORS]
            ): validate_price_sensors,
        }
    )


def create_grid_participant(config: dict[str, Any]) -> dict[str, Any]:
    """Create a grid participant configuration."""
    return {
        CONF_ELEMENT_TYPE: ELEMENT_TYPE_GRID,
        **config,
    }
