"""Forecast load device configuration flow for HAEO integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.const import CONF_NAME

from ..const import ELEMENT_TYPE_LOAD_FORECAST, CONF_FORECAST_SENSORS, CONF_ELEMENT_TYPE
from . import validate_element_name, validate_power_forecast_sensors

_LOGGER = logging.getLogger(__name__)


def get_forecast_load_schema(current_config: dict[str, Any] | None = None, **kwargs) -> vol.Schema:
    """Get the forecast load configuration schema."""
    # Use current config values as defaults if provided, otherwise use standard defaults
    defaults = {
        CONF_NAME: None,
        CONF_FORECAST_SENSORS: None,
    }
    if current_config:
        defaults.update(current_config)

    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=defaults[CONF_NAME]): validate_element_name,
            vol.Required(
                CONF_FORECAST_SENSORS, default=defaults[CONF_FORECAST_SENSORS]
            ): validate_power_forecast_sensors,
        }
    )


def create_forecast_load_participant(config: dict[str, Any]) -> dict[str, Any]:
    """Create a forecast load participant configuration."""
    return {
        CONF_ELEMENT_TYPE: ELEMENT_TYPE_LOAD_FORECAST,
        **config,
    }
