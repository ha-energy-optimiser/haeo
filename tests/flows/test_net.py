"""Test data and validation for net flow configuration."""

from custom_components.haeo.const import CONF_NAME

# Test data for net flow
VALID_DATA = [
    {
        "description": "Basic net configuration",
        "config": {CONF_NAME: "Test Net"},
    },
]

INVALID_DATA = [
    {
        "description": "Empty name should fail validation",
        "config": {CONF_NAME: ""},
        "error": "cannot be empty",
    },
]
