"""Constants for the Home Assistant Energy Optimization integration."""

# Integration domain
DOMAIN = "haeo"

# Configuration keys
CONF_ENTITIES = "entities"
CONF_CONNECTIONS = "connections"
CONF_ENTITY_TYPE = "entity_type"
CONF_ENTITY_CONFIG = "config"
CONF_SOURCE = "source"
CONF_TARGET = "target"
CONF_MIN_POWER = "min_power"
CONF_MAX_POWER = "max_power"

# Entity types
ENTITY_TYPE_BATTERY = "battery"
ENTITY_TYPE_GRID = "grid"
ENTITY_TYPE_LOAD = "load"
ENTITY_TYPE_GENERATOR = "generator"
ENTITY_TYPE_NET = "net"

ENTITY_TYPES = [
    ENTITY_TYPE_BATTERY,
    ENTITY_TYPE_GRID,
    ENTITY_TYPE_LOAD,
    ENTITY_TYPE_GENERATOR,
    ENTITY_TYPE_NET,
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
CONF_FORECAST = "forecast"
CONF_FORECAST_SENSOR = "forecast_sensor"
CONF_FORECAST_SENSORS = "forecast_sensors"
CONF_FORECAST_AGGREGATION = "forecast_aggregation"
CONF_FORECAST_MULTIPLIER = "forecast_multiplier"

# Forecast aggregation modes
FORECAST_AGGREGATION_SUM = "sum"
FORECAST_AGGREGATION_REPLACE = "replace"
FORECAST_AGGREGATION_MODES = [FORECAST_AGGREGATION_SUM, FORECAST_AGGREGATION_REPLACE]

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
DEFAULT_EFFICIENCY = 0.99
DEFAULT_MIN_CHARGE_PERCENTAGE = 10
DEFAULT_MAX_CHARGE_PERCENTAGE = 90
DEFAULT_INITIAL_CHARGE_PERCENTAGE = 50
DEFAULT_CURTAILMENT = True

# Service names
SERVICE_OPTIMIZE = "optimize"
SERVICE_UPDATE_CONFIG = "update_config"

# Sensor types
SENSOR_TYPE_OPTIMIZATION_COST = "optimization_cost"
SENSOR_TYPE_OPTIMIZATION_STATUS = "optimization_status"
SENSOR_TYPE_ENTITY_POWER = "entity_power"
SENSOR_TYPE_ENTITY_ENERGY = "entity_energy"
SENSOR_TYPE_CONNECTION_POWER = "connection_power"

# Update intervals
DEFAULT_UPDATE_INTERVAL = 300  # 5 minutes in seconds
FAST_UPDATE_INTERVAL = 60  # 1 minute in seconds

# Optimization statuses
OPTIMIZATION_STATUS_SUCCESS = "success"
OPTIMIZATION_STATUS_FAILED = "failed"
OPTIMIZATION_STATUS_PENDING = "pending"

# Sensor device classes and units
DEVICE_CLASS_POWER = "power"
DEVICE_CLASS_ENERGY = "energy"
DEVICE_CLASS_MONETARY = "monetary"

UNIT_POWER = "W"
UNIT_ENERGY = "Wh"
UNIT_CURRENCY = "USD"  # Could be made configurable
