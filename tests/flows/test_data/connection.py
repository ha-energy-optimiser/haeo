"""Test data and validation for connection flow configuration."""

from custom_components.haeo.const import CONF_MAX_POWER, CONF_MIN_POWER, CONF_NAME, CONF_SOURCE, CONF_TARGET

# Test data for connection flow
VALID_DATA = [
    {
        "description": "Basic connection configuration",
        "config": {
            CONF_NAME: "Battery to Grid",
            CONF_SOURCE: "Battery1",
            CONF_TARGET: "Grid1",
        },
    },
    {
        "description": "Connection with power limits",
        "config": {
            CONF_NAME: "Battery to Load",
            CONF_SOURCE: "Battery1",
            CONF_TARGET: "Load1",
            CONF_MIN_POWER: 0.0,
            CONF_MAX_POWER: 5000.0,
        },
    },
]

INVALID_DATA = [
    {
        "description": "Empty source should fail validation",
        "config": {CONF_NAME: "Test Connection", CONF_SOURCE: "", CONF_TARGET: "Grid1"},
        "error": "value must be one of",
    },
    {
        "description": "Empty target should fail validation",
        "config": {CONF_NAME: "Test Connection", CONF_SOURCE: "Battery1", CONF_TARGET: ""},
        "error": "value must be one of",
    },
]
