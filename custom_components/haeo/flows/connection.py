"""Connection device configuration flow for HAEO integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.const import CONF_NAME
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from ..const import (
    CONF_SOURCE,
    CONF_TARGET,
    CONF_MIN_POWER,
    CONF_MAX_POWER,
    ELEMENT_TYPE_CONNECTION,
)
from . import (
    validate_element_name,
    validate_positive_number,
    validate_non_negative_number,
)

_LOGGER = logging.getLogger(__name__)


def get_connection_schema(participants: dict[str, Any]) -> vol.Schema:
    """Get the connection configuration schema."""
    participant_options = list(participants.keys())

    return vol.Schema(
        {
            vol.Required(CONF_NAME): vol.All(str, validate_element_name),
            vol.Required(CONF_SOURCE): SelectSelector(
                SelectSelectorConfig(
                    options=participant_options,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(CONF_TARGET): SelectSelector(
                SelectSelectorConfig(
                    options=participant_options,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(CONF_MIN_POWER, default=0): vol.All(
                NumberSelector(
                    NumberSelectorConfig(
                        mode=NumberSelectorMode.BOX,
                        min=0,
                        step=1,
                        unit_of_measurement="W",
                    )
                ),
                validate_non_negative_number,
            ),
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
        }
    )


def validate_connection_config(config: dict[str, Any]) -> dict[str, str]:
    """Validate connection configuration."""
    errors = {}

    # Ensure source and target are different
    if config.get(CONF_SOURCE) == config.get(CONF_TARGET):
        errors[CONF_TARGET] = "cannot_connect_to_self"

    # Ensure min_power <= max_power if both are specified
    min_power = config.get(CONF_MIN_POWER, 0)
    max_power = config.get(CONF_MAX_POWER)
    if max_power is not None and min_power > max_power:
        errors[CONF_MIN_POWER] = "min_power_too_high"

    return errors


def create_connection_participant(config: dict[str, Any]) -> dict[str, Any]:
    """Create a connection participant configuration."""
    return {
        "type": ELEMENT_TYPE_CONNECTION,
        **config,
    }
