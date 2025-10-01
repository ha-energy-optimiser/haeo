"""Grid device configuration flow for HAEO integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import CONF_NAME
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from ..const import (
    CONF_PRICE_EXPORT_FORECAST_SENSOR,
    CONF_PRICE_IMPORT_FORECAST_SENSOR,
    ELEMENT_TYPE_GRID,
    CONF_IMPORT_LIMIT,
    CONF_EXPORT_LIMIT,
    CONF_PRICE_IMPORT_SENSOR,
    CONF_PRICE_EXPORT_SENSOR,
    CONF_ELEMENT_TYPE,
)
from . import (
    validate_element_name,
    validate_positive_number,
)

_LOGGER = logging.getLogger(__name__)


def get_grid_schema(current_config: dict[str, Any] | None = None) -> vol.Schema:
    """Get the grid configuration schema."""
    # Use current config values as defaults if provided, otherwise use standard defaults
    defaults = {
        CONF_NAME: None,
        CONF_IMPORT_LIMIT: None,
        CONF_EXPORT_LIMIT: None,
        CONF_PRICE_IMPORT_SENSOR: None,
        CONF_PRICE_EXPORT_SENSOR: None,
        CONF_PRICE_IMPORT_FORECAST_SENSOR: None,
        CONF_PRICE_EXPORT_FORECAST_SENSOR: None,
    }
    if current_config:
        defaults.update(current_config)

    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=defaults[CONF_NAME]): vol.All(str, validate_element_name),
            vol.Optional(CONF_IMPORT_LIMIT, default=defaults[CONF_IMPORT_LIMIT]): vol.All(
                NumberSelector(
                    NumberSelectorConfig(
                        mode=NumberSelectorMode.BOX,
                        min=1,
                        step=1,
                        unit_of_measurement="W",
                    )
                ),
                validate_positive_number,
            ),
            vol.Optional(CONF_EXPORT_LIMIT, default=defaults[CONF_EXPORT_LIMIT]): vol.All(
                NumberSelector(
                    NumberSelectorConfig(
                        mode=NumberSelectorMode.BOX,
                        min=1,
                        step=1,
                        unit_of_measurement="W",
                    )
                ),
                validate_positive_number,
            ),
            vol.Required(CONF_PRICE_IMPORT_SENSOR, default=defaults[CONF_PRICE_IMPORT_SENSOR]): EntitySelector(
                EntitySelectorConfig(
                    domain="sensor",
                    device_class=[
                        SensorDeviceClass.MONETARY,
                        SensorDeviceClass.ENERGY,
                    ],
                )
            ),
            vol.Required(CONF_PRICE_EXPORT_SENSOR, default=defaults[CONF_PRICE_EXPORT_SENSOR]): EntitySelector(
                EntitySelectorConfig(
                    domain="sensor",
                    device_class=[
                        SensorDeviceClass.MONETARY,
                        SensorDeviceClass.ENERGY,
                    ],
                )
            ),
            vol.Required(
                CONF_PRICE_IMPORT_FORECAST_SENSOR, default=defaults[CONF_PRICE_IMPORT_FORECAST_SENSOR]
            ): EntitySelector(
                EntitySelectorConfig(
                    domain="sensor",
                    device_class=[
                        SensorDeviceClass.MONETARY,
                        SensorDeviceClass.ENERGY,
                    ],
                )
            ),
            vol.Required(
                CONF_PRICE_EXPORT_FORECAST_SENSOR, default=defaults[CONF_PRICE_EXPORT_FORECAST_SENSOR]
            ): EntitySelector(
                EntitySelectorConfig(
                    domain="sensor",
                    device_class=[
                        SensorDeviceClass.MONETARY,
                        SensorDeviceClass.ENERGY,
                    ],
                )
            ),
        }
    )


def create_grid_participant(config: dict[str, Any]) -> dict[str, Any]:
    """Create a grid participant configuration."""
    return {
        CONF_ELEMENT_TYPE: ELEMENT_TYPE_GRID,
        **config,
    }
