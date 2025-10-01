"""Constants for the Home Assistant Energy Optimization integration."""

# Integration domain
DOMAIN = "haeo"

# Configuration keys
CONF_ELEMENTS = "elements"
CONF_ELEMENT_TYPE = "element_type"
CONF_ELEMENT_CONFIG = "config"
CONF_NAME = "name"
CONF_SOURCE = "source"
CONF_TARGET = "target"
CONF_MIN_POWER = "min_power"
CONF_MAX_POWER = "max_power"

# Component types
ELEMENT_TYPE_BATTERY = "battery"
ELEMENT_TYPE_CONNECTION = "connection"
ELEMENT_TYPE_GRID = "grid"
ELEMENT_TYPE_LOAD = "load"
ELEMENT_TYPE_GENERATOR = "generator"
ELEMENT_TYPE_NET = "net"

ELEMENT_TYPES = [
    ELEMENT_TYPE_BATTERY,
    ELEMENT_TYPE_CONNECTION,
    ELEMENT_TYPE_GRID,
    ELEMENT_TYPE_LOAD,
    ELEMENT_TYPE_GENERATOR,
    ELEMENT_TYPE_NET,
]

# Battery configuration keys
CONF_CAPACITY = "capacity"
CONF_INITIAL_CHARGE_PERCENTAGE = "initial_charge_percentage"
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
CONF_PRICE_IMPORT = "price_import"
CONF_PRICE_EXPORT = "price_export"
CONF_PRICE_IMPORT_SENSOR = "price_import_sensor"
CONF_PRICE_EXPORT_SENSOR = "price_export_sensor"

# Load configuration keys
CONF_LOAD_TYPE = "load_type"
CONF_POWER = "power"
CONF_ENERGY = "energy"
CONF_FORECAST = "forecast"
CONF_FORECAST_SENSOR = "forecast_sensor"
CONF_FORECAST_SENSORS = "forecast_sensors"

# Load types
LOAD_TYPE_FIXED = "fixed"
LOAD_TYPE_VARIABLE = "variable"
LOAD_TYPE_FORECAST = "forecast"

# Generator configuration keys
CONF_CURTAILMENT = "curtailment"
CONF_PRICE_PRODUCTION = "price_production"
CONF_PRICE_CONSUMPTION = "price_consumption"

# Sensor configuration keys
CONF_SENSORS = "sensors"
CONF_SENSOR_ENTITY_ID = "entity_id"
CONF_SENSOR_ATTRIBUTE = "attribute"

# Default values
DEFAULT_PERIOD = 3600  # 1 hour in seconds
DEFAULT_N_PERIODS = 24  # 24 hours

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
