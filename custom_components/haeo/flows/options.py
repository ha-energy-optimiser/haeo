"""Options flow for HAEO hub management."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from ..const import (
    ELEMENT_TYPE_BATTERY,
    ELEMENT_TYPE_GRID,
    ELEMENT_TYPE_LOAD,
    ELEMENT_TYPE_GENERATOR,
    ELEMENT_TYPE_NET,
    ELEMENT_TYPE_CONNECTION,
)
from .battery import get_battery_schema, create_battery_participant
from .grid import get_grid_schema, create_grid_participant
from .load import get_load_schema, create_load_participant
from .generator import get_generator_schema, create_generator_participant
from .net import get_net_schema, create_net_participant
from .connection import (
    get_connection_schema,
    create_connection_participant,
    validate_connection_config,
)

_LOGGER = logging.getLogger(__name__)


class HubOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for HAEO hub."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage the options."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["add_participant", "manage_participants", "remove_participant"],
        )

    async def async_step_add_participant(self, user_input: dict[str, Any] | None = None):
        """Add a new participant."""
        if user_input is not None:
            participant_type = user_input["participant_type"]

            # Route to specific configuration step
            if participant_type == ELEMENT_TYPE_BATTERY:
                return await self.async_step_configure_battery()
            elif participant_type == ELEMENT_TYPE_GRID:
                return await self.async_step_configure_grid()
            elif participant_type == ELEMENT_TYPE_LOAD:
                return await self.async_step_configure_load()
            elif participant_type == ELEMENT_TYPE_GENERATOR:
                return await self.async_step_configure_generator()
            elif participant_type == ELEMENT_TYPE_NET:
                return await self.async_step_configure_net()
            elif participant_type == ELEMENT_TYPE_CONNECTION:
                return await self.async_step_configure_connection()

        # Show participant type selection
        participant_types = [
            ELEMENT_TYPE_BATTERY,
            ELEMENT_TYPE_GRID,
            ELEMENT_TYPE_LOAD,
            ELEMENT_TYPE_GENERATOR,
            ELEMENT_TYPE_NET,
            ELEMENT_TYPE_CONNECTION,
        ]

        return self.async_show_form(
            step_id="add_participant",
            data_schema=vol.Schema(
                {
                    vol.Required("participant_type"): SelectSelector(
                        SelectSelectorConfig(
                            options=participant_types,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
        )

    async def async_step_configure_battery(self, user_input: dict[str, Any] | None = None):
        """Configure battery participant."""
        errors: dict[str, str] = {}

        if user_input is not None:
            name = user_input[CONF_NAME]

            # Check for duplicate names
            if self._check_participant_name_exists(name):
                errors[CONF_NAME] = "name_exists"
            else:
                # Add participant to configuration
                return await self._add_participant(name, create_battery_participant(user_input))

        return self.async_show_form(
            step_id="configure_battery",
            data_schema=get_battery_schema(),
            errors=errors,
        )

    async def async_step_configure_grid(self, user_input: dict[str, Any] | None = None):
        """Configure grid participant."""
        errors: dict[str, str] = {}

        if user_input is not None:
            name = user_input[CONF_NAME]

            # Check for duplicate names
            if self._check_participant_name_exists(name):
                errors[CONF_NAME] = "name_exists"
            else:
                # Add participant to configuration
                return await self._add_participant(name, create_grid_participant(user_input))

        return self.async_show_form(
            step_id="configure_grid",
            data_schema=get_grid_schema(),
            errors=errors,
        )

    async def async_step_configure_load(self, user_input: dict[str, Any] | None = None):
        """Configure load participant."""
        errors: dict[str, str] = {}

        if user_input is not None:
            name = user_input[CONF_NAME]

            # Check for duplicate names
            if self._check_participant_name_exists(name):
                errors[CONF_NAME] = "name_exists"
            else:
                # Add participant to configuration
                return await self._add_participant(name, create_load_participant(user_input))

        return self.async_show_form(
            step_id="configure_load",
            data_schema=get_load_schema(),
            errors=errors,
        )

    async def async_step_configure_generator(self, user_input: dict[str, Any] | None = None):
        """Configure generator participant."""
        errors: dict[str, str] = {}

        if user_input is not None:
            name = user_input[CONF_NAME]

            # Check for duplicate names
            if self._check_participant_name_exists(name):
                errors[CONF_NAME] = "name_exists"
            else:
                # Add participant to configuration
                return await self._add_participant(name, create_generator_participant(user_input))

        return self.async_show_form(
            step_id="configure_generator",
            data_schema=get_generator_schema(),
            errors=errors,
        )

    async def async_step_configure_net(self, user_input: dict[str, Any] | None = None):
        """Configure net participant."""
        errors: dict[str, str] = {}

        if user_input is not None:
            name = user_input[CONF_NAME]

            # Check for duplicate names
            if self._check_participant_name_exists(name):
                errors[CONF_NAME] = "name_exists"
            else:
                # Add participant to configuration
                return await self._add_participant(name, create_net_participant(user_input))

        return self.async_show_form(
            step_id="configure_net",
            data_schema=get_net_schema(),
            errors=errors,
        )

    async def async_step_configure_connection(self, user_input: dict[str, Any] | None = None):
        """Configure connection participant."""
        errors: dict[str, str] = {}
        participants = self.config_entry.data.get("participants", {})

        # Filter out existing connections to avoid connecting connections
        device_participants = {
            name: config for name, config in participants.items() if config.get("type") != ELEMENT_TYPE_CONNECTION
        }

        if len(device_participants) < 2:
            return self.async_abort(reason="insufficient_devices")

        if user_input is not None:
            name = user_input[CONF_NAME]

            # Check for duplicate names
            if self._check_participant_name_exists(name):
                errors[CONF_NAME] = "name_exists"

            # Validate connection configuration
            connection_errors = validate_connection_config(user_input)
            errors.update(connection_errors)

            if not errors:
                # Add participant to configuration
                return await self._add_participant(name, create_connection_participant(user_input))

        return self.async_show_form(
            step_id="configure_connection",
            data_schema=get_connection_schema(device_participants),
            errors=errors,
        )

    async def async_step_manage_participants(self, user_input: dict[str, Any] | None = None):
        """Manage existing participants."""
        participants = self.config_entry.data.get("participants", {})

        if not participants:
            return self.async_abort(reason="no_participants")

        if user_input is not None:
            # For now, just show the selected participant info
            # In the future, this could allow editing
            return self.async_create_entry(title="", data={})

        participant_options = list(participants.keys())

        return self.async_show_form(
            step_id="manage_participants",
            data_schema=vol.Schema(
                {
                    vol.Required("participant"): SelectSelector(
                        SelectSelectorConfig(
                            options=participant_options,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
        )

    async def async_step_remove_participant(self, user_input: dict[str, Any] | None = None):
        """Remove a participant."""
        participants = self.config_entry.data.get("participants", {})

        if not participants:
            return self.async_abort(reason="no_participants")

        if user_input is not None:
            participant_name = user_input["participant"]

            # Remove participant from configuration
            new_data = self.config_entry.data.copy()
            new_participants = new_data["participants"].copy()
            del new_participants[participant_name]
            new_data["participants"] = new_participants

            self.hass.config_entries.async_update_entry(self.config_entry, data=new_data)
            return self.async_create_entry(title="", data={})

        participant_options = list(participants.keys())

        return self.async_show_form(
            step_id="remove_participant",
            data_schema=vol.Schema(
                {
                    vol.Required("participant"): SelectSelector(
                        SelectSelectorConfig(
                            options=participant_options,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
        )

    def _check_participant_name_exists(self, name: str, exclude_current: str | None = None) -> bool:
        """Check if a participant name already exists."""
        participants = self.config_entry.data.get("participants", {})
        return name in participants and name != exclude_current

    async def _add_participant(self, name: str, participant_config: dict[str, Any]):
        """Add a participant to the configuration."""
        new_data = self.config_entry.data.copy()
        new_participants = new_data["participants"].copy()
        new_participants[name] = participant_config
        new_data["participants"] = new_participants

        self.hass.config_entries.async_update_entry(self.config_entry, data=new_data)
        return self.async_create_entry(title="", data={})
