"""Options flow for HAEO hub management."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from ..const import get_element_type_name, CONF_ELEMENT_TYPE
from ..types import ELEMENT_TYPES
from . import get_schema

_LOGGER = logging.getLogger(__name__)


class HubOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for HAEO hub."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage the options."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["add_participant", "edit_participant", "remove_participant"],
        )

    async def async_step_add_participant(self, user_input: dict[str, Any] | None = None):
        """Add a new participant."""
        if user_input is not None:
            participant_type = user_input["participant_type"]

            # Route to generic configuration step
            return await self.async_step_configure_element(participant_type)

        # Show participant type selection
        participant_types = [
            SelectOptionDict(value=element_type, label=get_element_type_name(element_type))
            for element_type in ELEMENT_TYPES.keys()
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

    async def async_step_configure_element(
        self, element_type: str, user_input: dict[str, Any] | None = None, current_config: dict[str, Any] | None = None
    ):
        """Configure participant."""
        errors: dict[str, str] = {}

        if user_input is not None:
            name = user_input[CONF_NAME]

            # Check for duplicate names (excluding current if editing)
            if self._check_participant_name_exists(
                name, exclude_current=current_config.get(CONF_NAME) if current_config else None
            ):
                errors[CONF_NAME] = "name_exists"
            else:
                if not errors:
                    # Add or update participant in configuration
                    participant = {CONF_ELEMENT_TYPE: element_type, **user_input}
                    if current_config:
                        return await self._update_participant(current_config[CONF_NAME], participant)
                    else:
                        return await self._add_participant(name, participant)

        # Get participants for schema if needed
        participants = self.config_entry.data.get("participants", {})

        return self.async_show_form(
            step_id=f"configure_{element_type}",
            data_schema=get_schema(element_type, participants=participants),
            errors=errors,
        )

    async def async_step_edit_participant(self, user_input: dict[str, Any] | None = None):
        """Edit an existing participant."""
        participants = self.config_entry.data.get("participants", {})

        if not participants:
            return self.async_abort(reason="no_participants")

        if user_input is not None:
            participant_name = user_input["participant"]
            participant_config = participants[participant_name]
            participant_type = participant_config.get("type")

            # Route to generic configure step for editing
            return await self.async_step_configure_element(participant_type, current_config=participant_config)

        participant_options = list(participants.keys())

        return self.async_show_form(
            step_id="edit_participant",
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

            # Reload the integration to ensure devices are updated
            try:
                await self.hass.config_entries.async_reload(self.config_entry.entry_id)
            except Exception as ex:
                _LOGGER.warning("Failed to reload integration after removing participant: %s", ex)

            return self.async_create_entry(title="", data={})

        # Show form for participant selection
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
        if exclude_current and exclude_current in participants:
            # If we're editing, allow the current name
            return name in participants and name != exclude_current
        else:
            # If we're creating, don't allow any duplicates
            return name in participants

    async def _add_participant(self, name: str, participant_config: dict[str, Any]):
        """Add a participant to the configuration."""
        new_data = self.config_entry.data.copy()
        new_participants = new_data["participants"].copy()
        new_participants[name] = participant_config
        new_data["participants"] = new_participants

        self.hass.config_entries.async_update_entry(self.config_entry, data=new_data)

        # Reload the integration to ensure devices are registered
        try:
            await self.hass.config_entries.async_reload(self.config_entry.entry_id)
        except Exception as ex:
            _LOGGER.warning("Failed to reload integration after adding participant: %s", ex)

        return self.async_create_entry(title="", data={})

    async def _update_participant(self, old_name: str, new_config: dict[str, Any]):
        """Update a participant in the configuration."""
        new_data = self.config_entry.data.copy()
        new_participants = new_data["participants"].copy()

        # Remove old participant and add updated one
        if old_name in new_participants:
            del new_participants[old_name]

        new_name = new_config[CONF_NAME]
        new_participants[new_name] = new_config

        new_data["participants"] = new_participants

        self.hass.config_entries.async_update_entry(self.config_entry, data=new_data)

        # Reload the integration to ensure devices are registered
        try:
            await self.hass.config_entries.async_reload(self.config_entry.entry_id)
        except Exception as ex:
            _LOGGER.warning("Failed to reload integration after adding participant: %s", ex)

        return self.async_create_entry(title="", data={})
