"""Constants for the Home Assistant Energy Optimization integration."""

# Integration domain
DOMAIN = "haeo"

# Configuration keys
CONF_NAME = "name"
CONF_SOURCE = "source"
CONF_TARGET = "target"
CONF_MIN_POWER = "min_power"
CONF_MAX_POWER = "max_power"
CONF_ELEMENT_TYPE = "type"
CONF_PARTICIPANTS = "participants"

# Component types
ELEMENT_TYPE_BATTERY = "battery"
ELEMENT_TYPE_CONNECTION = "connection"
ELEMENT_TYPE_GRID = "grid"
ELEMENT_TYPE_LOAD_CONSTANT = "load_constant"
ELEMENT_TYPE_LOAD_FORECAST = "load_forecast"
ELEMENT_TYPE_GENERATOR = "generator"
ELEMENT_TYPE_NET = "net"

ELEMENT_TYPES = [
    ELEMENT_TYPE_BATTERY,
    ELEMENT_TYPE_CONNECTION,
    ELEMENT_TYPE_GRID,
    ELEMENT_TYPE_LOAD_CONSTANT,
    ELEMENT_TYPE_LOAD_FORECAST,
    ELEMENT_TYPE_GENERATOR,
    ELEMENT_TYPE_NET,
]

# Battery configuration keys
CONF_CAPACITY = "capacity"
CONF_CURRENT_CHARGE_SENSOR = "current_charge_sensor"
CONF_MIN_CHARGE_PERCENTAGE = "min_charge_percentage"
CONF_MAX_CHARGE_PERCENTAGE = "max_charge_percentage"
CONF_MAX_CHARGE_POWER = "max_charge_power"
CONF_MAX_DISCHARGE_POWER = "max_discharge_power"
CONF_EFFICIENCY = "efficiency"
CONF_CHARGE_COST = "charge_cost"
CONF_DISCHARGE_COST = "discharge_cost"

# Grid configuration keys
CONF_IMPORT_LIMIT = "import_limit"
CONF_EXPORT_LIMIT = "export_limit"
CONF_PRICE_IMPORT_SENSOR = "price_import_sensor"
CONF_PRICE_EXPORT_SENSOR = "price_export_sensor"
CONF_PRICE_IMPORT_FORECAST_SENSORS = "price_import_forecast_sensor"
CONF_PRICE_EXPORT_FORECAST_SENSORS = "price_export_forecast_sensor"

# Load configuration keys
CONF_LOAD_TYPE = "load_type"
CONF_POWER = "power"
CONF_ENERGY = "energy"
CONF_FORECAST = "forecast"
CONF_FORECAST_SENSORS = "forecast_sensors"

# Load types
LOAD_TYPE_FIXED = "fixed"
LOAD_TYPE_VARIABLE = "variable"
LOAD_TYPE_FORECAST = "forecast"

# Generator configuration keys
CONF_CURTAILMENT = "curtailment"
CONF_PRICE_PRODUCTION = "price_production"
CONF_PRICE_CONSUMPTION = "price_consumption"
CONF_POWER_SENSOR = "power_sensor"

# Sensor configuration keys
CONF_SENSORS = "sensors"
CONF_SENSOR_ENTITY_ID = "entity_id"
CONF_SENSOR_ATTRIBUTE = "attribute"

# Default values
DEFAULT_PERIOD = 300  # 5 minutes in seconds
DEFAULT_N_PERIODS = 576  # 48 hours in 5 minute steps

# Update intervals
DEFAULT_UPDATE_INTERVAL = 300  # 5 minutes in seconds

# Optimization statuses
OPTIMIZATION_STATUS_SUCCESS = "success"
OPTIMIZATION_STATUS_FAILED = "failed"
OPTIMIZATION_STATUS_PENDING = "pending"

# Sensor units
UNIT_CURRENCY = "USD"  # Could be made configurable

# Entity attribute keys
ATTR_ENERGY = "energy"
ATTR_POWER = "power"


def get_element_type_name(element_type: str) -> str:
    """Get translated element type name."""
    import json
    import os
    import logging

    _logger = logging.getLogger(__name__)

    # Map element types to translation keys
    device_type_map = {
        ELEMENT_TYPE_BATTERY: "entity.device.battery",
        ELEMENT_TYPE_GRID: "entity.device.grid_connection",
        ELEMENT_TYPE_LOAD_CONSTANT: "entity.device.constant_load",
        ELEMENT_TYPE_LOAD_FORECAST: "entity.device.forecast_load",
        ELEMENT_TYPE_GENERATOR: "entity.device.generator",
        ELEMENT_TYPE_NET: "entity.device.network_node",
        ELEMENT_TYPE_CONNECTION: "entity.device.connection",
    }

    try:
        # Load translations from en.json file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        translations_file = os.path.join(current_dir, "translations", "en.json")

        with open(translations_file, "r", encoding="utf-8") as f:
            translations_data = json.load(f)

        translation_key = device_type_map.get(element_type)

        if not translation_key:
            raise ValueError(f"Unknown element type: {element_type}")

        # Parse the translation key path (e.g., "entity.device.battery")
        key_parts = translation_key.split(".")
        value = translations_data
        for part in key_parts:
            if part not in value:
                raise KeyError(f"Translation key not found: {translation_key}")
            value = value[part]

        if not isinstance(value, str):
            raise TypeError(f"Translation value is not a string for key: {translation_key}")

        return value

    except (json.JSONDecodeError, FileNotFoundError, KeyError, TypeError, ValueError) as ex:
        _logger.error("Failed to get element type name for %s: %s", element_type, ex)
        # Use a generic fallback for error cases
        return "Device"
