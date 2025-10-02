"""Base classes and utilities for HAEO config flows."""

from __future__ import annotations

import logging
from dataclasses import fields
from typing import Any, get_type_hints

from ..types import ELEMENT_TYPES
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig, SelectSelectorMode
import voluptuous as vol

from ..const import CONF_SOURCE, CONF_TARGET


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
                    )
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
