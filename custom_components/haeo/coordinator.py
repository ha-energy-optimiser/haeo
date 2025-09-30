"""Data update coordinator for the Home Assistant Energy Optimization integration."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    ENTITY_TYPE_BATTERY,
    ENTITY_TYPE_GRID,
    ENTITY_TYPE_GENERATOR,
    ENTITY_TYPE_LOAD,
    CONF_SENSORS,
    CONF_SENSOR_ENTITY_ID,
    CONF_SENSOR_ATTRIBUTE,
    CONF_CURRENT_CHARGE_SENSOR,
    CONF_INITIAL_CHARGE_PERCENTAGE,
    CONF_PRICE_IMPORT,
    CONF_PRICE_EXPORT,
    CONF_PRICE_IMPORT_SENSOR,
    CONF_PRICE_EXPORT_SENSOR,
    CONF_FORECAST_SENSORS,
    ATTR_POWER_CONSUMPTION,
    ATTR_POWER_PRODUCTION,
    DEFAULT_PERIOD,
    DEFAULT_N_PERIODS,
    DEFAULT_UPDATE_INTERVAL,
    OPTIMIZATION_STATUS_SUCCESS,
    OPTIMIZATION_STATUS_FAILED,
    OPTIMIZATION_STATUS_PENDING,
)
from .model import Network

_LOGGER = logging.getLogger(__name__)


class HaeoDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Data update coordinator for HAEO integration."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.hass = hass
        self.entry = entry
        self.config = entry.data
        self.network: Network | None = None
        self.optimization_result: dict[str, Any] | None = None
        self.optimization_status = OPTIMIZATION_STATUS_PENDING

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(seconds=DEFAULT_UPDATE_INTERVAL),
        )

    def get_future_timestamps(self) -> list[str]:
        """Get list of ISO timestamps for each optimization period."""
        if not self.optimization_result:
            return []

        start_time = self.optimization_result["timestamp"]
        timestamps = []

        for i in range(DEFAULT_N_PERIODS):
            period_time = start_time + timedelta(seconds=DEFAULT_PERIOD * i)
            timestamps.append(period_time.isoformat())

        return timestamps

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data from Home Assistant entities and run optimization."""
        try:
            # Rebuild network from configuration
            await self._build_network()

            # Collect sensor data
            await self._collect_sensor_data()

            # Run optimization
            cost = await self.hass.async_add_executor_job(self._run_optimization)

            self.optimization_result = {
                "cost": cost,
                "timestamp": dt_util.utcnow(),
            }
            self.optimization_status = OPTIMIZATION_STATUS_SUCCESS

            _LOGGER.debug("Optimization completed successfully with cost: %s", cost)

            return self.optimization_result

        except Exception as ex:
            self.optimization_status = OPTIMIZATION_STATUS_FAILED
            _LOGGER.error("Failed to update HAEO data: %s", ex)
            raise UpdateFailed(f"Error updating HAEO data: {ex}") from ex

    async def _build_network(self) -> None:
        """Build the network from configuration."""
        self.network = Network(
            name="haeo_network",
            period=DEFAULT_PERIOD,
            n_periods=DEFAULT_N_PERIODS,
        )

        # Get participants from hub configuration
        participants = self.config.get("participants", {})

        if not participants:
            _LOGGER.warning("No participants configured for hub")
            return

        # Add entities from participants
        for entity_name, entity_config in participants.items():
            entity_type = entity_config["type"]
            entity_params = entity_config.copy()
            entity_params.pop("type", None)  # Remove type key as it's not a constructor parameter

            _LOGGER.debug("Adding entity: %s (%s)", entity_name, entity_type)

            try:
                # Handle battery entities - use current charge from sensor
                if entity_type == ENTITY_TYPE_BATTERY:
                    if CONF_CURRENT_CHARGE_SENSOR in entity_params:
                        current_charge_sensor = entity_params[CONF_CURRENT_CHARGE_SENSOR]
                        current_charge = await self._get_sensor_value(current_charge_sensor)
                        if current_charge is not None:
                            # Update initial charge percentage from sensor
                            entity_params[CONF_INITIAL_CHARGE_PERCENTAGE] = current_charge
                        # Remove the sensor from params as it's not a Battery constructor parameter
                        entity_params.pop(CONF_CURRENT_CHARGE_SENSOR, None)

                # Handle grid entities - need price arrays
                if entity_type == ENTITY_TYPE_GRID:
                    # Handle pricing from sensors or constants
                    import_price_array = None
                    export_price_array = None

                    # Check for sensor-based pricing
                    if CONF_PRICE_IMPORT_SENSOR in entity_params:
                        import_price_data = await self._get_sensor_forecast(entity_params[CONF_PRICE_IMPORT_SENSOR])
                        if import_price_data:
                            import_price_array = import_price_data
                        # Remove sensor from params as it's not a Grid constructor parameter
                        entity_params.pop(CONF_PRICE_IMPORT_SENSOR, None)

                    if CONF_PRICE_EXPORT_SENSOR in entity_params:
                        export_price_data = await self._get_sensor_forecast(entity_params[CONF_PRICE_EXPORT_SENSOR])
                        if export_price_data:
                            export_price_array = export_price_data
                        # Remove sensor from params as it's not a Grid constructor parameter
                        entity_params.pop(CONF_PRICE_EXPORT_SENSOR, None)

                    # Check for constant pricing
                    if CONF_PRICE_IMPORT in entity_params:
                        constant_import = entity_params.pop(CONF_PRICE_IMPORT)
                        if import_price_array is None:  # Only use constant if no sensor data
                            import_price_array = [constant_import] * DEFAULT_N_PERIODS

                    if CONF_PRICE_EXPORT in entity_params:
                        constant_export = entity_params.pop(CONF_PRICE_EXPORT)
                        if export_price_array is None:  # Only use constant if no sensor data
                            export_price_array = [constant_export] * DEFAULT_N_PERIODS

                    # Provide default price arrays if nothing is set
                    if import_price_array is None:
                        import_price_array = [0.0] * DEFAULT_N_PERIODS
                    if export_price_array is None:
                        export_price_array = [0.0] * DEFAULT_N_PERIODS

                    # Set the price arrays for grid constructor
                    entity_params["price_import"] = import_price_array
                    entity_params["price_export"] = export_price_array

                self.network.add(entity_type, entity_name, **entity_params)
            except Exception as ex:
                _LOGGER.error("Failed to add entity %s: %s", entity_name, ex)
                raise

    async def _collect_sensor_data(self) -> None:
        """Collect data from Home Assistant sensors and update network entities."""
        if not self.network:
            return

        # Get participants from hub configuration
        participants = self.config.get("participants", {})

        for entity_name, entity_config in participants.items():
            entity_type = entity_config["type"]

            # Update dynamic sensor data for all entity types with forecast/price sensors
            if entity_type == ENTITY_TYPE_GRID:
                # Update price data from sensors for grid entities
                if CONF_PRICE_IMPORT_SENSOR in entity_config:
                    price_import_data = await self._get_sensor_forecast(entity_config[CONF_PRICE_IMPORT_SENSOR])
                    if price_import_data:
                        entity = self.network.entities[entity_name]
                        entity.price_production = price_import_data

                if CONF_PRICE_EXPORT_SENSOR in entity_config:
                    price_export_data = await self._get_sensor_forecast(entity_config[CONF_PRICE_EXPORT_SENSOR])
                    if price_export_data:
                        entity = self.network.entities[entity_name]
                        entity.price_consumption = price_export_data

            elif entity_type in [ENTITY_TYPE_GENERATOR, ENTITY_TYPE_LOAD]:
                # Update forecast data from sensors
                forecast_sensors = entity_config.get(CONF_FORECAST_SENSORS, [])
                if forecast_sensors:
                    # Get forecast data from all sensors
                    forecast_data = [
                        sensor_data
                        for sensor in forecast_sensors
                        if (sensor_data := await self._get_sensor_forecast(sensor))
                    ]

                    if forecast_data:
                        # Use the first sensor's data
                        entity = self.network.entities[entity_name]
                        entity.forecast = forecast_data[0]

            # Update data from configured sensors
            if CONF_SENSORS in entity_config:
                for sensor_config in entity_config[CONF_SENSORS]:
                    sensor_data = await self._get_sensor_data(sensor_config)
                    if sensor_data:
                        # Process sensor data based on entity type and sensor configuration
                        await self._process_sensor_data(entity_name, entity_type, sensor_config, sensor_data)

    async def _get_sensor_forecast(self, entity_id: str) -> list[float] | None:
        """Get forecast data from a sensor entity."""
        state = self.hass.states.get(entity_id)
        if not state:
            _LOGGER.warning("Sensor %s not found", entity_id)
            return None

        # Try to get forecast from attributes first
        forecast_attr = state.attributes.get("forecast")
        if forecast_attr and isinstance(forecast_attr, list):
            try:
                return [float(x) for x in forecast_attr[:DEFAULT_N_PERIODS]]
            except (ValueError, TypeError) as ex:
                _LOGGER.error("Invalid forecast data in sensor %s: %s", entity_id, ex)

        # Fallback: repeat current state value
        return self._get_repeated_value(state, entity_id)

    async def _get_sensor_data(self, sensor_config: dict[str, Any]) -> Any | None:
        """Get data from a sensor entity."""
        entity_id = sensor_config[CONF_SENSOR_ENTITY_ID]
        attribute = sensor_config.get(CONF_SENSOR_ATTRIBUTE)

        state = self.hass.states.get(entity_id)
        if not state:
            _LOGGER.warning("Sensor %s not found", entity_id)
            return None

        if attribute:
            return state.attributes.get(attribute)
        else:
            return state.state

    def _get_repeated_value(self, state, entity_id: str) -> list[float] | None:
        """Get repeated current state value for forecast periods."""
        try:
            current_value = float(state.state)
            return [current_value] * DEFAULT_N_PERIODS
        except (ValueError, TypeError) as ex:
            _LOGGER.error("Invalid state value in sensor %s: %s", entity_id, ex)
            return None

    async def _get_sensor_value(self, entity_id: str) -> float | None:
        """Get current numeric value from a sensor entity."""
        state = self.hass.states.get(entity_id)
        if not state:
            _LOGGER.warning("Sensor %s not found", entity_id)
            return None

        try:
            return float(state.state)
        except (ValueError, TypeError) as ex:
            _LOGGER.error("Invalid numeric value in sensor %s: %s", entity_id, ex)
            return None

    async def _process_sensor_data(
        self, entity_name: str, entity_type: str, sensor_config: dict[str, Any], sensor_data: Any
    ) -> None:
        """Process sensor data and update entity accordingly."""
        # This method can be extended to handle specific sensor data processing
        # For now, we'll log the data for debugging
        _LOGGER.debug("Received sensor data for entity %s (%s): %s", entity_name, entity_type, sensor_data)

    def _run_optimization(self) -> float:
        """Run the optimization process."""
        if not self.network:
            raise RuntimeError("Network not initialized")

        _LOGGER.debug("Running optimization for network with %d entities", len(self.network.entities))

        try:
            return self.network.optimize()
        except Exception as ex:
            _LOGGER.error("Optimization failed: %s", ex)
            raise

    def get_entity_data(self, entity_name: str) -> dict[str, Any] | None:
        """Get data for a specific entity directly from the network."""
        if not self.network or entity_name not in self.network.entities:
            return None

        from pulp import value

        entity = self.network.entities[entity_name]
        entity_data = {}

        # Helper to extract values safely
        def extract_values(variables):
            result = []
            for var in variables:
                val = value(var)
                result.append(float(val) if isinstance(val, (int, float)) else 0.0)
            return result

        # Get power consumption/production/energy values
        if entity.power_consumption is not None:
            entity_data[ATTR_POWER_CONSUMPTION] = extract_values(entity.power_consumption)

        if entity.power_production is not None:
            entity_data[ATTR_POWER_PRODUCTION] = extract_values(entity.power_production)

        if entity.energy is not None:
            entity_data["energy"] = extract_values(entity.energy)

        return entity_data if entity_data else None

    def get_connection_data(self, source: str, target: str) -> list[float] | None:
        """Get data for a specific connection directly from the network."""
        if not self.network:
            return None

        connection_key = (source, target)
        if connection_key not in self.network.connections:
            return None

        from pulp import value

        connection = self.network.connections[connection_key]
        power_values = []
        for var in connection.power:
            val = value(var)
            if isinstance(val, (int, float)):
                power_values.append(float(val))
            else:
                power_values.append(0.0)
        return power_values

    @property
    def last_optimization_cost(self) -> float | None:
        """Get the last optimization cost."""
        if self.optimization_result:
            return self.optimization_result["cost"]
        return None

    @property
    def last_optimization_time(self) -> Any | None:
        """Get the last optimization timestamp."""
        if self.optimization_result:
            return self.optimization_result["timestamp"]
        return None
