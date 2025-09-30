"""Sensor platform for Home Assistant Energy Optimization integration."""

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_ENTITIES,
    CONF_CONNECTIONS,
    DOMAIN,
    OPTIMIZATION_STATUS_SUCCESS,
    UNIT_CURRENCY,
)
from .coordinator import HaeoDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up HAEO sensor platform."""
    coordinator: HaeoDataUpdateCoordinator = config_entry.runtime_data

    entities: list[SensorEntity] = []

    # Add optimization status and cost sensors
    entities.append(HaeoOptimizationCostSensor(coordinator, config_entry))
    entities.append(HaeoOptimizationStatusSensor(coordinator, config_entry))

    # Add entity-specific sensors based on available data
    for entity_config in config_entry.data[CONF_ENTITIES]:
        entity_name = entity_config[CONF_NAME]

        # Create a helper function to check if we have optimization data for this entity
        def has_data_type(data_type: str) -> bool:
            if not coordinator.optimization_result:
                return True  # Assume we'll have it when optimization runs
            solution = coordinator.optimization_result.get("solution", {})
            return f"{entity_name}_{data_type}" in solution

        # Add power consumption sensor if entity has this capability
        if has_data_type("power_consumption"):
            entities.append(HaeoEntityPowerConsumptionSensor(coordinator, config_entry, entity_name))

        # Add power production sensor if entity has this capability
        if has_data_type("power_production"):
            entities.append(HaeoEntityPowerProductionSensor(coordinator, config_entry, entity_name))

        # Add net power sensor if entity has both consumption and production
        if has_data_type("power"):
            entities.append(HaeoEntityNetPowerSensor(coordinator, config_entry, entity_name))

        # Add energy sensor if entity has energy state (like batteries)
        if has_data_type("energy"):
            entities.append(HaeoEntityEnergySensor(coordinator, config_entry, entity_name))

    # Add connection sensors
    for connection_config in config_entry.data.get(CONF_CONNECTIONS, []):
        source = connection_config["source"]
        target = connection_config["target"]
        entities.append(HaeoConnectionPowerSensor(coordinator, config_entry, source, target))

    async_add_entities(entities)


class HaeoSensorBase(CoordinatorEntity[HaeoDataUpdateCoordinator], SensorEntity):
    """Base class for HAEO sensors."""

    coordinator: HaeoDataUpdateCoordinator

    def __init__(
        self,
        coordinator: HaeoDataUpdateCoordinator,
        config_entry: ConfigEntry,
        sensor_type: str,
        name_suffix: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.config_entry = config_entry
        self.sensor_type = sensor_type
        self._attr_name = f"HAEO {name_suffix}"
        self._attr_unique_id = f"{config_entry.entry_id}_{sensor_type}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.config_entry.entry_id)},
            name="HAEO Energy Optimizer",
            manufacturer="HAEO",
            model="Energy Optimization Network",
            sw_version="1.0.0",
        )


class HaeoOptimizationCostSensor(HaeoSensorBase):
    """Sensor for optimization cost."""

    def __init__(
        self,
        coordinator: HaeoDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry, "optimization_cost", "Optimization Cost")
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_native_unit_of_measurement = UNIT_CURRENCY
        self._attr_state_class = SensorStateClass.MEASUREMENT

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_native_value = self.coordinator.last_optimization_cost
        attrs = {}
        if self.coordinator.last_optimization_time:
            attrs["last_optimization"] = self.coordinator.last_optimization_time.isoformat()
        attrs["optimization_status"] = self.coordinator.optimization_status
        self._attr_extra_state_attributes = attrs
        super()._handle_coordinator_update()


class HaeoOptimizationStatusSensor(HaeoSensorBase):
    """Sensor for optimization status."""

    def __init__(
        self,
        coordinator: HaeoDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry, "optimization_status", "Optimization Status")

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        return self.coordinator.optimization_status

    @property
    def icon(self) -> str:
        """Return the icon of the sensor."""
        if self.coordinator.optimization_status == OPTIMIZATION_STATUS_SUCCESS:
            return "mdi:check-circle"
        else:
            return "mdi:alert-circle"

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        attrs = {}
        if self.coordinator.last_optimization_time:
            attrs["last_optimization"] = self.coordinator.last_optimization_time.isoformat()
        if self.coordinator.last_optimization_cost is not None:
            attrs["last_cost"] = self.coordinator.last_optimization_cost
        return attrs


class HaeoEntityPowerConsumptionSensor(HaeoSensorBase):
    """Sensor for entity power consumption."""

    def __init__(
        self,
        coordinator: HaeoDataUpdateCoordinator,
        config_entry: ConfigEntry,
        entity_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator, config_entry, f"{entity_name}_power_consumption", f"{entity_name} Power Consumption"
        )
        self.entity_name = entity_name
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> float | None:
        """Return the current power consumption."""
        entity_data = self.coordinator.get_entity_data(self.entity_name)
        if entity_data and "power_consumption" in entity_data:
            # Return the current period's value (first value)
            consumption_data = entity_data["power_consumption"]
            return consumption_data[0] if consumption_data else None
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        attrs = {}
        entity_data = self.coordinator.get_entity_data(self.entity_name)
        if entity_data and "power_consumption" in entity_data:
            consumption_data = entity_data["power_consumption"]
            timestamps = self.coordinator.get_future_timestamps()

            # Add forecast data
            attrs["forecast"] = consumption_data

            # Add timestamped forecast
            if len(timestamps) == len(consumption_data):
                attrs["timestamped_forecast"] = [
                    {"timestamp": ts, "value": value} for ts, value in zip(timestamps, consumption_data)
                ]
        return attrs


class HaeoEntityPowerProductionSensor(HaeoSensorBase):
    """Sensor for entity power production."""

    def __init__(
        self,
        coordinator: HaeoDataUpdateCoordinator,
        config_entry: ConfigEntry,
        entity_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator, config_entry, f"{entity_name}_power_production", f"{entity_name} Power Production"
        )
        self.entity_name = entity_name
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> float | None:
        """Return the current power production."""
        entity_data = self.coordinator.get_entity_data(self.entity_name)
        if entity_data and "power_production" in entity_data:
            # Return the current period's value (first value)
            production_data = entity_data["power_production"]
            return production_data[0] if production_data else None
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        attrs = {}
        entity_data = self.coordinator.get_entity_data(self.entity_name)
        if entity_data and "power_production" in entity_data:
            production_data = entity_data["power_production"]
            timestamps = self.coordinator.get_future_timestamps()

            # Add forecast data
            attrs["forecast"] = production_data

            # Add timestamped forecast
            if len(timestamps) == len(production_data):
                attrs["timestamped_forecast"] = [
                    {"timestamp": ts, "value": value} for ts, value in zip(timestamps, production_data)
                ]
        return attrs


class HaeoEntityNetPowerSensor(HaeoSensorBase):
    """Sensor for entity net power (consumption - production)."""

    def __init__(
        self,
        coordinator: HaeoDataUpdateCoordinator,
        config_entry: ConfigEntry,
        entity_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry, f"{entity_name}_net_power", f"{entity_name} Net Power")
        self.entity_name = entity_name
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> float | None:
        """Return the current net power."""
        entity_data = self.coordinator.get_entity_data(self.entity_name)
        if entity_data and "power" in entity_data:
            # Return the current period's value (first value)
            power_data = entity_data["power"]
            return power_data[0] if power_data else None
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        attrs = {}
        entity_data = self.coordinator.get_entity_data(self.entity_name)
        if entity_data and "power" in entity_data:
            attrs["forecast"] = entity_data["power"]
        return attrs


class HaeoEntityPowerSensor(HaeoSensorBase):
    """Sensor for single power value entities (load, generator)."""

    def __init__(
        self,
        coordinator: HaeoDataUpdateCoordinator,
        config_entry: ConfigEntry,
        entity_name: str,
        entity_type: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry, f"{entity_name}_power", f"{entity_name} Power")
        self.entity_name = entity_name
        self.entity_type = entity_type
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> float | None:
        """Return the current power."""
        entity_data = self.coordinator.get_entity_data(self.entity_name)
        if entity_data:
            # For loads, check power_consumption; for generators, check power_production
            if self.entity_type == "load" and "power_consumption" in entity_data:
                power_data = entity_data["power_consumption"]
                return power_data[0] if power_data else None
            elif self.entity_type == "generator" and "power_production" in entity_data:
                power_data = entity_data["power_production"]
                return power_data[0] if power_data else None
        return None


class HaeoEntityEnergySensor(HaeoSensorBase):
    """Sensor for entity energy (batteries)."""

    def __init__(
        self,
        coordinator: HaeoDataUpdateCoordinator,
        config_entry: ConfigEntry,
        entity_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry, f"{entity_name}_energy", f"{entity_name} Energy")
        self.entity_name = entity_name
        self._attr_device_class = SensorDeviceClass.ENERGY_STORAGE
        self._attr_native_unit_of_measurement = UnitOfEnergy.WATT_HOUR
        self._attr_state_class = SensorStateClass.TOTAL

    @property
    def native_value(self) -> float | None:
        """Return the current energy level."""
        entity_data = self.coordinator.get_entity_data(self.entity_name)
        if entity_data and "energy" in entity_data:
            # Return the current period's value (first value)
            energy_data = entity_data["energy"]
            return energy_data[0] if energy_data else None
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        attrs = {}
        entity_data = self.coordinator.get_entity_data(self.entity_name)
        if entity_data and "energy" in entity_data:
            energy_data = entity_data["energy"]
            timestamps = self.coordinator.get_future_timestamps()

            # Add forecast data
            attrs["forecast"] = energy_data

            # Add timestamped forecast
            if len(timestamps) == len(energy_data):
                attrs["timestamped_forecast"] = [
                    {"timestamp": ts, "value": value} for ts, value in zip(timestamps, energy_data)
                ]
        return attrs


class HaeoConnectionPowerSensor(HaeoSensorBase):
    """Sensor for connection power flow."""

    def __init__(
        self,
        coordinator: HaeoDataUpdateCoordinator,
        config_entry: ConfigEntry,
        source: str,
        target: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry, f"{source}_to_{target}_power", f"{source} to {target} Power Flow")
        self.source = source
        self.target = target
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> float | None:
        """Return the current power flow."""
        connection_data = self.coordinator.get_connection_data(self.source, self.target)
        if connection_data:
            # Return the current period's value (first value)
            return connection_data[0] if connection_data else None
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        attrs = {}
        connection_data = self.coordinator.get_connection_data(self.source, self.target)
        if connection_data:
            timestamps = self.coordinator.get_future_timestamps()

            # Add forecast data
            attrs["forecast"] = connection_data

            # Add timestamped forecast
            if len(timestamps) == len(connection_data):
                attrs["timestamped_forecast"] = [
                    {"timestamp": ts, "value": value} for ts, value in zip(timestamps, connection_data)
                ]
        attrs["source"] = self.source
        attrs["target"] = self.target
        return attrs
