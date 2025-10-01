"""Test data and validation for forecast load flow configuration."""

from custom_components.haeo.const import CONF_FORECAST_SENSORS

# Test data for load forecast flow
VALID_DATA = [
    {
        "description": "Variable load with forecast sensors",
        "config": {
            CONF_FORECAST_SENSORS: ["sensor.forecast1", "sensor.forecast2"],
        },
    },
]

INVALID_DATA = [
    {
        "description": "Empty config should fail validation",
        "config": {},
        "error": "cannot be empty",
    },
]
