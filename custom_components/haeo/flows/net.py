"""Net device configuration flow for HAEO integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.const import CONF_NAME

from ..const import ENTITY_TYPE_NET
from . import validate_entity_name

_LOGGER = logging.getLogger(__name__)


def get_net_schema() -> vol.Schema:
    """Get the net configuration schema."""
    return vol.Schema(
        {
            vol.Required(CONF_NAME): vol.All(str, validate_entity_name),
        }
    )


def create_net_participant(config: dict[str, Any]) -> dict[str, Any]:
    """Create a net participant configuration."""
    return {
        "type": ENTITY_TYPE_NET,
        **config,
    }
