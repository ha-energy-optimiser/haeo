"""Constant load device configuration flow for HAEO integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.const import CONF_NAME
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from ..const import (
    ELEMENT_TYPE_LOAD_FIXED,
    CONF_POWER,
    CONF_ELEMENT_TYPE,
)
from . import (
    validate_element_name,
    validate_positive_number,
)

_LOGGER = logging.getLogger(__name__)


def get_constant_load_schema(current_config: dict[str, Any] | None = None) -> vol.Schema:
    """Get the constant load configuration schema."""
    # Use current config values as defaults if provided, otherwise use standard defaults
    defaults = {
        CONF_NAME: None,
        CONF_POWER: None,
    }
    if current_config:
        defaults.update(current_config)

    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=defaults[CONF_NAME]): vol.All(str, validate_element_name),
            vol.Required(CONF_POWER, default=defaults[CONF_POWER]): vol.All(
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
        }
    )


def create_constant_load_participant(config: dict[str, Any]) -> dict[str, Any]:
    """Create a constant load participant configuration."""
    return {
        CONF_ELEMENT_TYPE: ELEMENT_TYPE_LOAD_FIXED,
        **config,
    }
