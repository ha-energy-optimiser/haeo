"""Test the HAEO coordinator."""

import pytest
from unittest.mock import patch
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.haeo.coordinator import HaeoDataUpdateCoordinator
from custom_components.haeo.const import (
    DOMAIN,
    CONF_ENTITIES,
    CONF_CONNECTIONS,
    CONF_ENTITY_TYPE,
    CONF_ENTITY_CONFIG,
    OPTIMIZATION_STATUS_SUCCESS,
    OPTIMIZATION_STATUS_FAILED,
)


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_ENTITIES: [
                {
                    "name": "test_battery",
                    CONF_ENTITY_TYPE: "battery",
                    CONF_ENTITY_CONFIG: {
                        "capacity": 10000,
                        "initial_charge_percentage": 50,
                    },
                },
                {
                    "name": "test_grid",
                    CONF_ENTITY_TYPE: "grid",
                    CONF_ENTITY_CONFIG: {
                        "import_limit": 10000,
                        "export_limit": 5000,
                        "price_import": [0.1] * 24,
                        "price_export": [0.05] * 24,
                    },
                },
            ],
            CONF_CONNECTIONS: [
                {
                    "source": "test_battery",
                    "target": "test_grid",
                }
            ],
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
    coordinator = HaeoDataUpdateCoordinator(hass, mock_config_entry)

    await coordinator._build_network()

    assert coordinator.network is not None
    assert "test_battery" in coordinator.network.entities
    assert "test_grid" in coordinator.network.entities
    assert len(coordinator.network.connections) == 1


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
    assert len(result) == 24  # DEFAULT_N_PERIODS
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


@patch("custom_components.haeo.coordinator.HaeoDataUpdateCoordinator._run_optimization")
async def test_update_data_failure(mock_optimize, hass: HomeAssistant, mock_config_entry):
    """Test failed data update."""
    coordinator = HaeoDataUpdateCoordinator(hass, mock_config_entry)

    # Mock optimization failure
    mock_optimize.side_effect = Exception("Optimization failed")

    with patch.object(hass, "async_add_executor_job", side_effect=Exception("Optimization failed")):
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()

    assert coordinator.optimization_status == OPTIMIZATION_STATUS_FAILED


def test_get_entity_data(hass: HomeAssistant, mock_config_entry):
    """Test getting entity data."""
    coordinator = HaeoDataUpdateCoordinator(hass, mock_config_entry)

    # Build a network with entities
    from custom_components.haeo.model import Network

    coordinator.network = Network("test", period=3600, n_periods=3)
    coordinator.network.add(
        "battery",
        "test_battery",
        capacity=1000,
        initial_charge_percentage=50,
        max_charge_power=100,
        max_discharge_power=100,
    )

    # Run a simple optimization to set variable values
    coordinator.network.optimize()

    result = coordinator.get_entity_data("test_battery")

    assert result is not None
    assert "power_consumption" in result
    assert "power_production" in result
    assert "energy" in result
    assert len(result["power_consumption"]) == 3
    assert len(result["power_production"]) == 3
    assert len(result["energy"]) == 3


def test_get_entity_data_no_result(hass: HomeAssistant, mock_config_entry):
    """Test getting entity data with no optimization result."""
    coordinator = HaeoDataUpdateCoordinator(hass, mock_config_entry)

    result = coordinator.get_entity_data("test_battery")

    assert result is None


def test_get_connection_data(hass: HomeAssistant, mock_config_entry):
    """Test getting connection data."""
    coordinator = HaeoDataUpdateCoordinator(hass, mock_config_entry)

    # Build a network with entities and connections
    from custom_components.haeo.model import Network

    coordinator.network = Network("test", period=3600, n_periods=3)
    coordinator.network.add(
        "battery",
        "test_battery",
        capacity=1000,
        initial_charge_percentage=50,
        max_charge_power=100,
        max_discharge_power=100,
    )
    coordinator.network.add(
        "grid", "test_grid", import_limit=1000, export_limit=1000, price_import=[0.1] * 3, price_export=[0.05] * 3
    )

    # Connect the entities
    coordinator.network.connect("test_battery", "test_grid")

    # Run optimization to set variable values
    coordinator.network.optimize()

    result = coordinator.get_connection_data("test_battery", "test_grid")

    assert result is not None
    assert len(result) == 3
    # Verify we get numeric values (optimization results may vary based on solver)
    assert all(isinstance(val, (int, float)) for val in result)
    assert all(val >= 0 for val in result)  # Power values should be non-negative


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
