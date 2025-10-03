"""Base classes and utilities for HAEO config flows."""

from __future__ import annotations

from dataclasses import fields
import logging
from typing import Any, get_type_hints

from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)
import voluptuous as vol

from ..const import (
    CONF_HORIZON_HOURS,
    CONF_PERIOD_MINUTES,
    CONF_SOURCE,
    CONF_TARGET,
    DEFAULT_HORIZON_HOURS,
    DEFAULT_PERIOD_MINUTES,
)
from ..types import ELEMENT_TYPES

_LOGGER = logging.getLogger(__name__)


def _get_participant_options(participants: dict[str, Any]) -> list[str]:
    """Get list of participant names for dropdown selection."""
    return list(participants.keys())


def _create_schema_from_config_class(config_class: type, participants: dict[str, Any] | None = None) -> vol.Schema:
    """Create a voluptuous schema from a config dataclass."""
    schema_dict = {}

    # Get type hints for the class
    type_hints = get_type_hints(config_class)

    for field_info in fields(config_class):
        field_name = field_info.name
        type_hints.get(field_name)
        field_metadata = field_info.metadata

        # Skip the element_type field as it's handled separately
        if field_name == "element_type":
            continue

        # Get the schema from metadata
        schema = field_metadata.get("schema")
        optional = field_metadata.get("optional", False)

        # Handle special cases for connections
        if config_class.__name__ == "ConnectionConfig" and field_name in [CONF_SOURCE, CONF_TARGET]:
            if participants is not None:
                participant_options = _get_participant_options(participants)
                schema = SelectSelector(
                    SelectSelectorConfig(
                        options=participant_options,
                        mode=SelectSelectorMode.DROPDOWN,
                    ),
                )
            else:
                # Fallback if no participants provided
                schema = vol.All(str, vol.Strip, vol.Length(min=1, msg=f"{field_name} cannot be empty"))

        # Handle fields with None schema (like element_name_field)
        if schema is None:
            schema = vol.All(str, vol.Strip, vol.Length(min=1, msg=f"{field_name} cannot be empty"))

        # Check if field has a default value (not default_factory)
        has_default = field_info.default is not None and field_info.default != vol.UNDEFINED

        # Handle optional fields or fields with defaults or default_factory
        if optional or has_default or field_info.default_factory is not None:
            # Use UNDEFINED for truly optional fields (not included in output if not provided)
            schema_dict[vol.Optional(field_name)] = schema
        else:
            schema_dict[vol.Required(field_name)] = schema

    return vol.Schema(schema_dict)


def get_schema(element_type: str, **kwargs) -> vol.Schema:
    """Get the appropriate schema for the given element type."""
    config_class = ELEMENT_TYPES.get(element_type)
    if config_class is None:
        raise ValueError(f"Unknown element type: {element_type}")

    participants = kwargs.get("participants")
    return _create_schema_from_config_class(config_class, participants)


def get_network_timing_schema(config_entry=None, include_name=False, name_required=True, current_name=None):
    """Get schema for network timing configuration.

    Args:
        config_entry: Config entry to get current values from
        include_name: Whether to include name field in schema
        name_required: Whether name field is required
        current_name: Current name value for editing

    Returns:
        Voluptuous schema for network timing configuration

    """
    schema_dict = {}

    # Add name field if requested
    if include_name:
        name_field = vol.Required("name") if name_required else vol.Optional("name", default=current_name or "")
        schema_dict[name_field] = vol.All(
            str,
            vol.Strip,
            vol.Length(min=1, msg="Name cannot be empty"),
            vol.Length(max=255, msg="Name cannot be longer than 255 characters"),
        )

    # Add horizon hours field
    current_horizon = DEFAULT_HORIZON_HOURS
    if config_entry:
        current_horizon = config_entry.data.get(CONF_HORIZON_HOURS, DEFAULT_HORIZON_HOURS)

    schema_dict[vol.Required(CONF_HORIZON_HOURS, default=current_horizon)] = NumberSelector(
        NumberSelectorConfig(min=1, max=168, step=1, mode="slider"),
    )

    # Add period minutes field
    current_period = DEFAULT_PERIOD_MINUTES
    if config_entry:
        current_period = config_entry.data.get(CONF_PERIOD_MINUTES, DEFAULT_PERIOD_MINUTES)

    schema_dict[vol.Required(CONF_PERIOD_MINUTES, default=current_period)] = NumberSelector(
        NumberSelectorConfig(min=1, max=60, step=1, mode="slider"),
    )

    return vol.Schema(schema_dict)


def validate_network_timing_input(user_input, hass=None, include_name=False, name_required=True):
    """Validate network timing input data.

    Args:
        user_input: User input dictionary
        hass: Home Assistant instance (needed for name validation)
        include_name: Whether name validation is needed
        name_required: Whether name is required

    Returns:
        Tuple of (errors dict, validated data dict)

    """
    errors = {}

    # Validate horizon hours
    horizon = user_input.get(CONF_HORIZON_HOURS, DEFAULT_HORIZON_HOURS)
    if not (1 <= horizon <= 168):
        errors[CONF_HORIZON_HOURS] = "invalid_horizon"

    # Validate period minutes
    period = user_input.get(CONF_PERIOD_MINUTES, DEFAULT_PERIOD_MINUTES)
    if not (1 <= period <= 60):
        errors[CONF_PERIOD_MINUTES] = "invalid_period"

    # Validate name if required
    if include_name and name_required:
        name = user_input.get("name", "").strip()
        if not name:
            errors["name"] = "name_required"
        elif len(name) > 255:
            errors["name"] = "name_too_long"
        elif hass:
            # Check for duplicate names
            for entry in hass.config_entries.async_entries("haeo"):
                if entry.title == name:
                    errors["name"] = "name_exists"
                    break

    validated_data = {
        CONF_HORIZON_HOURS: horizon,
        CONF_PERIOD_MINUTES: period,
    }

    if include_name:
        validated_data["name"] = name

    return errors, validated_data
