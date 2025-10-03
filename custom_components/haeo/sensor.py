"""Sensor platform for Home Assistant Energy Optimization integration."""

import logging
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_ENERGY,
    ATTR_POWER,
    DOMAIN,
    OPTIMIZATION_STATUS_PENDING,
    OPTIMIZATION_STATUS_SUCCESS,
    UNIT_CURRENCY,
    get_element_type_name,
)
from .coordinator import HaeoDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


def get_device_info_for_element(element_name: str, element_type: str, config_entry: ConfigEntry) -> DeviceInfo:
    """Get device info for a specific element."""
    device_name = get_element_type_name(element_type)
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


async def async_register_devices(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Register devices with the device registry."""
    device_registry_client = device_registry.async_get(hass)

    # Register the main network device
    device_registry_client.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, config_entry.entry_id)},
        name="HAEO Energy Optimization Network",
        manufacturer="HAEO",
        model="Energy Optimization Network",
        sw_version="1.0.0",
    )

    # Register devices for each participant element
    participants = config_entry.data.get("participants", {})
    for element_name, element_config in participants.items():
        element_type = element_config.get("type", "")

        device_name = get_element_type_name(element_type)
        device_registry_client.async_get_or_create(
            config_entry_id=config_entry.entry_id,
            identifiers={(DOMAIN, f"{config_entry.entry_id}_{element_name}")},
            name=element_name,
            manufacturer="HAEO",
            model=f"Energy Optimization {device_name}",
            via_device=(DOMAIN, config_entry.entry_id),
        )


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up HAEO sensor platform."""
    coordinator: HaeoDataUpdateCoordinator | None = getattr(config_entry, "runtime_data", None)

    # Cannot create any sensors without a coordinator
    if not coordinator:
        _LOGGER.debug("No coordinator available, skipping sensor setup")
        return

    # Register devices with the device registry
    try:
        await async_register_devices(hass, config_entry)
    except Exception as ex:
        _LOGGER.warning("Failed to register devices: %s", ex)

    entities = _create_sensors(coordinator, config_entry)

    if entities:
        async_add_entities(entities)


def _create_sensors(
    coordinator: HaeoDataUpdateCoordinator,
    config_entry: ConfigEntry,
) -> list[SensorEntity]:
    """Create all HAEO sensors."""
    entities: list[SensorEntity] = []

    # Add hub-level optimization sensors
    entities.append(HaeoOptimizationCostSensor(coordinator, config_entry))
    entities.append(HaeoOptimizationStatusSensor(coordinator, config_entry))

    # Add element-specific sensors
    participants = config_entry.data.get("participants", {})
    for element_name, element_config in participants.items():
        element_type = element_config.get("type", "")

        # Determine which sensors to create for this element
        sensor_configs = _get_element_sensor_configs(coordinator, element_name)

        for sensor_config in sensor_configs:
            entities.append(
                sensor_config["sensor_class"](
                    coordinator,
                    config_entry,
                    element_name,
                    element_type,
                )
            )

    return entities


def _get_element_sensor_configs(
    coordinator: HaeoDataUpdateCoordinator,
    element_name: str,
) -> list[dict[str, Any]]:
    """Get sensor configurations for an element."""
    sensor_configs = []

    # Check if we have optimization data for this element
    optimization_result = coordinator.optimization_result
    if optimization_result:
        solution = optimization_result.get("solution", {})
        has_power_data = f"{element_name}_{ATTR_POWER}" in solution
        has_energy_data = f"{element_name}_{ATTR_ENERGY}" in solution
    else:
        # Assume we'll have data when optimization runs
        # This is a reasonable assumption for most element types
        has_power_data = True
        has_energy_data = True

    # Add power sensor if element supports it
    if has_power_data:
        sensor_configs.append({"sensor_class": HaeoElementPowerSensor})

    # Add energy sensor if element supports it (typically batteries and other storage)
    if has_energy_data:
        sensor_configs.append({"sensor_class": HaeoElementEnergySensor})

    return sensor_configs


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
        self.element_name = element_name
        self.element_type = element_type
        self._attr_name = f"HAEO {name_suffix}"
        self._attr_unique_id = f"{config_entry.entry_id}_{sensor_type}"

        # Set device info based on whether this is a hub-level or entity-level sensor
        if element_name and element_type:
            self._attr_device_info = get_device_info_for_element(element_name, element_type, config_entry)
        else:
            self._attr_device_info = get_device_info_for_network(config_entry)

    @property
    def available(self) -> bool:
        """Return if the sensor is available."""
        # Check if coordinator is available
        if not super().available:
            return False

        # For entity-specific sensors, check if we can get element data
        if self.element_name and self.element_type:
            try:
                element_data = self.coordinator.get_element_data(self.element_name)
                return element_data is not None
            except Exception:
                return False

        # For hub-level sensors, check if coordinator has optimization results
        if self.sensor_type in ["optimization_cost", "optimization_status"]:
            return (
                self.coordinator.optimization_result is not None
                or self.coordinator.optimization_status != OPTIMIZATION_STATUS_PENDING
            )

        return True


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
        try:
            element_data = self.coordinator.get_element_data(self.element_name)
            if element_data and ATTR_POWER in element_data:
                # Return the current period's value (first value)
                power_data = element_data[ATTR_POWER]
                return power_data[0] if power_data else None
        except Exception as ex:
            _LOGGER.debug("Error getting element data for %s: %s", self.element_name, ex)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        attrs = {}
        try:
            element_data = self.coordinator.get_element_data(self.element_name)
            if element_data and ATTR_POWER in element_data:
                power_data = element_data[ATTR_POWER]

                # Add forecast data
                attrs["forecast"] = power_data

                # Add timestamped forecast (with error handling)
                try:
                    timestamps = self.coordinator.get_future_timestamps()
                    if len(timestamps) == len(power_data):
                        attrs["timestamped_forecast"] = [
                            {"timestamp": ts, "value": value} for ts, value in zip(timestamps, power_data, strict=False)
                        ]
                except Exception as ex:
                    _LOGGER.debug("Error getting timestamps for %s: %s", self.element_name, ex)
        except Exception as ex:
            _LOGGER.debug("Error getting element attributes for %s: %s", self.element_name, ex)
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
            coordinator,
            config_entry,
            f"{element_name}_energy",
            f"{element_name} Energy",
            element_name,
            element_type,
        )
        self.element_name = element_name
        self._attr_device_class = SensorDeviceClass.ENERGY_STORAGE
        self._attr_native_unit_of_measurement = UnitOfEnergy.WATT_HOUR
        self._attr_state_class = SensorStateClass.TOTAL

    @property
    def native_value(self) -> float | None:
        """Return the current energy level."""
        try:
            element_data = self.coordinator.get_element_data(self.element_name)
            if element_data and ATTR_ENERGY in element_data:
                # Return the current period's value (first value)
                energy_data = element_data[ATTR_ENERGY]
                return energy_data[0] if energy_data else None
        except Exception as ex:
            _LOGGER.debug("Error getting energy data for %s: %s", self.element_name, ex)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        attrs = {}
        try:
            element_data = self.coordinator.get_element_data(self.element_name)
            if element_data and ATTR_ENERGY in element_data:
                energy_data = element_data[ATTR_ENERGY]

                # Add forecast data
                attrs["forecast"] = energy_data

                # Add timestamped forecast (with error handling)
                try:
                    timestamps = self.coordinator.get_future_timestamps()
                    if len(timestamps) == len(energy_data):
                        attrs["timestamped_forecast"] = [
                            {"timestamp": ts, "value": value}
                            for ts, value in zip(timestamps, energy_data, strict=False)
                        ]
                except Exception as ex:
                    _LOGGER.debug("Error getting timestamps for %s: %s", self.element_name, ex)
        except Exception as ex:
            _LOGGER.debug("Error getting energy attributes for %s: %s", self.element_name, ex)
        return attrs
