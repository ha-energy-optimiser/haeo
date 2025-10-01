"""Base classes and utilities for HAEO config flows."""

from __future__ import annotations

import logging

import voluptuous as vol

from ..const import (
    ELEMENT_TYPE_BATTERY,
    ELEMENT_TYPE_CONNECTION,
    ELEMENT_TYPE_GENERATOR,
    ELEMENT_TYPE_GRID,
    ELEMENT_TYPE_LOAD_FIXED,
    ELEMENT_TYPE_LOAD_FORECAST,
    ELEMENT_TYPE_NET,
)

_LOGGER = logging.getLogger(__name__)

# Optimized validators using voluptuous built-ins
validate_element_name = vol.All(str, vol.Strip, vol.Length(min=1, msg="Name cannot be empty"))
validate_positive_number = vol.All(
    vol.Coerce(float), vol.Range(min=0, min_included=False, msg="Value must be positive")
)
validate_percentage = vol.All(vol.Coerce(float), vol.Range(min=0, max=100, msg="Value must be between 0 and 100"))
validate_efficiency = vol.All(
    vol.Coerce(float), vol.Range(min=0, max=1, min_included=False, msg="Efficiency must be between 0 and 1")
)
validate_non_negative_number = vol.All(vol.Coerce(float), vol.Range(min=0, msg="Value must be non-negative"))


def _get_schemas():
    """Get schema functions for all element types."""
    from . import battery, connection, generator, grid, load_constant, load_forecast, net

    return {
        ELEMENT_TYPE_BATTERY: battery.get_battery_schema,
        ELEMENT_TYPE_CONNECTION: connection.get_connection_schema,
        ELEMENT_TYPE_GENERATOR: generator.get_generator_schema,
        ELEMENT_TYPE_GRID: grid.get_grid_schema,
        ELEMENT_TYPE_LOAD_FIXED: load_constant.get_constant_load_schema,
        ELEMENT_TYPE_LOAD_FORECAST: load_forecast.get_forecast_load_schema,
        ELEMENT_TYPE_NET: net.get_net_schema,
    }


# Schema function mapping for dynamic schema selection
SCHEMA_FUNCTIONS = _get_schemas()


def get_schema(element_type: str, **kwargs):
    """Get the appropriate schema function for the given element type."""
    return SCHEMA_FUNCTIONS[element_type](**kwargs)
