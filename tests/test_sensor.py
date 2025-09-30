"""Test the HAEO sensor platform."""

from unittest.mock import AsyncMock, Mock
import pytest
from datetime import datetime, timezone

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from custom_components.haeo.const import (
    DOMAIN,
    CONF_ENTITIES,
    CONF_CONNECTIONS,
    ENTITY_TYPE_BATTERY,
    ENTITY_TYPE_GRID,
    OPTIMIZATION_STATUS_SUCCESS,
    OPTIMIZATION_STATUS_FAILED,
    UNIT_CURRENCY,
    ATTR_POWER_CONSUMPTION,
    ATTR_POWER_PRODUCTION,
)
from custom_components.haeo.sensor import (
    async_setup_entry,
    HaeoSensorBase,
    HaeoOptimizationCostSensor,
    HaeoOptimizationStatusSensor,
    HaeoEntityPowerConsumptionSensor,
    HaeoEntityPowerProductionSensor,
    HaeoEntityNetPowerSensor,
    HaeoEntityEnergySensor,
    HaeoConnectionPowerSensor,
)
from custom_components.haeo.coordinator import HaeoDataUpdateCoordinator


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator."""
    coordinator = Mock(spec=HaeoDataUpdateCoordinator)
    coordinator.last_update_success = True
    coordinator.optimization_status = OPTIMIZATION_STATUS_SUCCESS
    coordinator.last_optimization_cost = 15.50
    coordinator.last_optimization_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    coordinator.optimization_result = {
        "solution": {
            "test_battery_power_consumption": [100.0, 150.0, 200.0],
            "test_battery_power_production": [50.0, 75.0, 100.0],
            "test_battery_power": [50.0, 75.0, 100.0],
            "test_battery_energy": [500.0, 600.0, 700.0],
        }
    }
    coordinator.get_entity_data.return_value = {
        ATTR_POWER_CONSUMPTION: [100.0, 150.0, 200.0],
        ATTR_POWER_PRODUCTION: [50.0, 75.0, 100.0],
        "power": [50.0, 75.0, 100.0],
        "energy": [500.0, 600.0, 700.0],
    }
    coordinator.get_connection_data.return_value = [75.0, 125.0, 175.0]
    coordinator.get_future_timestamps.return_value = [
        datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
        datetime(2024, 1, 1, 14, 0, 0, tzinfo=timezone.utc),
        datetime(2024, 1, 1, 15, 0, 0, tzinfo=timezone.utc),
    ]
    return coordinator


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    return Mock(
        spec=ConfigEntry,
        entry_id="test_entry",
        data={
            CONF_ENTITIES: [
                {"name": "test_battery", "type": ENTITY_TYPE_BATTERY},
                {"name": "test_grid", "type": ENTITY_TYPE_GRID},
            ],
            CONF_CONNECTIONS: [
                {"source": "test_battery", "target": "test_grid"},
            ],
        },
    )


@pytest.fixture
def mock_add_entities():
    """Create a mock add entities callback."""
    return AsyncMock()


class TestSensorSetup:
    """Test sensor platform setup."""

    async def test_async_setup_entry(self, hass: HomeAssistant, mock_config_entry, mock_coordinator, mock_add_entities):
        """Test setting up sensors from config entry."""
        # Set up the config entry with runtime_data
        mock_config_entry.runtime_data = mock_coordinator

        await async_setup_entry(hass, mock_config_entry, mock_add_entities)

        # Verify that entities were added
        mock_add_entities.assert_called_once()
        added_entities = mock_add_entities.call_args[0][0]

        # Should have optimization sensors + entity sensors + connection sensors
        assert len(added_entities) >= 2  # At least cost and status sensors

        # Check for specific sensor types
        sensor_types = [type(entity).__name__ for entity in added_entities]
        assert "HaeoOptimizationCostSensor" in sensor_types
        assert "HaeoOptimizationStatusSensor" in sensor_types


class TestHaeoSensorBase:
    """Test the base sensor class."""

    def test_init(self, mock_coordinator, mock_config_entry):
        """Test sensor base initialization."""
        sensor = HaeoSensorBase(mock_coordinator, mock_config_entry, "test_type", "Test Sensor")

        assert sensor.config_entry == mock_config_entry
        assert sensor.sensor_type == "test_type"
        assert sensor._attr_name == "HAEO Test Sensor"
        assert sensor._attr_unique_id == f"{mock_config_entry.entry_id}_test_type"

    def test_device_info(self, mock_coordinator, mock_config_entry):
        """Test device info property."""
        sensor = HaeoSensorBase(mock_coordinator, mock_config_entry, "test_type", "Test Sensor")
        device_info = sensor.device_info

        assert device_info is not None
        assert device_info.get("identifiers") == {(DOMAIN, mock_config_entry.entry_id)}
        assert device_info.get("name") == "HAEO Energy Optimizer"
        assert device_info.get("manufacturer") == "HAEO"

    def test_available_success(self, mock_coordinator, mock_config_entry):
        """Test availability when coordinator is successful."""
        mock_coordinator.last_update_success = True
        sensor = HaeoSensorBase(mock_coordinator, mock_config_entry, "test_type", "Test Sensor")

        assert sensor.available is True

    def test_available_failure(self, mock_coordinator, mock_config_entry):
        """Test availability when coordinator fails."""
        mock_coordinator.last_update_success = False
        sensor = HaeoSensorBase(mock_coordinator, mock_config_entry, "test_type", "Test Sensor")

        assert sensor.available is False


class TestHaeoOptimizationCostSensor:
    """Test the optimization cost sensor."""

    def test_init(self, mock_coordinator, mock_config_entry):
        """Test sensor initialization."""
        sensor = HaeoOptimizationCostSensor(mock_coordinator, mock_config_entry)

        assert sensor._attr_name == "HAEO Optimization Cost"
        assert sensor._attr_native_unit_of_measurement == UNIT_CURRENCY
        assert sensor._attr_unique_id == f"{mock_config_entry.entry_id}_optimization_cost"

    def test_native_value(self, mock_coordinator, mock_config_entry):
        """Test native value property."""
        sensor = HaeoOptimizationCostSensor(mock_coordinator, mock_config_entry)
        assert sensor.native_value == 15.50

    def test_native_value_none(self, mock_coordinator, mock_config_entry):
        """Test native value when no cost available."""
        mock_coordinator.last_optimization_cost = None
        sensor = HaeoOptimizationCostSensor(mock_coordinator, mock_config_entry)
        assert sensor.native_value is None

    def test_extra_state_attributes(self, mock_coordinator, mock_config_entry):
        """Test extra state attributes."""
        sensor = HaeoOptimizationCostSensor(mock_coordinator, mock_config_entry)
        attrs = sensor.extra_state_attributes

        assert attrs is not None
        assert "last_optimization" in attrs
        assert attrs["last_optimization"] == "2024-01-01T12:00:00+00:00"
        assert attrs["optimization_status"] == OPTIMIZATION_STATUS_SUCCESS

    def test_extra_state_attributes_no_time(self, mock_coordinator, mock_config_entry):
        """Test extra state attributes when no optimization time."""
        mock_coordinator.last_optimization_time = None
        sensor = HaeoOptimizationCostSensor(mock_coordinator, mock_config_entry)
        attrs = sensor.extra_state_attributes

        assert attrs is not None
        assert "last_optimization" not in attrs
        assert attrs["optimization_status"] == OPTIMIZATION_STATUS_SUCCESS


class TestHaeoOptimizationStatusSensor:
    """Test the optimization status sensor."""

    def test_init(self, mock_coordinator, mock_config_entry):
        """Test sensor initialization."""
        sensor = HaeoOptimizationStatusSensor(mock_coordinator, mock_config_entry)

        assert sensor._attr_name == "HAEO Optimization Status"
        assert sensor._attr_unique_id == f"{mock_config_entry.entry_id}_optimization_status"

    def test_native_value_success(self, mock_coordinator, mock_config_entry):
        """Test native value for successful optimization."""
        sensor = HaeoOptimizationStatusSensor(mock_coordinator, mock_config_entry)
        assert sensor.native_value == OPTIMIZATION_STATUS_SUCCESS

    def test_native_value_failure(self, mock_coordinator, mock_config_entry):
        """Test native value for failed optimization."""
        mock_coordinator.optimization_status = OPTIMIZATION_STATUS_FAILED
        sensor = HaeoOptimizationStatusSensor(mock_coordinator, mock_config_entry)
        assert sensor.native_value == OPTIMIZATION_STATUS_FAILED

    def test_icon_success(self, mock_coordinator, mock_config_entry):
        """Test icon for successful optimization."""
        sensor = HaeoOptimizationStatusSensor(mock_coordinator, mock_config_entry)
        assert sensor.icon == "mdi:check-circle"

    def test_icon_failure(self, mock_coordinator, mock_config_entry):
        """Test icon for failed optimization."""
        mock_coordinator.optimization_status = OPTIMIZATION_STATUS_FAILED
        sensor = HaeoOptimizationStatusSensor(mock_coordinator, mock_config_entry)
        assert sensor.icon == "mdi:alert-circle"

    def test_extra_state_attributes(self, mock_coordinator, mock_config_entry):
        """Test extra state attributes."""
        sensor = HaeoOptimizationStatusSensor(mock_coordinator, mock_config_entry)
        attrs = sensor.extra_state_attributes

        assert attrs is not None
        assert attrs["last_optimization"] == "2024-01-01T12:00:00+00:00"
        assert attrs["last_cost"] == 15.50


class TestHaeoEntityPowerConsumptionSensor:
    """Test the entity power consumption sensor."""

    def test_init(self, mock_coordinator, mock_config_entry):
        """Test sensor initialization."""
        sensor = HaeoEntityPowerConsumptionSensor(mock_coordinator, mock_config_entry, "test_battery")

        assert sensor.entity_name == "test_battery"
        assert sensor._attr_name == "HAEO test_battery Power Consumption"
        assert sensor._attr_unique_id == f"{mock_config_entry.entry_id}_test_battery_power_consumption"

    def test_native_value(self, mock_coordinator, mock_config_entry):
        """Test native value property."""
        sensor = HaeoEntityPowerConsumptionSensor(mock_coordinator, mock_config_entry, "test_battery")
        assert sensor.native_value == 100.0

    def test_native_value_no_data(self, mock_coordinator, mock_config_entry):
        """Test native value when no data available."""
        mock_coordinator.get_entity_data.return_value = None
        sensor = HaeoEntityPowerConsumptionSensor(mock_coordinator, mock_config_entry, "test_battery")
        assert sensor.native_value is None

    def test_native_value_empty_data(self, mock_coordinator, mock_config_entry):
        """Test native value when data is empty."""
        mock_coordinator.get_entity_data.return_value = {ATTR_POWER_CONSUMPTION: []}
        sensor = HaeoEntityPowerConsumptionSensor(mock_coordinator, mock_config_entry, "test_battery")
        assert sensor.native_value is None

    def test_extra_state_attributes(self, mock_coordinator, mock_config_entry):
        """Test extra state attributes."""
        sensor = HaeoEntityPowerConsumptionSensor(mock_coordinator, mock_config_entry, "test_battery")
        attrs = sensor.extra_state_attributes

        assert attrs is not None
        assert attrs["forecast"] == [100.0, 150.0, 200.0]
        assert "timestamped_forecast" in attrs
        assert len(attrs["timestamped_forecast"]) == 3
        assert attrs["timestamped_forecast"][0]["value"] == 100.0


class TestHaeoEntityPowerProductionSensor:
    """Test the entity power production sensor."""

    def test_init(self, mock_coordinator, mock_config_entry):
        """Test sensor initialization."""
        sensor = HaeoEntityPowerProductionSensor(mock_coordinator, mock_config_entry, "test_battery")

        assert sensor.entity_name == "test_battery"
        assert sensor._attr_name == "HAEO test_battery Power Production"

    def test_native_value(self, mock_coordinator, mock_config_entry):
        """Test native value property."""
        sensor = HaeoEntityPowerProductionSensor(mock_coordinator, mock_config_entry, "test_battery")
        assert sensor.native_value == 50.0


class TestHaeoEntityNetPowerSensor:
    """Test the entity net power sensor."""

    def test_init(self, mock_coordinator, mock_config_entry):
        """Test sensor initialization."""
        sensor = HaeoEntityNetPowerSensor(mock_coordinator, mock_config_entry, "test_battery")

        assert sensor.entity_name == "test_battery"
        assert sensor._attr_name == "HAEO test_battery Net Power"

    def test_native_value(self, mock_coordinator, mock_config_entry):
        """Test native value property."""
        sensor = HaeoEntityNetPowerSensor(mock_coordinator, mock_config_entry, "test_battery")
        assert sensor.native_value == 50.0


class TestHaeoEntityEnergySensor:
    """Test the entity energy sensor."""

    def test_init(self, mock_coordinator, mock_config_entry):
        """Test sensor initialization."""
        sensor = HaeoEntityEnergySensor(mock_coordinator, mock_config_entry, "test_battery")

        assert sensor.entity_name == "test_battery"
        assert sensor._attr_name == "HAEO test_battery Energy"

    def test_native_value(self, mock_coordinator, mock_config_entry):
        """Test native value property."""
        sensor = HaeoEntityEnergySensor(mock_coordinator, mock_config_entry, "test_battery")
        assert sensor.native_value == 500.0


class TestHaeoConnectionPowerSensor:
    """Test the connection power sensor."""

    def test_init(self, mock_coordinator, mock_config_entry):
        """Test sensor initialization."""
        sensor = HaeoConnectionPowerSensor(mock_coordinator, mock_config_entry, "test_battery", "test_grid")

        assert sensor.source == "test_battery"
        assert sensor.target == "test_grid"
        assert sensor._attr_name == "HAEO test_battery to test_grid Power Flow"

    def test_native_value(self, mock_coordinator, mock_config_entry):
        """Test native value property."""
        sensor = HaeoConnectionPowerSensor(mock_coordinator, mock_config_entry, "test_battery", "test_grid")
        assert sensor.native_value == 75.0

    def test_native_value_no_data(self, mock_coordinator, mock_config_entry):
        """Test native value when no connection data available."""
        mock_coordinator.get_connection_data.return_value = None
        sensor = HaeoConnectionPowerSensor(mock_coordinator, mock_config_entry, "test_battery", "test_grid")
        assert sensor.native_value is None

    def test_native_value_empty_data(self, mock_coordinator, mock_config_entry):
        """Test native value when connection data is empty."""
        mock_coordinator.get_connection_data.return_value = []
        sensor = HaeoConnectionPowerSensor(mock_coordinator, mock_config_entry, "test_battery", "test_grid")
        assert sensor.native_value is None

    def test_handle_coordinator_update(self, mock_coordinator, mock_config_entry, hass):
        """Test handling coordinator updates."""
        sensor = HaeoConnectionPowerSensor(mock_coordinator, mock_config_entry, "test_battery", "test_grid")
        sensor.hass = hass  # Set hass attribute for the sensor
        sensor.entity_id = "sensor.test_battery_to_test_grid_power_flow"  # Set entity_id

        # Test with optimization data
        sensor._handle_coordinator_update()
        assert sensor.native_value == 75.0  # Should get connection data
        assert "last_optimization" in sensor.extra_state_attributes
        assert sensor.extra_state_attributes["optimization_status"] == OPTIMIZATION_STATUS_SUCCESS
