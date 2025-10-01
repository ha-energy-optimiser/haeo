"""Test the HAEO integration."""

import pytest
from unittest.mock import AsyncMock, patch
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.haeo import async_setup_entry, async_unload_entry, async_reload_entry
from custom_components.haeo.const import (
    CONF_CAPACITY,
    CONF_CURRENT_CHARGE_SENSOR,
    CONF_ELEMENT_TYPE,
    CONF_EXPORT_LIMIT,
    CONF_IMPORT_LIMIT,
    CONF_MAX_POWER,
    CONF_PARTICIPANTS,
    CONF_PRICE_EXPORT_SENSOR,
    CONF_PRICE_IMPORT_SENSOR,
    CONF_SOURCE,
    CONF_TARGET,
    DOMAIN,
    ELEMENT_TYPE_BATTERY,
    ELEMENT_TYPE_GRID,
    ELEMENT_TYPE_CONNECTION,
)


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            "integration_type": "hub",
            "name": "Test Network",
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
                    CONF_PRICE_IMPORT_SENSOR: "sensor.import_price",
                    CONF_PRICE_EXPORT_SENSOR: "sensor.export_price",
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
        title="Test HAEO Integration",
    )


async def test_setup_entry(hass: HomeAssistant, mock_config_entry):
    """Test setting up the integration."""
    mock_config_entry.add_to_hass(hass)

    # Set up sensor state for battery
    hass.states.async_set("sensor.battery_charge", "50", {})

    with patch("custom_components.haeo.coordinator.HaeoDataUpdateCoordinator") as mock_coordinator:
        # Mock the coordinator to avoid complex setup
        mock_instance = AsyncMock()
        mock_coordinator.return_value = mock_instance

        result = await async_setup_entry(hass, mock_config_entry)

        assert result is True
        assert mock_config_entry.runtime_data is not None
        mock_coordinator.assert_called_once()


async def test_unload_entry(hass: HomeAssistant, mock_config_entry):
    """Test unloading the integration."""
    mock_config_entry.add_to_hass(hass)

    # Set up sensor state for battery
    hass.states.async_set("sensor.battery_charge", "50", {})

    with patch("custom_components.haeo.coordinator.HaeoDataUpdateCoordinator") as mock_coordinator:
        # Set up the integration first
        mock_instance = AsyncMock()
        mock_coordinator.return_value = mock_instance

        await async_setup_entry(hass, mock_config_entry)

        # Now test unloading
        with patch("homeassistant.config_entries.async_unload_platforms", return_value=True) as mock_unload:
            result = await async_unload_entry(hass, mock_config_entry)

            assert result is True
            mock_unload.assert_called_once()


async def test_setup_entry_failure(hass: HomeAssistant, mock_config_entry):
    """Test setup entry failure."""
    mock_config_entry.add_to_hass(hass)

    # Set up sensor state for battery
    hass.states.async_set("sensor.battery_charge", "50", {})

    with patch("custom_components.haeo.coordinator.HaeoDataUpdateCoordinator") as mock_coordinator:
        # Mock coordinator to raise exception
        mock_coordinator.side_effect = Exception("Test error")

        with pytest.raises(Exception):
            await async_setup_entry(hass, mock_config_entry)


async def test_reload_entry(hass: HomeAssistant, mock_config_entry):
    """Test reloading the integration."""
    mock_config_entry.add_to_hass(hass)

    # Set up sensor state for battery
    hass.states.async_set("sensor.battery_charge", "50", {})

    with patch("custom_components.haeo.coordinator.HaeoDataUpdateCoordinator") as mock_coordinator:
        # Set up the integration first
        mock_instance = AsyncMock()
        mock_coordinator.return_value = mock_instance

        await async_setup_entry(hass, mock_config_entry)

        # Now test reloading
        with patch("homeassistant.config_entries.async_unload_platforms", return_value=True):
            await async_reload_entry(hass, mock_config_entry)

            # Verify the integration was reloaded (coordinator should be recreated)
            assert mock_config_entry.runtime_data is not None
