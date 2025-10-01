"""Grid device configuration flow for HAEO integration."""

from __future__ import annotations

import logging
from typing import Any

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
    ELEMENT_TYPE_GRID,
    CONF_IMPORT_LIMIT,
    CONF_EXPORT_LIMIT,
    CONF_PRICE_IMPORT,
    CONF_PRICE_EXPORT,
    CONF_PRICE_IMPORT_SENSOR,
    CONF_PRICE_EXPORT_SENSOR,
)
from . import (
    validate_element_name,
    validate_positive_number,
    validate_non_negative_number,
)

_LOGGER = logging.getLogger(__name__)


def get_grid_schema() -> vol.Schema:
    """Get the grid configuration schema."""
    return vol.Schema(
        {
            vol.Required(CONF_NAME): vol.All(str, validate_element_name),
            vol.Optional(CONF_IMPORT_LIMIT): vol.All(
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
            vol.Optional(CONF_EXPORT_LIMIT): vol.All(
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
            vol.Optional(CONF_PRICE_IMPORT): vol.All(
                NumberSelector(
                    NumberSelectorConfig(
                        mode=NumberSelectorMode.BOX,
                        min=0,
                        step=0.01,
                        unit_of_measurement="$/kWh",
                    )
                ),
                validate_non_negative_number,
            ),
            vol.Optional(CONF_PRICE_EXPORT): vol.All(
                NumberSelector(
                    NumberSelectorConfig(
                        mode=NumberSelectorMode.BOX,
                        min=0,
                        step=0.01,
                        unit_of_measurement="$/kWh",
                    )
                ),
                validate_non_negative_number,
            ),
            vol.Optional(CONF_PRICE_IMPORT_SENSOR): EntitySelector(EntitySelectorConfig(domain="sensor")),
            vol.Optional(CONF_PRICE_EXPORT_SENSOR): EntitySelector(EntitySelectorConfig(domain="sensor")),
        }
    )


def create_grid_participant(config: dict[str, Any]) -> dict[str, Any]:
    """Create a grid participant configuration."""
    return {
        "type": ELEMENT_TYPE_GRID,
        **config,
    }
