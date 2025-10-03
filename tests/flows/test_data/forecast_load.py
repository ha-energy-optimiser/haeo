"""Test data and validation for forecast load flow configuration."""

from custom_components.haeo.const import CONF_NAME

# Test data for load forecast flow
VALID_DATA = [
    {
        "description": "Variable load with forecast sensors",
        "config": {
            CONF_NAME: "Forecast Load",
            "forecast": ["sensor.forecast1", "sensor.forecast2"],
        },
    },
]

INVALID_DATA = [
    {
        "description": "Empty name should fail validation",
        "config": {CONF_NAME: "", "forecast": ["sensor.forecast1"]},
        "error": "cannot be empty",
    },
    {
        "description": "Invalid forecast sensors should fail validation",
        "config": {CONF_NAME: "Test Load", "forecast": "not_a_list"},
        "error": "value should be a list",
    },
]
