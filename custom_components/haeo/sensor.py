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
    CONF_ELEMENTS,
    DOMAIN,
    ELEMENT_TYPE_BATTERY,
    ELEMENT_TYPE_GRID,
    ELEMENT_TYPE_CONNECTION,
    ELEMENT_TYPE_LOAD,
    ELEMENT_TYPE_GENERATOR,
    ELEMENT_TYPE_NET,
    OPTIMIZATION_STATUS_SUCCESS,
    UNIT_CURRENCY,
    ATTR_POWER,
    ATTR_ENERGY,
)
from .coordinator import HaeoDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


def get_device_info_for_element(element_name: str, element_type: str, config_entry: ConfigEntry) -> DeviceInfo:
    """Get device info for a specific element."""
    device_name_map = {
        ELEMENT_TYPE_BATTERY: "Battery",
        ELEMENT_TYPE_GRID: "Grid Connection",
        ELEMENT_TYPE_LOAD: "Load",
        ELEMENT_TYPE_GENERATOR: "Generator",
        ELEMENT_TYPE_NET: "Network Node",
        ELEMENT_TYPE_CONNECTION: "Connection",
    }

    device_name = device_name_map.get(element_type, "Device")
    return DeviceInfo(
        identifiers={(DOMAIN, f"{config_entry.entry_id}_{element_name}")},
        name=f"{element_name}",
        manufacturer="HAEO",
        model=f"Energy Optimization {device_name}",
        via_device=(DOMAIN, config_entry.entry_id),
    )


def get_device_info_for_network(config_entry: ConfigEntry) -> DeviceInfo:
    """Get device info for the main hub."""
    return DeviceInfo(
        identifiers={(DOMAIN, config_entry.entry_id)},
        name="HAEO Energy Optimization Network",
        manufacturer="HAEO",
        model="Energy Optimization Network",
        sw_version="1.0.0",
    )


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up HAEO sensor platform."""
    coordinator: HaeoDataUpdateCoordinator = config_entry.runtime_data

    entities: list[SensorEntity] = []

    # Add optimization status and cost sensors (hub-level)
    entities.append(HaeoOptimizationCostSensor(coordinator, config_entry))
    entities.append(HaeoOptimizationStatusSensor(coordinator, config_entry))

    # Add element-specific sensors based on available data
    for element_config in config_entry.data[CONF_ELEMENTS]:
        element_name = element_config[CONF_NAME]
        element_type = element_config.get("type", "")

        # Create a helper function to check if we have optimization data for this entity
        def has_data_type(data_type: str) -> bool:
            if not coordinator.optimization_result:
                return True  # Assume we'll have it when optimization runs
            solution = coordinator.optimization_result.get("solution", {})
            return f"{element_name}_{data_type}" in solution

        # Add power consumption sensor if entity has this capability
        if has_data_type(ATTR_POWER):
            entities.append(HaeoElementPowerSensor(coordinator, config_entry, element_name, element_type))

        # Add energy sensor if entity has energy state (like batteries)
        if has_data_type(ATTR_ENERGY):
            entities.append(HaeoElementEnergySensor(coordinator, config_entry, element_name, element_type))

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
        element_name: str | None = None,
        element_type: str | None = None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.config_entry = config_entry
        self.sensor_type = sensor_type
        self._attr_name = f"HAEO {name_suffix}"
        self._attr_unique_id = f"{config_entry.entry_id}_{sensor_type}"

        # Set device info based on whether this is a hub-level or entity-level sensor
        if element_name and element_type:
            self._attr_device_info = get_device_info_for_element(element_name, element_type, config_entry)
        else:
            self._attr_device_info = get_device_info_for_network(config_entry)


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

        # Set initial values from coordinator
        self._attr_native_value = self.coordinator.last_optimization_cost
        attrs = {}
        if self.coordinator.last_optimization_time:
            attrs["last_optimization"] = self.coordinator.last_optimization_time.isoformat()
        attrs["optimization_status"] = self.coordinator.optimization_status
        self._attr_extra_state_attributes = attrs

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


class HaeoElementPowerSensor(HaeoSensorBase):
    """Sensor for element power."""

    def __init__(
        self,
        coordinator: HaeoDataUpdateCoordinator,
        config_entry: ConfigEntry,
        element_name: str,
        element_type: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            config_entry,
            f"{element_name}_power",
            f"{element_name} Power",
            element_name,
            element_type,
        )
        self.element_name = element_name
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> float | None:
        """Return the current net power (positive = producing, negative = consuming)."""
        element_data = self.coordinator.get_element_data(self.element_name)
        if element_data and ATTR_POWER in element_data:
            # Return the current period's value (first value)
            power_data = element_data[ATTR_POWER]
            return power_data[0] if power_data else None
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        attrs = {}
        element_data = self.coordinator.get_element_data(self.element_name)
        if element_data and ATTR_POWER in element_data:
            power_data = element_data[ATTR_POWER]
            timestamps = self.coordinator.get_future_timestamps()

            # Add forecast data
            attrs["forecast"] = power_data

            # Add timestamped forecast
            if len(timestamps) == len(power_data):
                attrs["timestamped_forecast"] = [
                    {"timestamp": ts, "value": value} for ts, value in zip(timestamps, power_data)
                ]
        return attrs


class HaeoElementEnergySensor(HaeoSensorBase):
    """Sensor for entity energy (batteries)."""

    def __init__(
        self,
        coordinator: HaeoDataUpdateCoordinator,
        config_entry: ConfigEntry,
        element_name: str,
        element_type: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator, config_entry, f"{element_name}_energy", f"{element_name} Energy", element_name, element_type
        )
        self.element_name = element_name
        self._attr_device_class = SensorDeviceClass.ENERGY_STORAGE
        self._attr_native_unit_of_measurement = UnitOfEnergy.WATT_HOUR
        self._attr_state_class = SensorStateClass.TOTAL

    @property
    def native_value(self) -> float | None:
        """Return the current energy level."""
        element_data = self.coordinator.get_element_data(self.element_name)
        if element_data and ATTR_ENERGY in element_data:
            # Return the current period's value (first value)
            energy_data = element_data[ATTR_ENERGY]
            return energy_data[0] if energy_data else None
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        attrs = {}
        element_data = self.coordinator.get_element_data(self.element_name)
        if element_data and ATTR_ENERGY in element_data:
            energy_data = element_data[ATTR_ENERGY]
            timestamps = self.coordinator.get_future_timestamps()

            # Add forecast data
            attrs["forecast"] = energy_data

            # Add timestamped forecast
            if len(timestamps) == len(energy_data):
                attrs["timestamped_forecast"] = [
                    {"timestamp": ts, "value": value} for ts, value in zip(timestamps, energy_data)
                ]
        return attrs
