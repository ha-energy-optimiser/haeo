"""Load device configuration flow for HAEO integration."""

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
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from ..const import (
    ELEMENT_TYPE_LOAD,
    CONF_LOAD_TYPE,
    CONF_POWER,
    CONF_ENERGY,
    CONF_FORECAST_SENSORS,
    LOAD_TYPE_FIXED,
    LOAD_TYPE_VARIABLE,
    LOAD_TYPE_FORECAST,
)
from . import (
    validate_element_name,
    validate_positive_number,
)

_LOGGER = logging.getLogger(__name__)


def get_load_schema() -> vol.Schema:
    """Get the load configuration schema."""
    return vol.Schema(
        {
            vol.Required(CONF_NAME): vol.All(str, validate_element_name),
            vol.Required(CONF_LOAD_TYPE): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        SelectOptionDict(value=LOAD_TYPE_FIXED, label="Fixed Power"),
                        SelectOptionDict(value=LOAD_TYPE_VARIABLE, label="Variable Power"),
                        SelectOptionDict(value=LOAD_TYPE_FORECAST, label="Forecast-based"),
                    ],
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(CONF_POWER): vol.All(
                NumberSelector(
                    NumberSelectorConfig(
                        mode=NumberSelectorMode.BOX,
                        min=0,
                        step=1,
                        unit_of_measurement="W",
                    )
                ),
                validate_positive_number,
            ),
            vol.Optional(CONF_ENERGY): vol.All(
                NumberSelector(
                    NumberSelectorConfig(
                        mode=NumberSelectorMode.BOX,
                        min=0,
                        step=1,
                        unit_of_measurement="Wh",
                    )
                ),
                validate_positive_number,
            ),
            vol.Optional(CONF_FORECAST_SENSORS): EntitySelector(EntitySelectorConfig(domain="sensor", multiple=True)),
        }
    )


def create_load_participant(config: dict[str, Any]) -> dict[str, Any]:
    """Create a load participant configuration."""
    return {
        "type": ELEMENT_TYPE_LOAD,
        **config,
    }
