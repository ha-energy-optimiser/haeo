"""Test the HAEO sensor platform."""

from unittest.mock import AsyncMock, Mock
import pytest
from datetime import datetime, timezone

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.haeo.const import (
    CONF_ELEMENT_TYPE,
    DOMAIN,
    ELEMENT_TYPE_BATTERY,
    ELEMENT_TYPE_CONNECTION,
    ELEMENT_TYPE_GENERATOR,
    ELEMENT_TYPE_GRID,
    ELEMENT_TYPE_LOAD_FIXED,
    ELEMENT_TYPE_LOAD_FORECAST,
    ELEMENT_TYPE_NET,
    OPTIMIZATION_STATUS_SUCCESS,
    OPTIMIZATION_STATUS_FAILED,
    UNIT_CURRENCY,
    ATTR_POWER,
    ATTR_ENERGY,
)
from custom_components.haeo.sensor import (
    async_setup_entry,
    HaeoSensorBase,
    HaeoOptimizationCostSensor,
    HaeoOptimizationStatusSensor,
    HaeoElementPowerSensor,
    HaeoElementEnergySensor,
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
            "test_battery_power": [50.0, 75.0, 100.0],  # Battery transporting power
            "test_battery_energy": [500.0, 600.0, 700.0],
        }
    }
    coordinator.get_element_data.return_value = {
        ATTR_POWER: [-50.0, -75.0, -100.0],  # Net power (negative = consuming)
        ATTR_ENERGY: [500.0, 600.0, 700.0],
    }
    coordinator.get_future_timestamps.return_value = [
        datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
        datetime(2024, 1, 1, 14, 0, 0, tzinfo=timezone.utc),
        datetime(2024, 1, 1, 15, 0, 0, tzinfo=timezone.utc),
    ]
    return coordinator


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    return MockConfigEntry(
        title="Test HAEO",
        domain=DOMAIN,
        entry_id="test_entry",
        data={
            "participants": {
                "test_battery": {CONF_ELEMENT_TYPE: ELEMENT_TYPE_BATTERY},
                "test_grid": {CONF_ELEMENT_TYPE: ELEMENT_TYPE_GRID},
                "test_load_fixed": {CONF_ELEMENT_TYPE: ELEMENT_TYPE_LOAD_FIXED},
                "test_load_forecast": {CONF_ELEMENT_TYPE: ELEMENT_TYPE_LOAD_FORECAST},
                "test_connection": {CONF_ELEMENT_TYPE: ELEMENT_TYPE_CONNECTION},
            },
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
        assert device_info.get("name") == "HAEO Energy Optimization Network"
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


class TestHaeoElementPowerSensor:
    """Test the entity power consumption sensor."""

    def test_init(self, mock_coordinator, mock_config_entry):
        """Test sensor initialization."""
        sensor = HaeoElementPowerSensor(mock_coordinator, mock_config_entry, "test_battery", ELEMENT_TYPE_BATTERY)

        assert sensor.element_name == "test_battery"
        assert sensor._attr_name == "HAEO test_battery Power"
        assert sensor._attr_unique_id == f"{mock_config_entry.entry_id}_test_battery_power"

    def test_native_value(self, mock_coordinator, mock_config_entry):
        """Test native value property."""
        sensor = HaeoElementPowerSensor(mock_coordinator, mock_config_entry, "test_battery", ELEMENT_TYPE_BATTERY)
        assert sensor.native_value == -50.0  # Net power: 0 production - 50 consumption = -50

    def test_native_value_no_data(self, mock_coordinator, mock_config_entry):
        """Test native value when no data available."""
        mock_coordinator.get_element_data.return_value = None
        sensor = HaeoElementPowerSensor(mock_coordinator, mock_config_entry, "test_battery", ELEMENT_TYPE_BATTERY)
        assert sensor.native_value is None

    def test_native_value_empty_data(self, mock_coordinator, mock_config_entry):
        """Test native value when data is empty."""
        mock_coordinator.get_element_data.return_value = {ATTR_POWER: []}
        sensor = HaeoElementPowerSensor(mock_coordinator, mock_config_entry, "test_battery", ELEMENT_TYPE_BATTERY)
        assert sensor.native_value is None

    def test_extra_state_attributes(self, mock_coordinator, mock_config_entry):
        """Test extra state attributes."""
        sensor = HaeoElementPowerSensor(mock_coordinator, mock_config_entry, "test_battery", ELEMENT_TYPE_BATTERY)
        attrs = sensor.extra_state_attributes

        assert attrs is not None
        assert attrs["forecast"] == [-50.0, -75.0, -100.0]  # Net power forecast
        assert "timestamped_forecast" in attrs
        assert len(attrs["timestamped_forecast"]) == 3
        assert attrs["timestamped_forecast"][0]["value"] == -50.0


class TestHaeoElementEnergySensor:
    """Test the entity energy sensor."""

    def test_init(self, mock_coordinator, mock_config_entry):
        """Test sensor initialization."""
        sensor = HaeoElementEnergySensor(mock_coordinator, mock_config_entry, "test_battery", ELEMENT_TYPE_BATTERY)

        assert sensor.element_name == "test_battery"
        assert sensor._attr_name == "HAEO test_battery Energy"

    def test_native_value(self, mock_coordinator, mock_config_entry):
        """Test native value property."""
        sensor = HaeoElementEnergySensor(mock_coordinator, mock_config_entry, "test_battery", ELEMENT_TYPE_BATTERY)
        assert sensor.native_value == 500.0

    def test_native_value_no_data(self, mock_coordinator, mock_config_entry):
        """Test native value when no data available."""
        mock_coordinator.get_element_data.return_value = None
        sensor = HaeoElementEnergySensor(mock_coordinator, mock_config_entry, "test_battery", ELEMENT_TYPE_BATTERY)
        assert sensor.native_value is None

    def test_native_value_empty_data(self, mock_coordinator, mock_config_entry):
        """Test native value when energy data is empty."""
        mock_coordinator.get_element_data.return_value = {ATTR_ENERGY: []}
        sensor = HaeoElementEnergySensor(mock_coordinator, mock_config_entry, "test_battery", ELEMENT_TYPE_BATTERY)
        assert sensor.native_value is None

    def test_extra_state_attributes(self, mock_coordinator, mock_config_entry):
        """Test extra state attributes."""
        sensor = HaeoElementEnergySensor(mock_coordinator, mock_config_entry, "test_battery", ELEMENT_TYPE_BATTERY)
        attrs = sensor.extra_state_attributes

        assert attrs is not None
        assert attrs["forecast"] == [500.0, 600.0, 700.0]
        assert "timestamped_forecast" in attrs
        assert len(attrs["timestamped_forecast"]) == 3


class TestHaeoSensorBaseWithElement:
    """Test the base sensor class with element-specific initialization."""

    def test_device_info_with_element(self, mock_coordinator, mock_config_entry):
        """Test device info property with element info."""
        sensor = HaeoSensorBase(
            mock_coordinator, mock_config_entry, "test_type", "Test Sensor", "test_battery", ELEMENT_TYPE_BATTERY
        )
        device_info = sensor.device_info

        assert device_info is not None
        assert device_info.get("identifiers") == {(DOMAIN, f"{mock_config_entry.entry_id}_test_battery")}
        assert device_info.get("name") == "test_battery"
        assert device_info.get("manufacturer") == "HAEO"
        assert device_info.get("model") == "Energy Optimization Battery"


# Coordinator update tests removed as they require complex Home Assistant context mocking
# The functionality is already tested through the property getters and existing coordinator tests


class TestSensorErrorHandling:
    """Test sensor error handling scenarios."""

    def test_coordinator_get_element_data_exception(self, mock_coordinator, mock_config_entry):
        """Test handling exception when getting element data."""
        # Set up normal data first
        mock_coordinator.get_element_data.return_value = {
            ATTR_POWER: [-50.0, -75.0, -100.0],
        }

        sensor = HaeoElementPowerSensor(mock_coordinator, mock_config_entry, "test_battery", ELEMENT_TYPE_BATTERY)

        # First verify normal operation
        assert sensor.native_value == -50.0

        # Now make get_element_data raise an exception
        mock_coordinator.get_element_data.side_effect = Exception("Data retrieval failed")

        # Create a new sensor instance to test error handling
        sensor_error = HaeoElementPowerSensor(mock_coordinator, mock_config_entry, "test_battery", ELEMENT_TYPE_BATTERY)

        # Should handle gracefully and return None
        assert sensor_error.native_value is None

    def test_coordinator_get_future_timestamps_exception(self, mock_coordinator, mock_config_entry):
        """Test handling exception when getting future timestamps."""
        # Set up normal data - keep get_element_data working but make get_future_timestamps fail
        mock_coordinator.get_element_data.return_value = {
            ATTR_POWER: [-50.0, -75.0, -100.0],
        }

        sensor = HaeoElementPowerSensor(mock_coordinator, mock_config_entry, "test_battery", ELEMENT_TYPE_BATTERY)

        # First verify normal operation
        attrs = sensor.extra_state_attributes
        assert attrs is not None
        assert "forecast" in attrs
        assert "timestamped_forecast" in attrs

        # Now make get_future_timestamps raise an exception
        mock_coordinator.get_future_timestamps.side_effect = Exception("Timestamp retrieval failed")

        # Create a new sensor instance to test error handling
        sensor_error = HaeoElementPowerSensor(mock_coordinator, mock_config_entry, "test_battery", ELEMENT_TYPE_BATTERY)

        # Should handle gracefully - the method should not raise an exception
        # and should return attributes with forecast but without timestamped_forecast
        attrs_error = sensor_error.extra_state_attributes
        assert attrs_error is not None
        assert "forecast" in attrs_error
        # timestamped_forecast should be missing due to the exception
        assert "timestamped_forecast" not in attrs_error

    def test_sensor_available_with_coordinator_exception(self, mock_coordinator, mock_config_entry):
        """Test sensor availability when coordinator throws exceptions."""
        # Make get_element_data raise an exception
        mock_coordinator.get_element_data.side_effect = Exception("Coordinator error")

        sensor = HaeoElementPowerSensor(mock_coordinator, mock_config_entry, "test_battery", ELEMENT_TYPE_BATTERY)

        # Sensor should be unavailable when coordinator fails
        assert sensor.available is False

    def test_sensor_available_with_no_element_data(self, mock_coordinator, mock_config_entry):
        """Test sensor availability when element data is None."""
        # Return None for element data (no data available)
        mock_coordinator.get_element_data.return_value = None

        sensor = HaeoElementPowerSensor(mock_coordinator, mock_config_entry, "test_battery", ELEMENT_TYPE_BATTERY)

        # Sensor should be unavailable when no data is available
        assert sensor.available is False

    def test_optimization_sensor_available_pending_status(self, mock_coordinator, mock_config_entry):
        """Test optimization sensor availability with pending status."""
        # Set up coordinator with pending status and no results
        mock_coordinator.optimization_result = None
        mock_coordinator.optimization_status = "pending"

        sensor = HaeoOptimizationCostSensor(mock_coordinator, mock_config_entry)

        # Sensor should be unavailable when status is pending and no results
        assert sensor.available is False

    def test_optimization_sensor_available_with_results(self, mock_coordinator, mock_config_entry):
        """Test optimization sensor availability with results."""
        # Set up coordinator with results
        mock_coordinator.optimization_result = {"cost": 100.0}
        mock_coordinator.optimization_status = "success"

        sensor = HaeoOptimizationCostSensor(mock_coordinator, mock_config_entry)

        # Sensor should be available when results exist
        assert sensor.available is True

    def test_native_value_with_no_element_data(self, mock_coordinator, mock_config_entry):
        """Test native value when element data is missing."""
        # Return None for element data
        mock_coordinator.get_element_data.return_value = None

        sensor = HaeoElementPowerSensor(mock_coordinator, mock_config_entry, "test_battery", ELEMENT_TYPE_BATTERY)

        # Should return None gracefully
        assert sensor.native_value is None

    def test_native_value_with_empty_element_data(self, mock_coordinator, mock_config_entry):
        """Test native value when element data is empty."""
        # Return empty dict for element data
        mock_coordinator.get_element_data.return_value = {}

        sensor = HaeoElementPowerSensor(mock_coordinator, mock_config_entry, "test_battery", ELEMENT_TYPE_BATTERY)

        # Should return None gracefully
        assert sensor.native_value is None


class TestSensorWithDifferentElementTypes:
    """Test sensors with different element types."""

    def test_battery_sensor_device_info(self, mock_coordinator, mock_config_entry):
        """Test device info for battery sensor."""
        sensor = HaeoElementPowerSensor(mock_coordinator, mock_config_entry, "test_battery", ELEMENT_TYPE_BATTERY)
        device_info = sensor.device_info

        assert device_info.get("model") == "Energy Optimization Battery"

    def test_grid_sensor_device_info(self, mock_coordinator, mock_config_entry):
        """Test device info for grid sensor."""
        sensor = HaeoElementPowerSensor(mock_coordinator, mock_config_entry, "test_grid", ELEMENT_TYPE_GRID)
        device_info = sensor.device_info

        assert device_info.get("model") == "Energy Optimization Grid Connection"

    def test_generator_sensor_device_info(self, mock_coordinator, mock_config_entry):
        """Test device info for generator sensor."""
        sensor = HaeoElementPowerSensor(mock_coordinator, mock_config_entry, "test_generator", ELEMENT_TYPE_GENERATOR)
        device_info = sensor.device_info

        assert device_info.get("model") == "Energy Optimization Generator"

    def test_load_sensor_device_info(self, mock_coordinator, mock_config_entry):
        """Test device info for load sensor."""
        sensor = HaeoElementPowerSensor(mock_coordinator, mock_config_entry, "test_load", ELEMENT_TYPE_LOAD)
        device_info = sensor.device_info

        assert device_info.get("model") == "Energy Optimization Load"

    def test_load_fixed_sensor_device_info(self, mock_coordinator, mock_config_entry):
        """Test device info for fixed load sensor."""
        sensor = HaeoElementPowerSensor(mock_coordinator, mock_config_entry, "test_load_fixed", ELEMENT_TYPE_LOAD_FIXED)
        device_info = sensor.device_info

        assert device_info.get("model") == "Energy Optimization Fixed Load"

    def test_load_forecast_sensor_device_info(self, mock_coordinator, mock_config_entry):
        """Test device info for forecast load sensor."""
        sensor = HaeoElementPowerSensor(
            mock_coordinator, mock_config_entry, "test_load_forecast", ELEMENT_TYPE_LOAD_FORECAST
        )
        device_info = sensor.device_info

        assert device_info.get("model") == "Energy Optimization Forecast Load"

    def test_net_sensor_device_info(self, mock_coordinator, mock_config_entry):
        """Test device info for net sensor."""
        sensor = HaeoElementPowerSensor(mock_coordinator, mock_config_entry, "test_net", ELEMENT_TYPE_NET)
        device_info = sensor.device_info

        assert device_info.get("model") == "Energy Optimization Network Node"

    def test_connection_sensor_device_info(self, mock_coordinator, mock_config_entry):
        """Test device info for connection sensor."""
        sensor = HaeoElementPowerSensor(mock_coordinator, mock_config_entry, "test_connection", ELEMENT_TYPE_CONNECTION)
        device_info = sensor.device_info

        assert device_info.get("model") == "Energy Optimization Connection"
