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
    CONF_EXPORT_LIMIT,
    CONF_HORIZON_HOURS,
    CONF_IMPORT_LIMIT,
    CONF_MAX_POWER,
    CONF_PARTICIPANTS,
    CONF_PERIOD_MINUTES,
    DOMAIN,
    ELEMENT_TYPE_BATTERY,
    ELEMENT_TYPE_CONNECTION,
    ELEMENT_TYPE_GRID,
    OPTIMIZATION_STATUS_SUCCESS,
    OPTIMIZATION_STATUS_FAILED,
    ATTR_POWER,
    ATTR_ENERGY,
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
            CONF_HORIZON_HOURS: 48,
            CONF_PERIOD_MINUTES: 5,
            CONF_PARTICIPANTS: {
                "test_battery": {
                    CONF_ELEMENT_TYPE: ELEMENT_TYPE_BATTERY,
                    CONF_CAPACITY: 10000,
                    "current_charge": "sensor.battery_charge",
                },
                "test_grid": {
                    CONF_ELEMENT_TYPE: ELEMENT_TYPE_GRID,
                    CONF_IMPORT_LIMIT: 10000,
                    CONF_EXPORT_LIMIT: 5000,
                    # For tests, use constant pricing to avoid sensor setup complexity
                    "import_price": [0.1] * 576,  # 48 hours in 5-minute steps
                    "export_price": [0.05] * 576,  # 48 hours in 5-minute steps
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


@patch("custom_components.haeo.model.network.Network.optimize")
async def test_update_data_success(mock_optimize, hass: HomeAssistant, mock_config_entry):
    """Test successful data update."""
    # Set up sensor state for battery sensor
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


@patch("custom_components.haeo.model.network.Network.optimize")
async def test_update_data_failure(mock_optimize, hass: HomeAssistant, mock_config_entry):
    """Test failed data update."""
    # Set up sensor states for battery and grid
    hass.states.async_set("sensor.battery_charge", "50", {})
    hass.states.async_set("sensor.import_price", "0.10", {"forecast": [0.10] * 576})
    hass.states.async_set("sensor.export_price", "0.05", {"forecast": [0.05] * 576})

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

    # Create a network for the coordinator
    from custom_components.haeo.model import Network

    coordinator.network = Network("test", period=300, n_periods=576)

    # Set optimization result with timestamp
    test_time = datetime.now()
    coordinator.optimization_result = {
        "cost": 150.0,
        "timestamp": test_time,
    }

    result = coordinator.get_future_timestamps()

    assert len(result) == 576  # 48 hours in 5-minute steps
    # Check that timestamps are ISO format strings
    for timestamp in result:
        assert isinstance(timestamp, str)
        # Should be able to parse as datetime
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))


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


async def test_update_data_network_build_failure(hass: HomeAssistant, mock_config_entry):
    """Test update data when network building fails."""
    # Set up sensor state for battery
    hass.states.async_set("sensor.battery_charge", "50", {})

    coordinator = HaeoDataUpdateCoordinator(hass, mock_config_entry)

    # Mock failing network build (which now includes sensor data loading)
    with (
        patch.object(coordinator.data_loader, "load_network_data", side_effect=Exception("Network build failed")),
        patch("custom_components.haeo.model.network.Network.optimize", return_value=100.0),
    ):
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()

    assert coordinator.optimization_status == OPTIMIZATION_STATUS_FAILED
