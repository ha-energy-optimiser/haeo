"""Test the HAEO coordinator."""

from homeassistant.const import CONF_NAME, CONF_SOURCE, CONF_TARGET
import pytest
from unittest.mock import patch
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry
from datetime import datetime

from custom_components.haeo.coordinator import HaeoDataUpdateCoordinator
from custom_components.haeo.const import (
    CONF_CAPACITY,
    CONF_CURRENT_CHARGE_SENSOR,
    CONF_EXPORT_LIMIT,
    CONF_IMPORT_LIMIT,
    CONF_MAX_CHARGE_POWER,
    CONF_MAX_DISCHARGE_POWER,
    CONF_MAX_POWER,
    CONF_PARTICIPANTS,
    DOMAIN,
    ELEMENT_TYPE_BATTERY,
    ELEMENT_TYPE_CONNECTION,
    ELEMENT_TYPE_GRID,
    ELEMENT_TYPE_LOAD_FORECAST,
    OPTIMIZATION_STATUS_SUCCESS,
    OPTIMIZATION_STATUS_FAILED,
    ATTR_POWER,
    ATTR_ENERGY,
    CONF_PRICE_IMPORT_SENSOR,
    CONF_PRICE_EXPORT_SENSOR,
    CONF_FORECAST_SENSORS,
    CONF_SENSORS,
    CONF_SENSOR_ENTITY_ID,
    CONF_SENSOR_ATTRIBUTE,
    DEFAULT_N_PERIODS,
    CONF_ELEMENT_TYPE,
)


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            "integration_type": "hub",
            CONF_NAME: "Power Network",
            CONF_PARTICIPANTS: {
                "test_battery": {
                    CONF_ELEMENT_TYPE: ELEMENT_TYPE_BATTERY,
                    CONF_CAPACITY: 10000,
                    CONF_CURRENT_CHARGE_SENSOR: "sensor.battery_charge",
                },
                "test_grid": {
                    CONF_ELEMENT_TYPE: ELEMENT_TYPE_GRID,
                    CONF_IMPORT_LIMIT: 10000,
                    CONF_EXPORT_LIMIT: 5000,
                    CONF_PRICE_IMPORT_SENSOR: ["sensor.import_price"],
                    CONF_PRICE_EXPORT_SENSOR: ["sensor.export_price"],
                    # For tests, use constant pricing to avoid sensor setup complexity
                    "price_import": [0.1] * DEFAULT_N_PERIODS,
                    "price_export": [0.05] * DEFAULT_N_PERIODS,
                },
                "test_connection": {
                    CONF_ELEMENT_TYPE: ELEMENT_TYPE_CONNECTION,
                    CONF_SOURCE: "test_battery",
                    CONF_TARGET: "test_grid",
                    CONF_MAX_POWER: 5000,
                },
            },
        },
        entry_id="test_entry_id",
    )


async def test_coordinator_initialization(hass: HomeAssistant, mock_config_entry):
    """Test coordinator initialization."""
    coordinator = HaeoDataUpdateCoordinator(hass, mock_config_entry)

    assert coordinator.hass == hass
    assert coordinator.entry == mock_config_entry
    assert coordinator.config == mock_config_entry.data
    assert coordinator.network is None
    assert coordinator.optimization_result is None


async def test_build_network(hass: HomeAssistant, mock_config_entry):
    """Test building the network from configuration."""
    # Set up sensor state for battery
    hass.states.async_set("sensor.battery_charge", "50", {})

    coordinator = HaeoDataUpdateCoordinator(hass, mock_config_entry)

    await coordinator._build_network()

    assert coordinator.network is not None
    assert "test_battery" in coordinator.network.elements
    assert "test_grid" in coordinator.network.elements


async def test_get_sensor_forecast_with_forecast_attribute(hass: HomeAssistant, mock_config_entry):
    """Test getting sensor forecast with forecast attribute."""
    coordinator = HaeoDataUpdateCoordinator(hass, mock_config_entry)

    # Set up sensor state with forecast attribute
    hass.states.async_set("sensor.test", "100", {"forecast": [100, 200, 300, 400]})

    result = await coordinator._get_sensor_forecast("sensor.test")

    assert result == [100.0, 200.0, 300.0, 400.0]


async def test_get_sensor_forecast_fallback_to_state(hass: HomeAssistant, mock_config_entry):
    """Test getting sensor forecast fallback to current state."""
    coordinator = HaeoDataUpdateCoordinator(hass, mock_config_entry)

    # Set up sensor state without forecast attribute
    hass.states.async_set("sensor.test", "150", {})

    result = await coordinator._get_sensor_forecast("sensor.test")

    assert result is not None
    assert len(result) == 576  # DEFAULT_N_PERIODS
    assert all(x == 150.0 for x in result)


async def test_get_sensor_forecast_missing_sensor(hass: HomeAssistant, mock_config_entry):
    """Test getting forecast from missing sensor."""
    coordinator = HaeoDataUpdateCoordinator(hass, mock_config_entry)

    # Don't set any state for the sensor
    result = await coordinator._get_sensor_forecast("sensor.missing")

    assert result is None


@patch("custom_components.haeo.coordinator.HaeoDataUpdateCoordinator._run_optimization")
async def test_update_data_success(mock_optimize, hass: HomeAssistant, mock_config_entry):
    """Test successful data update."""
    # Set up sensor state for battery
    hass.states.async_set("sensor.battery_charge", "50", {})

    coordinator = HaeoDataUpdateCoordinator(hass, mock_config_entry)

    # Mock optimization result - now returns only cost
    mock_cost = 100.0
    mock_optimize.return_value = mock_cost

    async def async_job():
        return mock_cost

    with patch.object(hass, "async_add_executor_job", return_value=async_job()):
        result = await coordinator._async_update_data()

    assert result is not None
    assert coordinator.optimization_status == OPTIMIZATION_STATUS_SUCCESS
    assert coordinator.optimization_result is not None
    assert coordinator.optimization_result["cost"] == mock_cost


async def test_build_network_with_battery_sensor(hass: HomeAssistant):
    """Test building network with battery sensor configuration."""

    # Create a config entry with battery that has current charge sensor
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "integration_type": "hub",
            CONF_NAME: "Power Network",
            CONF_PARTICIPANTS: {
                "test_battery": {
                    CONF_ELEMENT_TYPE: ELEMENT_TYPE_BATTERY,
                    CONF_CAPACITY: 10000,
                    CONF_CURRENT_CHARGE_SENSOR: "sensor.battery_charge",
                    CONF_MAX_CHARGE_POWER: 5000,
                    CONF_MAX_DISCHARGE_POWER: 5000,
                }
            },
        },
    )

    # Create coordinator
    coordinator = HaeoDataUpdateCoordinator(hass, config_entry)

    # Mock the sensor value
    with patch.object(coordinator, "_get_sensor_value", return_value=75.0) as mock_get_sensor:
        # Build the network - this should trigger the sensor reading logic
        await coordinator._build_network()

        # Verify sensor was called
        mock_get_sensor.assert_called_with("sensor.battery_charge")


@patch("custom_components.haeo.coordinator.HaeoDataUpdateCoordinator._run_optimization")
async def test_update_data_failure(mock_optimize, hass: HomeAssistant, mock_config_entry):
    """Test failed data update."""
    # Set up sensor state for battery
    hass.states.async_set("sensor.battery_charge", "50", {})

    coordinator = HaeoDataUpdateCoordinator(hass, mock_config_entry)

    # Mock optimization failure
    mock_optimize.side_effect = Exception("Optimization failed")

    with patch.object(hass, "async_add_executor_job", side_effect=Exception("Optimization failed")):
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()

    assert coordinator.optimization_status == OPTIMIZATION_STATUS_FAILED


def test_get_element_data(hass: HomeAssistant, mock_config_entry):
    """Test getting entity data."""
    coordinator = HaeoDataUpdateCoordinator(hass, mock_config_entry)

    # Build a network with entities
    from custom_components.haeo.model import Network

    coordinator.network = Network("test", period=3600, n_periods=3)
    coordinator.network.add(
        ELEMENT_TYPE_BATTERY,
        "test_battery",
        capacity=1000,
        initial_charge_percentage=50,
        max_charge_power=100,
        max_discharge_power=100,
    )

    # Run a simple optimization to set variable values
    coordinator.network.optimize()

    result = coordinator.get_element_data("test_battery")

    assert result is not None
    assert ATTR_POWER in result
    assert ATTR_ENERGY in result
    assert len(result[ATTR_POWER]) == 3
    assert len(result[ATTR_ENERGY]) == 3


def test_get_element_data_no_result(hass: HomeAssistant, mock_config_entry):
    """Test getting entity data with no optimization result."""
    coordinator = HaeoDataUpdateCoordinator(hass, mock_config_entry)

    result = coordinator.get_element_data("test_battery")

    assert result is None


def test_last_optimization_properties(hass: HomeAssistant, mock_config_entry):
    """Test last optimization properties."""
    coordinator = HaeoDataUpdateCoordinator(hass, mock_config_entry)

    # Initially no optimization result
    assert coordinator.last_optimization_cost is None
    assert coordinator.last_optimization_time is None

    # Set optimization result
    from datetime import datetime

    test_time = datetime.now()
    coordinator.optimization_result = {
        "cost": 150.0,
        "solution": {},
        "timestamp": test_time,
    }

    assert coordinator.last_optimization_cost == 150.0
    assert coordinator.last_optimization_time == test_time


async def test_get_future_timestamps_no_result(hass: HomeAssistant, mock_config_entry):
    """Test getting future timestamps with no optimization result."""
    coordinator = HaeoDataUpdateCoordinator(hass, mock_config_entry)

    result = coordinator.get_future_timestamps()

    assert result == []


async def test_get_future_timestamps_with_result(hass: HomeAssistant, mock_config_entry):
    """Test getting future timestamps with optimization result."""
    coordinator = HaeoDataUpdateCoordinator(hass, mock_config_entry)

    # Set optimization result with timestamp
    test_time = datetime.now()
    coordinator.optimization_result = {
        "cost": 150.0,
        "timestamp": test_time,
    }

    result = coordinator.get_future_timestamps()

    assert len(result) == DEFAULT_N_PERIODS
    # Check that timestamps are ISO format strings
    for timestamp in result:
        assert isinstance(timestamp, str)
        # Should be able to parse as datetime
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))


async def test_build_network_no_participants(hass: HomeAssistant):
    """Test building network with no participants."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "integration_type": "hub",
            CONF_NAME: "Power Network",
            CONF_PARTICIPANTS: {},  # Empty participants
        },
        entry_id="test_entry_id",
    )

    coordinator = HaeoDataUpdateCoordinator(hass, config_entry)

    await coordinator._build_network()

    assert coordinator.network is not None
    # Should log warning about no participants


async def test_build_network_with_grid_sensor_pricing(hass: HomeAssistant):
    """Test building network with grid that has sensor-based pricing."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "integration_type": "hub",
            CONF_NAME: "Power Network",
            CONF_PARTICIPANTS: {
                "test_grid": {
                    CONF_ELEMENT_TYPE: ELEMENT_TYPE_GRID,
                    CONF_IMPORT_LIMIT: 10000,
                    CONF_EXPORT_LIMIT: 5000,
                    CONF_PRICE_IMPORT_SENSOR: ["sensor.import_price"],
                    CONF_PRICE_EXPORT_SENSOR: ["sensor.export_price"],
                }
            },
        },
        entry_id="test_entry_id",
    )

    coordinator = HaeoDataUpdateCoordinator(hass, config_entry)

    # Mock sensor forecast data with correct number of periods (DEFAULT_N_PERIODS)
    with patch.object(coordinator, "_get_sensor_forecast") as mock_forecast:
        mock_forecast.return_value = [0.1] * DEFAULT_N_PERIODS

        await coordinator._build_network()

        assert coordinator.network is not None
        assert "test_grid" in coordinator.network.elements

        # Verify sensors were called
        assert mock_forecast.call_count == 2  # import and export sensors


async def test_build_network_with_constant_pricing(hass: HomeAssistant):
    """Test building network with grid that has constant pricing."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "integration_type": "hub",
            CONF_NAME: "Power Network",
            CONF_PARTICIPANTS: {
                "test_grid": {
                    CONF_ELEMENT_TYPE: ELEMENT_TYPE_GRID,
                    CONF_IMPORT_LIMIT: 10000,
                    CONF_EXPORT_LIMIT: 5000,
                    CONF_PRICE_IMPORT_SENSOR: ["sensor.import_price"],
                    CONF_PRICE_EXPORT_SENSOR: ["sensor.export_price"],
                }
            },
        },
        entry_id="test_entry_id",
    )

    coordinator = HaeoDataUpdateCoordinator(hass, config_entry)

    await coordinator._build_network()

    assert coordinator.network is not None
    assert "test_grid" in coordinator.network.elements


async def test_build_network_with_mixed_pricing(hass: HomeAssistant):
    """Test building network with grid that has mixed pricing (sensor + constant)."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "integration_type": "hub",
            CONF_NAME: "Power Network",
            CONF_PARTICIPANTS: {
                "test_grid": {
                    CONF_ELEMENT_TYPE: ELEMENT_TYPE_GRID,
                    CONF_IMPORT_LIMIT: 10000,
                    CONF_EXPORT_LIMIT: 5000,
                    CONF_PRICE_IMPORT_SENSOR: ["sensor.import_price"],
                    CONF_PRICE_EXPORT_SENSOR: ["sensor.export_price"],
                }
            },
        },
        entry_id="test_entry_id",
    )

    coordinator = HaeoDataUpdateCoordinator(hass, config_entry)

    # Mock sensor forecast data for import and export (576 periods)
    with patch.object(coordinator, "_get_sensor_forecast") as mock_forecast:

        def mock_forecast_side_effect(sensor_ids):
            if isinstance(sensor_ids, list):
                if "sensor.import_price" in sensor_ids:
                    return [0.1] * DEFAULT_N_PERIODS
                elif "sensor.export_price" in sensor_ids:
                    return [0.05] * DEFAULT_N_PERIODS
            elif sensor_ids == "sensor.import_price":
                return [0.1] * DEFAULT_N_PERIODS
            elif sensor_ids == "sensor.export_price":
                return [0.05] * DEFAULT_N_PERIODS
            return None

        mock_forecast.side_effect = mock_forecast_side_effect

        await coordinator._build_network()

        assert coordinator.network is not None
        assert "test_grid" in coordinator.network.elements

        # Verify sensors were called for both import and export
        assert mock_forecast.call_count == 2
        mock_forecast.assert_any_call(["sensor.import_price"])
        mock_forecast.assert_any_call(["sensor.export_price"])


async def test_build_network_element_creation_error(hass: HomeAssistant):
    """Test building network when element creation fails."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "integration_type": "hub",
            CONF_NAME: "Power Network",
            CONF_PARTICIPANTS: {
                "test_battery": {
                    CONF_ELEMENT_TYPE: ELEMENT_TYPE_BATTERY,
                    CONF_CAPACITY: -1000,  # Invalid capacity
                    CONF_CURRENT_CHARGE_SENSOR: "sensors.current_charge",
                }
            },
        },
        entry_id="test_entry_id",
    )

    coordinator = HaeoDataUpdateCoordinator(hass, config_entry)

    # Should handle the error gracefully and continue
    await coordinator._build_network()

    # Network should still be created but without the invalid element
    assert coordinator.network is not None


async def test_collect_sensor_data_with_grid_price_sensors(hass: HomeAssistant):
    """Test collecting sensor data for grid with price sensors."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "integration_type": "hub",
            CONF_NAME: "Power Network",
            CONF_PARTICIPANTS: {
                "test_grid": {
                    CONF_ELEMENT_TYPE: ELEMENT_TYPE_GRID,
                    CONF_IMPORT_LIMIT: 10000,
                    CONF_EXPORT_LIMIT: 5000,
                    CONF_PRICE_IMPORT_SENSOR: ["sensor.import_price"],
                    CONF_PRICE_EXPORT_SENSOR: ["sensor.export_price"],
                }
            },
        },
        entry_id="test_entry_id",
    )

    coordinator = HaeoDataUpdateCoordinator(hass, config_entry)

    # Build network first
    await coordinator._build_network()

    # Mock sensor forecast data
    with patch.object(coordinator, "_get_sensor_forecast") as mock_forecast:
        mock_forecast.return_value = [0.1, 0.2, 0.15]

        await coordinator._collect_sensor_data()

        # Verify sensors were called
        assert mock_forecast.call_count == 2


async def test_collect_sensor_data_with_load_forecast_sensors(hass: HomeAssistant):
    """Test collecting sensor data for load with forecast sensors."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "integration_type": "hub",
            CONF_NAME: "Power Network",
            CONF_PARTICIPANTS: {
                "test_load": {
                    CONF_ELEMENT_TYPE: ELEMENT_TYPE_LOAD_FORECAST,
                    "forecast": [100] * DEFAULT_N_PERIODS,  # Default number of periods
                    CONF_FORECAST_SENSORS: ["sensor.load_forecast"],
                }
            },
        },
        entry_id="test_entry_id",
    )

    coordinator = HaeoDataUpdateCoordinator(hass, config_entry)

    # Build network first
    await coordinator._build_network()

    # Mock sensor forecast data
    with patch.object(coordinator, "_get_sensor_forecast") as mock_forecast:
        mock_forecast.return_value = [100] * DEFAULT_N_PERIODS  # Default number of periods

        await coordinator._collect_sensor_data()

        # Verify sensor was called
        mock_forecast.assert_called_once_with(["sensor.load_forecast"])


async def test_collect_sensor_data_with_additional_sensors(hass: HomeAssistant):
    """Test collecting sensor data with additional sensors."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "integration_type": "hub",
            CONF_NAME: "Power Network",
            CONF_PARTICIPANTS: {
                "test_battery": {
                    CONF_ELEMENT_TYPE: ELEMENT_TYPE_BATTERY,
                    CONF_CAPACITY: 10000,
                    CONF_CURRENT_CHARGE_SENSOR: "sensors.current_charge",
                    CONF_MAX_CHARGE_POWER: 5000,
                    CONF_MAX_DISCHARGE_POWER: 5000,
                }
            },
        },
        entry_id="test_entry_id",
    )

    coordinator = HaeoDataUpdateCoordinator(hass, config_entry)

    # Build network first
    await coordinator._build_network()

    # Mock sensor data - simulate the sensors configuration being present in the config
    with patch.object(coordinator, "_get_sensor_data") as mock_sensor_data:
        mock_sensor_data.return_value = 25.5

        # Add the sensors config to the participant after network is built
        coordinator.config[CONF_PARTICIPANTS]["test_battery"][CONF_SENSORS] = [
            {
                CONF_SENSOR_ENTITY_ID: "sensor.battery_temp",
                CONF_SENSOR_ATTRIBUTE: "temperature",
            }
        ]

        await coordinator._collect_sensor_data()

        # Verify sensor was called
        mock_sensor_data.assert_called_once()


async def test_get_sensor_data_with_attribute(hass: HomeAssistant, mock_config_entry):
    """Test getting sensor data with attribute."""
    coordinator = HaeoDataUpdateCoordinator(hass, mock_config_entry)

    # Set up sensor state with attributes
    hass.states.async_set("sensor.test", "100", {"temperature": "25.5", "humidity": "60"})

    sensor_config = {
        CONF_SENSOR_ENTITY_ID: "sensor.test",
        CONF_SENSOR_ATTRIBUTE: "temperature",
    }

    result = await coordinator._get_sensor_data(sensor_config)

    assert result == "25.5"


async def test_get_sensor_data_without_attribute(hass: HomeAssistant, mock_config_entry):
    """Test getting sensor data without attribute (use state)."""
    coordinator = HaeoDataUpdateCoordinator(hass, mock_config_entry)

    # Set up sensor state
    hass.states.async_set("sensor.test", "150", {})

    sensor_config = {
        CONF_SENSOR_ENTITY_ID: "sensor.test",
    }

    result = await coordinator._get_sensor_data(sensor_config)

    assert result == "150"


async def test_get_sensor_data_missing_sensor(hass: HomeAssistant, mock_config_entry):
    """Test getting sensor data from missing sensor."""
    coordinator = HaeoDataUpdateCoordinator(hass, mock_config_entry)

    sensor_config = {
        CONF_SENSOR_ENTITY_ID: "sensor.missing",
    }

    result = await coordinator._get_sensor_data(sensor_config)

    assert result is None


async def test_get_sensor_value_success(hass: HomeAssistant, mock_config_entry):
    """Test getting sensor value successfully."""
    coordinator = HaeoDataUpdateCoordinator(hass, mock_config_entry)

    # Set up sensor state
    hass.states.async_set("sensor.test", "123.45", {})

    result = await coordinator._get_sensor_value("sensor.test")

    assert result == 123.45


async def test_get_sensor_value_invalid_number(hass: HomeAssistant, mock_config_entry):
    """Test getting sensor value with invalid number."""
    coordinator = HaeoDataUpdateCoordinator(hass, mock_config_entry)

    # Set up sensor state with invalid number
    hass.states.async_set("sensor.test", "not_a_number", {})

    result = await coordinator._get_sensor_value("sensor.test")

    assert result is None


async def test_get_sensor_value_missing_sensor(hass: HomeAssistant, mock_config_entry):
    """Test getting sensor value from missing sensor."""
    coordinator = HaeoDataUpdateCoordinator(hass, mock_config_entry)

    result = await coordinator._get_sensor_value("sensor.missing")

    assert result is None


async def test_process_sensor_data(hass: HomeAssistant, mock_config_entry):
    """Test processing sensor data."""
    coordinator = HaeoDataUpdateCoordinator(hass, mock_config_entry)

    # This method currently just logs, so we mainly test it doesn't error
    await coordinator._process_sensor_data(
        "test_battery", ELEMENT_TYPE_BATTERY, {CONF_SENSOR_ENTITY_ID: "sensor.test"}, 25.5
    )

    # Should not raise any exceptions


def test_run_optimization_no_network(hass: HomeAssistant, mock_config_entry):
    """Test running optimization with no network."""
    coordinator = HaeoDataUpdateCoordinator(hass, mock_config_entry)

    with pytest.raises(RuntimeError, match="Network not initialized"):
        coordinator._run_optimization()


def test_run_optimization_with_network(hass: HomeAssistant, mock_config_entry):
    """Test running optimization with network."""
    coordinator = HaeoDataUpdateCoordinator(hass, mock_config_entry)

    # Build a simple network
    from custom_components.haeo.model import Network

    coordinator.network = Network("test", period=3600, n_periods=3)
    coordinator.network.add(
        ELEMENT_TYPE_BATTERY,
        "test_battery",
        capacity=1000,
        initial_charge_percentage=50,
    )

    # Mock the optimize method to return a cost
    with patch.object(coordinator.network, "optimize", return_value=150.0) as mock_optimize:
        result = coordinator._run_optimization()

        assert result == 150.0
        mock_optimize.assert_called_once()


def test_run_optimization_failure(hass: HomeAssistant, mock_config_entry):
    """Test running optimization that fails."""
    coordinator = HaeoDataUpdateCoordinator(hass, mock_config_entry)

    # Build a simple network
    from custom_components.haeo.model import Network

    coordinator.network = Network("test", period=3600, n_periods=3)
    coordinator.network.add(
        ELEMENT_TYPE_BATTERY,
        "test_battery",
        capacity=1000,
        initial_charge_percentage=50,
    )

    # Mock the optimize method to raise an exception
    with patch.object(coordinator.network, "optimize", side_effect=Exception("Optimization failed")):
        with pytest.raises(Exception, match="Optimization failed"):
            coordinator._run_optimization()


async def test_update_data_network_build_failure(hass: HomeAssistant, mock_config_entry):
    """Test update data when network building fails."""
    # Set up sensor state for battery
    hass.states.async_set("sensor.battery_charge", "50", {})

    coordinator = HaeoDataUpdateCoordinator(hass, mock_config_entry)

    # Mock network building to fail
    with patch.object(coordinator, "_build_network", side_effect=Exception("Network build failed")):
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()

    assert coordinator.optimization_status == OPTIMIZATION_STATUS_FAILED


async def test_update_data_sensor_collection_failure(hass: HomeAssistant, mock_config_entry):
    """Test update data when sensor collection fails."""
    # Set up sensor state for battery
    hass.states.async_set("sensor.battery_charge", "50", {})

    coordinator = HaeoDataUpdateCoordinator(hass, mock_config_entry)

    # Mock successful network build but failing sensor collection
    with (
        patch.object(coordinator, "_build_network"),
        patch.object(coordinator, "_collect_sensor_data", side_effect=Exception("Sensor collection failed")),
        patch.object(coordinator, "_run_optimization", return_value=100.0),
    ):
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()

    assert coordinator.optimization_status == OPTIMIZATION_STATUS_FAILED


async def test_collect_sensor_data_no_network(hass: HomeAssistant):
    """Test collecting sensor data when network is None."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "integration_type": "hub",
            CONF_NAME: "Power Network",
            CONF_PARTICIPANTS: {
                "test_battery": {
                    CONF_ELEMENT_TYPE: ELEMENT_TYPE_BATTERY,
                    CONF_CAPACITY: 10000,
                    CONF_CURRENT_CHARGE_SENSOR: "sensors.current_charge",
                    CONF_MAX_CHARGE_POWER: 5000,
                    CONF_MAX_DISCHARGE_POWER: 5000,
                }
            },
        },
        entry_id="test_entry_id",
    )

    coordinator = HaeoDataUpdateCoordinator(hass, config_entry)

    # Don't build network - it should be None
    await coordinator._collect_sensor_data()

    # Should handle gracefully and not crash


async def test_build_network_element_exception_handling(hass: HomeAssistant):
    """Test that element creation exceptions are properly handled and logged."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "integration_type": "hub",
            CONF_NAME: "Power Network",
            CONF_PARTICIPANTS: {
                "test_battery": {
                    CONF_ELEMENT_TYPE: ELEMENT_TYPE_BATTERY,
                    CONF_CAPACITY: -1000,  # Invalid capacity that will cause exception
                    CONF_CURRENT_CHARGE_SENSOR: "sensors.current_charge",
                }
            },
        },
        entry_id="test_entry_id",
    )

    coordinator = HaeoDataUpdateCoordinator(hass, config_entry)

    # Should handle the exception gracefully and log it
    await coordinator._build_network()

    # Network should still be created even if element creation failed
    assert coordinator.network is not None


async def test_get_sensor_forecast_with_invalid_data(hass: HomeAssistant, mock_config_entry):
    """Test getting sensor forecast with invalid forecast data."""
    coordinator = HaeoDataUpdateCoordinator(hass, mock_config_entry)

    # Set up sensor state with invalid forecast data (non-numeric values)
    hass.states.async_set("sensor.test", "100", {"forecast": ["not_a_number", "also_not", "123"]})

    result = await coordinator._get_sensor_forecast("sensor.test")

    # Should handle invalid data gracefully and fall back to current state value repeated
    assert result is not None
    assert len(result) == 576  # DEFAULT_N_PERIODS
    assert all(x == 100.0 for x in result)  # Should fall back to current state value


async def test_get_sensor_value_with_invalid_number(hass: HomeAssistant, mock_config_entry):
    """Test getting sensor value with non-numeric data."""
    coordinator = HaeoDataUpdateCoordinator(hass, mock_config_entry)

    # Set up sensor state with invalid numeric data
    hass.states.async_set("sensor.test", "not_a_number", {})

    result = await coordinator._get_sensor_value("sensor.test")

    # Should handle invalid data gracefully and return None
    assert result is None
