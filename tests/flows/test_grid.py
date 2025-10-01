"""Test data and validation for grid flow configuration."""

from custom_components.haeo.const import (
    CONF_IMPORT_LIMIT,
    CONF_EXPORT_LIMIT,
    CONF_PRICE_IMPORT_SENSOR,
    CONF_PRICE_EXPORT_SENSOR,
)

# Test data for grid flow
VALID_DATA = [
    {
        "description": "Basic grid configuration",
        "config": {
            CONF_IMPORT_LIMIT: 5000,
            CONF_EXPORT_LIMIT: 3000,
        },
    },
    {
        "description": "Grid with sensor-based pricing",
        "config": {
            CONF_IMPORT_LIMIT: 8000,
            CONF_EXPORT_LIMIT: 5000,
            CONF_PRICE_IMPORT_SENSOR: "sensor.import_price",
            CONF_PRICE_EXPORT_SENSOR: "sensor.export_price",
        },
    },
]

INVALID_DATA = [
    {
        "description": "Empty name should fail validation",
        "config": {CONF_IMPORT_LIMIT: 5000},
        "error": "cannot be empty",
    },
    {
        "description": "Negative import limit should fail validation",
        "config": {CONF_IMPORT_LIMIT: -1000},
        "error": "too small",
    },
]
