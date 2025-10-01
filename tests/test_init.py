"""Test the HAEO integration."""

import pytest
from unittest.mock import patch
from homeassistant.config_entries import ConfigEntry
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


async def test_setup_entry(hass: HomeAssistant, mock_config_entry: ConfigEntry):
    """Test setting up the integration."""
    with (
        patch("custom_components.haeo.coordinator.HaeoDataUpdateCoordinator.async_config_entry_first_refresh"),
        patch("homeassistant.config_entries.ConfigEntries.async_forward_entry_setups"),
    ):
        result = await async_setup_entry(hass, mock_config_entry)

        assert result is True
        assert mock_config_entry.runtime_data is not None


async def test_unload_entry(hass: HomeAssistant, mock_config_entry: ConfigEntry):
    """Test unloading the integration."""
    # First set up the integration
    with (
        patch("custom_components.haeo.coordinator.HaeoDataUpdateCoordinator.async_config_entry_first_refresh"),
        patch("homeassistant.config_entries.ConfigEntries.async_forward_entry_setups"),
        patch("homeassistant.config_entries.ConfigEntries.async_unload_platforms", return_value=True),
    ):
        await async_setup_entry(hass, mock_config_entry)

        # Now test unloading
        result = await async_unload_entry(hass, mock_config_entry)

        assert result is True


async def test_setup_entry_failure(hass: HomeAssistant, mock_config_entry: ConfigEntry):
    """Test setup entry failure."""
    with patch(
        "custom_components.haeo.coordinator.HaeoDataUpdateCoordinator.async_config_entry_first_refresh",
        side_effect=Exception("Test error"),
    ):
        with pytest.raises(Exception):
            await async_setup_entry(hass, mock_config_entry)


async def test_reload_entry(hass: HomeAssistant, mock_config_entry: ConfigEntry):
    """Test reloading the integration."""
    with (
        patch("custom_components.haeo.coordinator.HaeoDataUpdateCoordinator.async_config_entry_first_refresh"),
        patch("homeassistant.config_entries.ConfigEntries.async_forward_entry_setups"),
        patch("homeassistant.config_entries.ConfigEntries.async_unload_platforms", return_value=True),
    ):
        # First set up the integration
        await async_setup_entry(hass, mock_config_entry)

        # Now test reloading
        await async_reload_entry(hass, mock_config_entry)

        # Verify the integration was reloaded (coordinator should be recreated)
        assert mock_config_entry.runtime_data is not None
