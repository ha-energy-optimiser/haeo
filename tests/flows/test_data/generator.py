"""Test data and validation for generator flow configuration."""

from custom_components.haeo.const import (
    CONF_NAME,
    CONF_POWER,
    CONF_CURTAILMENT,
    CONF_FORECAST,
    CONF_PRICE_PRODUCTION,
)

# Test data for generator flow
VALID_DATA = [
    {
        "description": "Basic generator configuration",
        "config": {
            CONF_NAME: "Test Generator",
            CONF_POWER: "sensor.generator_power",
            CONF_CURTAILMENT: False,
            CONF_FORECAST: ["sensor.generator_forecast"],
        },
    },
    {
        "description": "Curtailable generator configuration",
        "config": {
            CONF_NAME: "Curtailable Generator",
            CONF_POWER: "sensor.generator_power",
            CONF_CURTAILMENT: True,
            CONF_FORECAST: ["sensor.generator_forecast"],
            CONF_PRICE_PRODUCTION: 0.03,
        },
    },
    {
        "description": "Generator with forecast sensors",
        "config": {
            CONF_NAME: "Solar Generator",
            CONF_POWER: "sensor.generator_power",
            CONF_CURTAILMENT: True,
            CONF_FORECAST: ["sensor.solar_forecast"],
            CONF_PRICE_PRODUCTION: 0.04,
        },
    },
]

INVALID_DATA = [
    {
        "description": "Empty name should fail validation",
        "config": {CONF_NAME: "", CONF_POWER: "sensor.test"},
        "error": "cannot be empty",
    },
    {
        "description": "Invalid curtailment value should fail validation",
        "config": {CONF_NAME: "Test", CONF_POWER: "sensor.test", CONF_CURTAILMENT: "invalid"},
        "error": "expected bool",
    },
]
