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
    ATTR_POWER,
    DOMAIN,
    ELEMENT_TYPE_BATTERY,
    ELEMENT_TYPE_GRID,
    ELEMENT_TYPE_GENERATOR,
    ELEMENT_TYPE_LOAD,
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
        for element_name, element_config in participants.items():
            element_type = element_config["type"]
            element_params = element_config.copy()
            element_params.pop("type", None)  # Remove type key as it's not a constructor parameter

            _LOGGER.debug("Adding element: %s (%s)", element_name, element_type)

            try:
                # Handle battery entities - use current charge from sensor
                if element_type == ELEMENT_TYPE_BATTERY:
                    if CONF_CURRENT_CHARGE_SENSOR in element_params:
                        current_charge_sensor = element_params[CONF_CURRENT_CHARGE_SENSOR]
                        current_charge = await self._get_sensor_value(current_charge_sensor)
                        if current_charge is not None:
                            # Update initial charge percentage from sensor
                            element_params[CONF_INITIAL_CHARGE_PERCENTAGE] = current_charge
                        # Remove the sensor from params as it's not a Battery constructor parameter
                        element_params.pop(CONF_CURRENT_CHARGE_SENSOR, None)

                # Handle grid entities - need price arrays
                if element_type == ELEMENT_TYPE_GRID:
                    # Handle pricing from sensors or constants
                    import_price_array = None
                    export_price_array = None

                    # Check for sensor-based pricing
                    if CONF_PRICE_IMPORT_SENSOR in element_params:
                        import_price_data = await self._get_sensor_forecast(element_params[CONF_PRICE_IMPORT_SENSOR])
                        if import_price_data:
                            import_price_array = import_price_data
                        # Remove sensor from params as it's not a Grid constructor parameter
                        element_params.pop(CONF_PRICE_IMPORT_SENSOR, None)

                    if CONF_PRICE_EXPORT_SENSOR in element_params:
                        export_price_data = await self._get_sensor_forecast(element_params[CONF_PRICE_EXPORT_SENSOR])
                        if export_price_data:
                            export_price_array = export_price_data
                        # Remove sensor from params as it's not a Grid constructor parameter
                        element_params.pop(CONF_PRICE_EXPORT_SENSOR, None)

                    # Check for constant pricing
                    if CONF_PRICE_IMPORT in element_params:
                        constant_import = element_params.pop(CONF_PRICE_IMPORT)
                        if import_price_array is None:  # Only use constant if no sensor data
                            import_price_array = [constant_import] * DEFAULT_N_PERIODS

                    if CONF_PRICE_EXPORT in element_params:
                        constant_export = element_params.pop(CONF_PRICE_EXPORT)
                        if export_price_array is None:  # Only use constant if no sensor data
                            export_price_array = [constant_export] * DEFAULT_N_PERIODS

                    # Provide default price arrays if nothing is set
                    if import_price_array is None:
                        import_price_array = [0.0] * DEFAULT_N_PERIODS
                    if export_price_array is None:
                        export_price_array = [0.0] * DEFAULT_N_PERIODS

                    # Set the price arrays for grid constructor
                    element_params["price_import"] = import_price_array
                    element_params["price_export"] = export_price_array

                self.network.add(element_type, element_name, **element_params)
            except Exception as ex:
                _LOGGER.error("Failed to add element %s: %s", element_name, ex)
                raise

    async def _collect_sensor_data(self) -> None:
        """Collect data from Home Assistant sensors and update network entities."""
        if not self.network:
            return

        # Get participants from hub configuration
        participants = self.config.get("participants", {})

        for element_name, element_config in participants.items():
            element_type = element_config["type"]

            # Update dynamic sensor data for all entity types with forecast/price sensors
            if element_type == ELEMENT_TYPE_GRID:
                # Update price data from sensors for grid entities
                if CONF_PRICE_IMPORT_SENSOR in element_config:
                    price_import_data = await self._get_sensor_forecast(element_config[CONF_PRICE_IMPORT_SENSOR])
                    if price_import_data:
                        element = self.network.elements[element_name]
                        element.price_production = price_import_data

                if CONF_PRICE_EXPORT_SENSOR in element_config:
                    price_export_data = await self._get_sensor_forecast(element_config[CONF_PRICE_EXPORT_SENSOR])
                    if price_export_data:
                        element = self.network.elements[element_name]
                        element.price_consumption = price_export_data

            elif element_type in [ELEMENT_TYPE_GENERATOR, ELEMENT_TYPE_LOAD]:
                # Update forecast data from sensors
                forecast_sensors = element_config.get(CONF_FORECAST_SENSORS, [])
                if forecast_sensors:
                    # Get forecast data from all sensors
                    forecast_data = [
                        sensor_data
                        for sensor in forecast_sensors
                        if (sensor_data := await self._get_sensor_forecast(sensor))
                    ]

                    if forecast_data:
                        # Use the first sensor's data
                        element = self.network.elements[element_name]
                        element.forecast = forecast_data[0]

            # Update data from configured sensors
            if CONF_SENSORS in element_config:
                for sensor_config in element_config[CONF_SENSORS]:
                    sensor_data = await self._get_sensor_data(sensor_config)
                    if sensor_data:
                        # Process sensor data based on element type and sensor configuration
                        await self._process_sensor_data(element_name, element_type, sensor_config, sensor_data)

    async def _get_sensor_forecast(self, element_id: str) -> list[float] | None:
        """Get forecast data from a sensor entity."""
        state = self.hass.states.get(element_id)
        if not state:
            _LOGGER.warning("Sensor %s not found", element_id)
            return None

        # Try to get forecast from attributes first
        forecast_attr = state.attributes.get("forecast")
        if forecast_attr and isinstance(forecast_attr, list):
            try:
                return [float(x) for x in forecast_attr[:DEFAULT_N_PERIODS]]
            except (ValueError, TypeError) as ex:
                _LOGGER.error("Invalid forecast data in sensor %s: %s", element_id, ex)

        # Fallback: repeat current state value
        return self._get_repeated_value(state, element_id)

    async def _get_sensor_data(self, sensor_config: dict[str, Any]) -> Any | None:
        """Get data from a sensor entity."""
        element_id = sensor_config[CONF_SENSOR_ENTITY_ID]
        attribute = sensor_config.get(CONF_SENSOR_ATTRIBUTE)

        state = self.hass.states.get(element_id)
        if not state:
            _LOGGER.warning("Sensor %s not found", element_id)
            return None

        if attribute:
            return state.attributes.get(attribute)
        else:
            return state.state

    def _get_repeated_value(self, state, element_id: str) -> list[float] | None:
        """Get repeated current state value for forecast periods."""
        try:
            current_value = float(state.state)
            return [current_value] * DEFAULT_N_PERIODS
        except (ValueError, TypeError) as ex:
            _LOGGER.error("Invalid state value in sensor %s: %s", element_id, ex)
            return None

    async def _get_sensor_value(self, element_id: str) -> float | None:
        """Get current numeric value from a sensor entity."""
        state = self.hass.states.get(element_id)
        if not state:
            _LOGGER.warning("Sensor %s not found", element_id)
            return None

        try:
            return float(state.state)
        except (ValueError, TypeError) as ex:
            _LOGGER.error("Invalid numeric value in sensor %s: %s", element_id, ex)
            return None

    async def _process_sensor_data(
        self, element_name: str, element_type: str, sensor_config: dict[str, Any], sensor_data: Any
    ) -> None:
        """Process sensor data and update entity accordingly."""
        # This method can be extended to handle specific sensor data processing
        # For now, we'll log the data for debugging
        _LOGGER.debug("Received sensor data for entity %s (%s): %s", element_name, element_type, sensor_data)

    def _run_optimization(self) -> float:
        """Run the optimization process."""
        if not self.network:
            raise RuntimeError("Network not initialized")

        _LOGGER.debug("Running optimization for network with %d elements", len(self.network.elements))

        try:
            return self.network.optimize()
        except Exception as ex:
            _LOGGER.error("Optimization failed: %s", ex)
            raise

    def get_element_data(self, element_name: str) -> dict[str, Any] | None:
        """Get data for a specific element directly from the network."""
        if not self.network or element_name not in self.network.elements:
            return None

        from pulp import value

        element = self.network.elements[element_name]
        element_data = {}

        # Helper to extract values safely
        def extract_values(variables):
            result = []
            for var in variables:
                val = value(var)
                result.append(float(val) if isinstance(val, (int, float)) else 0.0)
            return result

        # Get power values (net power, can be positive or negative)
        if hasattr(element, "power") and element.power is not None:
            # Connections have a single power attribute (net flow)
            element_data[ATTR_POWER] = extract_values(element.power)
        elif hasattr(element, "power_consumption") and element.power_consumption is not None:
            # Elements like batteries have separate consumption and production
            consumption = extract_values(element.power_consumption)
            production = (
                extract_values(element.power_production)
                if hasattr(element, "power_production") and element.power_production is not None
                else [0.0] * len(consumption)
            )
            # Net power = production - consumption (positive = net production, negative = net consumption)
            element_data[ATTR_POWER] = [p - c for p, c in zip(production, consumption)]

        if hasattr(element, "energy") and element.energy is not None:
            element_data["energy"] = extract_values(element.energy)

        return element_data if element_data else None

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
