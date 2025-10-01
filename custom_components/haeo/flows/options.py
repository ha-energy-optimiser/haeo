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

from ..const import (
    ELEMENT_TYPE_BATTERY,
    ELEMENT_TYPE_GRID,
    ELEMENT_TYPE_LOAD_FIXED,
    ELEMENT_TYPE_LOAD_FORECAST,
    ELEMENT_TYPE_GENERATOR,
    ELEMENT_TYPE_NET,
    ELEMENT_TYPE_CONNECTION,
    get_element_type_name,
)
from .battery import get_battery_schema, create_battery_participant
from .grid import get_grid_schema, create_grid_participant
from .load_constant import get_constant_load_schema, create_constant_load_participant
from .load_forecast import get_forecast_load_schema, create_forecast_load_participant
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
            menu_options=["add_participant", "edit_participant", "remove_participant"],
        )

    async def async_step_add_participant(self, user_input: dict[str, Any] | None = None):
        """Add a new participant."""
        if user_input is not None:
            participant_type = user_input["participant_type"]

            # Route to specific configuration step
            if participant_type == ELEMENT_TYPE_LOAD_FIXED:
                return await self.async_step_configure_fixed_load()
            elif participant_type == ELEMENT_TYPE_LOAD_FORECAST:
                return await self.async_step_configure_forecast_load()
            elif participant_type == ELEMENT_TYPE_BATTERY:
                return await self.async_step_configure_battery()
            elif participant_type == ELEMENT_TYPE_GRID:
                return await self.async_step_configure_grid()
            elif participant_type == ELEMENT_TYPE_GENERATOR:
                return await self.async_step_configure_generator()
            elif participant_type == ELEMENT_TYPE_NET:
                return await self.async_step_configure_net()
            elif participant_type == ELEMENT_TYPE_CONNECTION:
                return await self.async_step_configure_connection()

        # Show participant type selection
        participant_types = [
            SelectOptionDict(value=ELEMENT_TYPE_LOAD_FIXED, label=get_element_type_name(ELEMENT_TYPE_LOAD_FIXED)),
            SelectOptionDict(value=ELEMENT_TYPE_LOAD_FORECAST, label=get_element_type_name(ELEMENT_TYPE_LOAD_FORECAST)),
            SelectOptionDict(value=ELEMENT_TYPE_BATTERY, label=get_element_type_name(ELEMENT_TYPE_BATTERY)),
            SelectOptionDict(value=ELEMENT_TYPE_GRID, label=get_element_type_name(ELEMENT_TYPE_GRID)),
            SelectOptionDict(value=ELEMENT_TYPE_GENERATOR, label=get_element_type_name(ELEMENT_TYPE_GENERATOR)),
            SelectOptionDict(value=ELEMENT_TYPE_NET, label=get_element_type_name(ELEMENT_TYPE_NET)),
            SelectOptionDict(value=ELEMENT_TYPE_CONNECTION, label=get_element_type_name(ELEMENT_TYPE_CONNECTION)),
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

    async def async_step_configure_battery(
        self, user_input: dict[str, Any] | None = None, current_config: dict[str, Any] | None = None
    ):
        """Configure battery participant."""
        errors: dict[str, str] = {}

        if user_input is not None:
            name = user_input[CONF_NAME]

            # Check for duplicate names (excluding current if editing)
            if self._check_participant_name_exists(
                name, exclude_current=current_config.get(CONF_NAME) if current_config else None
            ):
                errors[CONF_NAME] = "name_exists"
            else:
                # Add or update participant in configuration
                if current_config:
                    return await self._update_participant(
                        current_config[CONF_NAME], create_battery_participant(user_input)
                    )
                else:
                    return await self._add_participant(name, create_battery_participant(user_input))

        return self.async_show_form(
            step_id="configure_battery",
            data_schema=get_battery_schema(current_config),
            errors=errors,
        )

    async def async_step_configure_grid(
        self, user_input: dict[str, Any] | None = None, current_config: dict[str, Any] | None = None
    ):
        """Configure grid participant."""
        errors: dict[str, str] = {}

        if user_input is not None:
            name = user_input[CONF_NAME]

            # Check for duplicate names (excluding current if editing)
            if self._check_participant_name_exists(
                name, exclude_current=current_config.get(CONF_NAME) if current_config else None
            ):
                errors[CONF_NAME] = "name_exists"
            else:
                # Add or update participant in configuration
                if current_config:
                    return await self._update_participant(
                        current_config[CONF_NAME], create_grid_participant(user_input)
                    )
                else:
                    return await self._add_participant(name, create_grid_participant(user_input))

        return self.async_show_form(
            step_id="configure_grid",
            data_schema=get_grid_schema(current_config),
            errors=errors,
        )

    async def async_step_configure_fixed_load(
        self, user_input: dict[str, Any] | None = None, current_config: dict[str, Any] | None = None
    ):
        """Configure fixed load participant."""
        errors: dict[str, str] = {}

        if user_input is not None:
            name = user_input[CONF_NAME]

            # Check for duplicate names (excluding current if editing)
            if self._check_participant_name_exists(
                name, exclude_current=current_config.get(CONF_NAME) if current_config else None
            ):
                errors[CONF_NAME] = "name_exists"
            else:
                # Add or update participant in configuration
                if current_config:
                    return await self._update_participant(
                        current_config[CONF_NAME], create_constant_load_participant(user_input)
                    )
                else:
                    return await self._add_participant(name, create_constant_load_participant(user_input))

        return self.async_show_form(
            step_id="configure_fixed_load",
            data_schema=get_constant_load_schema(current_config),
            errors=errors,
        )

    async def async_step_configure_forecast_load(
        self, user_input: dict[str, Any] | None = None, current_config: dict[str, Any] | None = None
    ):
        """Configure forecast load participant."""
        errors: dict[str, str] = {}

        if user_input is not None:
            name = user_input[CONF_NAME]

            # Check for duplicate names (excluding current if editing)
            if self._check_participant_name_exists(
                name, exclude_current=current_config.get(CONF_NAME) if current_config else None
            ):
                errors[CONF_NAME] = "name_exists"
            else:
                # Add or update participant in configuration
                if current_config:
                    return await self._update_participant(
                        current_config[CONF_NAME], create_forecast_load_participant(user_input)
                    )
                else:
                    return await self._add_participant(name, create_forecast_load_participant(user_input))

        return self.async_show_form(
            step_id="configure_forecast_load",
            data_schema=get_forecast_load_schema(current_config),
            errors=errors,
        )

    async def async_step_configure_generator(
        self, user_input: dict[str, Any] | None = None, current_config: dict[str, Any] | None = None
    ):
        """Configure generator participant."""
        errors: dict[str, str] = {}

        if user_input is not None:
            name = user_input[CONF_NAME]

            # Check for duplicate names (excluding current if editing)
            if self._check_participant_name_exists(
                name, exclude_current=current_config.get(CONF_NAME) if current_config else None
            ):
                errors[CONF_NAME] = "name_exists"
            else:
                # Add or update participant in configuration
                if current_config:
                    return await self._update_participant(
                        current_config[CONF_NAME], create_generator_participant(user_input)
                    )
                else:
                    return await self._add_participant(name, create_generator_participant(user_input))

        return self.async_show_form(
            step_id="configure_generator",
            data_schema=get_generator_schema(current_config),
            errors=errors,
        )

    async def async_step_configure_net(
        self, user_input: dict[str, Any] | None = None, current_config: dict[str, Any] | None = None
    ):
        """Configure net participant."""
        errors: dict[str, str] = {}

        if user_input is not None:
            name = user_input[CONF_NAME]

            # Check for duplicate names (excluding current if editing)
            if self._check_participant_name_exists(
                name, exclude_current=current_config.get(CONF_NAME) if current_config else None
            ):
                errors[CONF_NAME] = "name_exists"
            else:
                # Add or update participant in configuration
                if current_config:
                    return await self._update_participant(current_config[CONF_NAME], create_net_participant(user_input))
                else:
                    return await self._add_participant(name, create_net_participant(user_input))

        return self.async_show_form(
            step_id="configure_net",
            data_schema=get_net_schema(current_config),
            errors=errors,
        )

    async def async_step_configure_connection(
        self, user_input: dict[str, Any] | None = None, current_config: dict[str, Any] | None = None
    ):
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

            # Check for duplicate names (excluding current if editing)
            if self._check_participant_name_exists(
                name, exclude_current=current_config.get(CONF_NAME) if current_config else None
            ):
                errors[CONF_NAME] = "name_exists"

            # Validate connection configuration
            connection_errors = validate_connection_config(user_input)
            errors.update(connection_errors)

            if not errors:
                # Add or update participant in configuration
                if current_config:
                    return await self._update_participant(
                        current_config[CONF_NAME], create_connection_participant(user_input)
                    )
                else:
                    return await self._add_participant(name, create_connection_participant(user_input))

        return self.async_show_form(
            step_id="configure_connection",
            data_schema=get_connection_schema(device_participants, current_config),
            errors=errors,
        )

    async def async_step_edit_participant(self, user_input: dict[str, Any] | None = None):
        """Edit an existing participant."""
        participants = self.config_entry.data.get("participants", {})

        if not participants:
            return self.async_abort(reason="no_participants")

        if user_input is not None:
            participant_name = user_input["participant"]

            # Route to specific edit step based on participant type
            participant_config = participants[participant_name]
            participant_type = participant_config.get("type")

            if participant_type == ELEMENT_TYPE_BATTERY:
                return await self.async_step_edit_battery(participant_name, participant_config)
            elif participant_type == ELEMENT_TYPE_GRID:
                return await self.async_step_edit_grid(participant_name, participant_config)
            elif participant_type in [ELEMENT_TYPE_LOAD_FIXED, ELEMENT_TYPE_LOAD_FORECAST]:
                return await self.async_step_edit_load(participant_name, participant_config)
            elif participant_type == ELEMENT_TYPE_GENERATOR:
                return await self.async_step_edit_generator(participant_name, participant_config)
            elif participant_type == ELEMENT_TYPE_NET:
                return await self.async_step_edit_net(participant_name, participant_config)
            elif participant_type == ELEMENT_TYPE_CONNECTION:
                return await self.async_step_edit_connection(participant_name, participant_config)

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

    async def async_step_edit_battery(
        self, participant_name: str, participant_config: dict[str, Any], user_input: dict[str, Any] | None = None
    ):
        """Edit battery participant."""
        # Use the configure function with current config for editing
        return await self.async_step_configure_battery(user_input, participant_config)

    async def async_step_edit_grid(
        self, participant_name: str, participant_config: dict[str, Any], user_input: dict[str, Any] | None = None
    ):
        """Edit grid participant."""
        # Use the configure function with current config for editing
        return await self.async_step_configure_grid(user_input, participant_config)

    async def async_step_edit_load(
        self, participant_name: str, participant_config: dict[str, Any], user_input: dict[str, Any] | None = None
    ):
        """Edit load participant."""
        # Use the appropriate configure function with current config for editing
        element_type = participant_config.get("type")
        if element_type == ELEMENT_TYPE_LOAD_FIXED:
            return await self.async_step_configure_fixed_load(user_input, participant_config)
        else:
            return await self.async_step_configure_forecast_load(user_input, participant_config)

    async def async_step_edit_generator(
        self, participant_name: str, participant_config: dict[str, Any], user_input: dict[str, Any] | None = None
    ):
        """Edit generator participant."""
        # Use the configure function with current config for editing
        return await self.async_step_configure_generator(user_input, participant_config)

    async def async_step_edit_net(
        self, participant_name: str, participant_config: dict[str, Any], user_input: dict[str, Any] | None = None
    ):
        """Edit net participant."""
        # Use the configure function with current config for editing
        return await self.async_step_configure_net(user_input, participant_config)

    async def async_step_edit_connection(
        self, participant_name: str, participant_config: dict[str, Any], user_input: dict[str, Any] | None = None
    ):
        """Edit connection participant."""
        # Use the configure function with current config for editing
        return await self.async_step_configure_connection(user_input, participant_config)

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
