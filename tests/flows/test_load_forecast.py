"""Test data and validation for forecast load flow configuration."""

from custom_components.haeo.const import CONF_NAME, CONF_FORECAST_SENSORS

# Test data for load forecast flow
VALID_DATA = [
    {
        "description": "Variable load with forecast sensors",
        "config": {
            CONF_NAME: "Forecast Load",
            CONF_FORECAST_SENSORS: ["sensor.forecast1", "sensor.forecast2"],
        },
    },
]

INVALID_DATA = [
    {
        "description": "Empty name should fail validation",
        "config": {CONF_NAME: "", CONF_FORECAST_SENSORS: ["sensor.forecast1"]},
        "error": "cannot be empty",
    },
    {
        "description": "Invalid forecast sensors should fail validation",
        "config": {CONF_NAME: "Test Load", CONF_FORECAST_SENSORS: "not_a_list"},
        "error": "value should be a list",
    },
]
