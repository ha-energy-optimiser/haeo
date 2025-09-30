"""Test the HAEO integration."""

import pytest
from unittest.mock import patch
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.haeo import async_setup_entry, async_unload_entry
from custom_components.haeo.const import (
    DOMAIN,
    CONF_ENTITIES,
    CONF_CONNECTIONS,
    CONF_ENTITY_TYPE,
    CONF_ENTITY_CONFIG,
)


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_ENTITIES: [
                {
                    CONF_NAME: "test_battery",
                    CONF_ENTITY_TYPE: "battery",
                    CONF_ENTITY_CONFIG: {
                        "capacity": 10000,
                        "initial_charge_percentage": 50,
                    },
                },
                {
                    CONF_NAME: "test_grid",
                    CONF_ENTITY_TYPE: "grid",
                    CONF_ENTITY_CONFIG: {
                        "import_limit": 10000,
                        "export_limit": 5000,
                        "price_import": [0.1, 0.2, 0.15],
                        "price_export": [0.05, 0.08, 0.06],
                    },
                },
            ],
            CONF_CONNECTIONS: [
                {
                    "source": "test_battery",
                    "target": "test_grid",
                    "max_power": 5000,
                }
            ],
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
