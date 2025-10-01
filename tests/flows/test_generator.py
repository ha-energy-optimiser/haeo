"""Test data and validation for generator flow configuration."""

from custom_components.haeo.const import CONF_MAX_POWER, CONF_CURTAILMENT, CONF_FORECAST_SENSORS

# Test data for generator flow
VALID_DATA = [
    {
        "description": "Basic generator configuration",
        "config": {
            CONF_MAX_POWER: 3000,
            CONF_CURTAILMENT: False,
        },
    },
    {
        "description": "Curtailable generator configuration",
        "config": {
            CONF_MAX_POWER: 5000,
            CONF_CURTAILMENT: True,
        },
    },
    {
        "description": "Generator with forecast sensors",
        "config": {
            CONF_MAX_POWER: 4000,
            CONF_CURTAILMENT: True,
            CONF_FORECAST_SENSORS: ["sensor.solar_forecast"],
        },
    },
]

INVALID_DATA = [
    {
        "description": "Empty name should fail validation",
        "config": {CONF_MAX_POWER: 3000},
        "error": "cannot be empty",
    },
    {
        "description": "Negative max power should fail validation",
        "config": {CONF_MAX_POWER: -1000},
        "error": "too small",
    },
]
