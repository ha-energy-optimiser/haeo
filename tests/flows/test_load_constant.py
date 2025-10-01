"""Test data and validation for constant load flow configuration."""

from custom_components.haeo.const import CONF_POWER

# Test data for load constant flow
VALID_DATA = [
    {
        "description": "Fixed load configuration",
        "config": {
            CONF_POWER: 1500,
        },
    },
]

INVALID_DATA = [
    {
        "description": "Empty config should fail validation",
        "config": {},
        "error": "cannot be empty",
    },
    {
        "description": "Negative power should fail validation",
        "config": {CONF_POWER: -500},
        "error": "too small",
    },
]
