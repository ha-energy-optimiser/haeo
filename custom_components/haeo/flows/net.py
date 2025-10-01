"""Net device configuration flow for HAEO integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.const import CONF_NAME

from ..const import ELEMENT_TYPE_NET, CONF_ELEMENT_TYPE
from . import validate_element_name

_LOGGER = logging.getLogger(__name__)


def get_net_schema(current_config: dict[str, Any] | None = None) -> vol.Schema:
    """Get the net configuration schema."""
    # Use current config values as defaults if provided, otherwise use standard defaults
    defaults = {
        CONF_NAME: None,
    }
    if current_config:
        defaults.update(current_config)

    return vol.Schema({vol.Required(CONF_NAME, default=defaults[CONF_NAME]): vol.All(str, validate_element_name)})


def create_net_participant(config: dict[str, Any]) -> dict[str, Any]:
    """Create a net participant configuration."""
    return {
        CONF_ELEMENT_TYPE: ELEMENT_TYPE_NET,
        **config,
    }
