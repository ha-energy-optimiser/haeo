"""Hub configuration flow for HAEO integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME

from ..const import DOMAIN
from . import validate_element_name

_LOGGER = logging.getLogger(__name__)


class HubConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HAEO hub creation."""

    VERSION = 1
    MINOR_VERSION = 1

    def _check_existing_names(self, name: str) -> bool:
        """Check if integration name already exists."""
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            if entry.title == name:
                return True
        return False

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step for hub creation."""
        errors: dict[str, str] = {}

        if user_input is not None:
            hub_name = user_input[CONF_NAME]

            # Check for duplicate names
            if self._check_existing_names(hub_name):
                errors[CONF_NAME] = "name_exists"
            else:
                # Create hub entry
                await self.async_set_unique_id(f"haeo_hub_{hub_name.lower().replace(' ', '_')}")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=hub_name,
                    data={
                        "integration_type": "hub",
                        CONF_NAME: hub_name,
                        "participants": {},
                    },
                )

        # Show form
        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME): vol.All(str, validate_element_name),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Get the options flow for this handler."""
        from .options import HubOptionsFlow

        return HubOptionsFlow()
