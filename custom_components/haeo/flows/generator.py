"""Generator device configuration flow for HAEO integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass
import voluptuous as vol
from homeassistant.const import CONF_NAME
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from ..const import (
    CONF_POWER_SENSOR,
    ELEMENT_TYPE_GENERATOR,
    CONF_CURTAILMENT,
    CONF_PRICE_PRODUCTION,
    CONF_FORECAST_SENSORS,
    CONF_ELEMENT_TYPE,
)
from . import validate_element_name, validate_power_sensor, validate_power_forecast_sensors, validate_price_sensors

_LOGGER = logging.getLogger(__name__)


def get_generator_schema(current_config: dict[str, Any] | None = None, **kwargs) -> vol.Schema:
    """Get the generator configuration schema."""
    # Use current config values as defaults if provided, otherwise use standard defaults
    defaults = {
        CONF_NAME: None,
        CONF_POWER_SENSOR: None,
        CONF_FORECAST_SENSORS: [],
        CONF_CURTAILMENT: False,
        CONF_PRICE_PRODUCTION: None,
    }
    if current_config:
        defaults.update(current_config)

    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=defaults[CONF_NAME]): vol.All(str, validate_element_name),
            vol.Required(CONF_POWER_SENSOR, default=defaults[CONF_POWER_SENSOR]): validate_power_sensor,
            vol.Optional(
                CONF_FORECAST_SENSORS, default=defaults[CONF_FORECAST_SENSORS]
            ): validate_power_forecast_sensors,
            vol.Required(CONF_CURTAILMENT, default=defaults[CONF_CURTAILMENT]): bool,
            vol.Optional(CONF_PRICE_PRODUCTION, default=defaults[CONF_PRICE_PRODUCTION]): validate_price_sensors,
        }
    )


def create_generator_participant(config: dict[str, Any]) -> dict[str, Any]:
    """Create a generator participant configuration."""
    return {
        CONF_ELEMENT_TYPE: ELEMENT_TYPE_GENERATOR,
        **config,
    }
