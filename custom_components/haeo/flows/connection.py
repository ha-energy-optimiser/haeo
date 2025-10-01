"""Connection device configuration flow for HAEO integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.const import CONF_NAME
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig, SelectSelectorMode

from ..const import (
    CONF_SOURCE,
    CONF_TARGET,
    CONF_MIN_POWER,
    CONF_MAX_POWER,
    ELEMENT_TYPE_CONNECTION,
    CONF_ELEMENT_TYPE,
)
from . import validate_element_name, validate_power_flow_value

_LOGGER = logging.getLogger(__name__)


def get_connection_schema(participants: dict[str, Any], current_config: dict[str, Any] | None = None) -> vol.Schema:
    """Get the connection configuration schema."""
    # Use current config values as defaults if provided, otherwise use standard defaults
    defaults = {
        CONF_NAME: None,
        CONF_SOURCE: None,
        CONF_TARGET: None,
        CONF_MIN_POWER: None,
        CONF_MAX_POWER: None,
    }
    if current_config:
        defaults.update(current_config)

    participant_options = list(participants.keys())

    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=defaults[CONF_NAME]): vol.All(str, validate_element_name),
            vol.Required(CONF_SOURCE, default=defaults[CONF_SOURCE]): SelectSelector(
                SelectSelectorConfig(
                    options=participant_options,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(CONF_TARGET, default=defaults[CONF_TARGET]): SelectSelector(
                SelectSelectorConfig(
                    options=participant_options,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(CONF_MIN_POWER, default=defaults[CONF_MIN_POWER]): validate_power_flow_value,
            vol.Optional(CONF_MAX_POWER, default=defaults[CONF_MAX_POWER]): validate_power_flow_value,
        }
    )


def validate_connection_config(config: dict[str, Any]) -> dict[str, str]:
    """Validate connection configuration."""
    errors = {}

    # Ensure source and target are different
    if config.get(CONF_SOURCE) == config.get(CONF_TARGET):
        errors[CONF_TARGET] = "cannot_connect_to_self"

    # For bidirectional connections, ensure proper power limits
    min_power = config.get(CONF_MIN_POWER)
    max_power = config.get(CONF_MAX_POWER)

    # If both bounds are None, it's a valid unlimited connection
    if min_power is None and max_power is None:
        return errors

    # Check for invalid power range combinations
    if min_power is not None and max_power is not None and min_power >= 0 and min_power > max_power:
        # min_power cannot be greater than max_power for forward flow
        errors[CONF_MIN_POWER] = "min_power_too_high"

    # Note: We allow negative min_power or max_power independently as they represent
    # different directional limits:
    # - Negative min_power: maximum reverse flow (from target to source)
    # - Negative max_power: would mean no forward flow allowed, but this is unusual
    # - Positive min_power: minimum forward flow required
    # - Positive max_power: maximum forward flow allowed

    return errors


def create_connection_participant(config: dict[str, Any]) -> dict[str, Any]:
    """Create a connection participant configuration."""
    return {
        CONF_ELEMENT_TYPE: ELEMENT_TYPE_CONNECTION,
        **config,
    }
