"""Generator device configuration flow for HAEO integration."""

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
    ELEMENT_TYPE_GENERATOR,
    CONF_MAX_POWER,
    CONF_CURTAILMENT,
    CONF_PRICE_PRODUCTION,
    CONF_PRICE_CONSUMPTION,
    CONF_FORECAST_SENSORS,
)
from . import (
    validate_element_name,
    validate_positive_number,
    validate_non_negative_number,
)

_LOGGER = logging.getLogger(__name__)


def get_generator_schema() -> vol.Schema:
    """Get the generator configuration schema."""
    return vol.Schema(
        {
            vol.Required(CONF_NAME): vol.All(str, validate_element_name),
            vol.Optional(CONF_MAX_POWER): vol.All(
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
            vol.Optional(CONF_CURTAILMENT, default=True): bool,
            vol.Optional(CONF_PRICE_PRODUCTION): vol.All(
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
            vol.Optional(CONF_PRICE_CONSUMPTION): vol.All(
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
            vol.Optional(CONF_FORECAST_SENSORS): EntitySelector(EntitySelectorConfig(domain="sensor", multiple=True)),
        }
    )


def create_generator_participant(config: dict[str, Any]) -> dict[str, Any]:
    """Create a generator participant configuration."""
    return {
        "type": ELEMENT_TYPE_GENERATOR,
        **config,
    }
