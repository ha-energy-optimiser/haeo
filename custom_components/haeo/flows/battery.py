"""Battery device configuration flow for HAEO integration."""

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
    ENTITY_TYPE_BATTERY,
    CONF_CAPACITY,
    CONF_CURRENT_CHARGE_SENSOR,
    CONF_MIN_CHARGE_PERCENTAGE,
    CONF_MAX_CHARGE_PERCENTAGE,
    CONF_MAX_CHARGE_POWER,
    CONF_MAX_DISCHARGE_POWER,
    CONF_EFFICIENCY,
    CONF_CHARGE_COST,
    CONF_DISCHARGE_COST,
)
from . import (
    validate_entity_name,
    validate_positive_number,
    validate_percentage,
    validate_efficiency,
    validate_non_negative_number,
)

_LOGGER = logging.getLogger(__name__)


def get_battery_schema() -> vol.Schema:
    """Get the battery configuration schema."""
    return vol.Schema(
        {
            vol.Required(CONF_NAME): vol.All(str, validate_entity_name),
            vol.Required(CONF_CAPACITY): vol.All(
                NumberSelector(
                    NumberSelectorConfig(
                        mode=NumberSelectorMode.BOX,
                        min=1,
                        step=1,
                        unit_of_measurement="Wh",
                    )
                ),
                validate_positive_number,
            ),
            vol.Required(CONF_CURRENT_CHARGE_SENSOR): EntitySelector(EntitySelectorConfig(domain="sensor")),
            vol.Optional(CONF_MIN_CHARGE_PERCENTAGE, default=10): vol.All(
                NumberSelector(
                    NumberSelectorConfig(
                        mode=NumberSelectorMode.BOX,
                        min=0,
                        max=100,
                        step=1,
                        unit_of_measurement="%",
                    )
                ),
                validate_percentage,
            ),
            vol.Optional(CONF_MAX_CHARGE_PERCENTAGE, default=90): vol.All(
                NumberSelector(
                    NumberSelectorConfig(
                        mode=NumberSelectorMode.BOX,
                        min=0,
                        max=100,
                        step=1,
                        unit_of_measurement="%",
                    )
                ),
                validate_percentage,
            ),
            vol.Required(CONF_MAX_CHARGE_POWER): vol.All(
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
            vol.Required(CONF_MAX_DISCHARGE_POWER): vol.All(
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
            vol.Optional(CONF_EFFICIENCY, default=0.95): vol.All(
                NumberSelector(
                    NumberSelectorConfig(
                        mode=NumberSelectorMode.BOX,
                        min=0.01,
                        max=1.0,
                        step=0.01,
                    )
                ),
                validate_efficiency,
            ),
            vol.Optional(CONF_CHARGE_COST, default=0): vol.All(
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
            vol.Optional(CONF_DISCHARGE_COST, default=0): vol.All(
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
        }
    )


def create_battery_participant(config: dict[str, Any]) -> dict[str, Any]:
    """Create a battery participant configuration."""
    return {
        "type": ENTITY_TYPE_BATTERY,
        **config,
    }
