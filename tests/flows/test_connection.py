"""Test data and validation for connection flow configuration."""

from custom_components.haeo.const import (
    CONF_NAME,
    CONF_SOURCE,
    CONF_TARGET,
    CONF_MIN_POWER,
    CONF_MAX_POWER,
)

# Test data for connection flow
VALID_DATA = [
    {
        "description": "Basic connection configuration",
        "config": {
            CONF_NAME: "Battery to Grid",
            CONF_SOURCE: "battery_1",
            CONF_TARGET: "grid_1",
        },
    },
    {
        "description": "Connection with power limits",
        "config": {
            CONF_NAME: "Solar to Load",
            CONF_SOURCE: "solar_1",
            CONF_TARGET: "house_load",
            CONF_MIN_POWER: 0,
            CONF_MAX_POWER: 5000,
        },
    },
]

INVALID_DATA = [
    {
        "description": "Empty source should fail validation",
        "config": {CONF_NAME: "Test Connection", CONF_SOURCE: "", CONF_TARGET: "grid_1"},
        "error": "value must be one of",
    },
    {
        "description": "Empty target should fail validation",
        "config": {CONF_NAME: "Test Connection", CONF_SOURCE: "battery_1", CONF_TARGET: ""},
        "error": "value must be one of",
    },
]
