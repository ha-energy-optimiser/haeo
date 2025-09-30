"""Test configuration and fixtures."""

import pytest
from unittest.mock import MagicMock

from custom_components.haeo.const import ENTITY_TYPE_BATTERY, ENTITY_TYPE_GRID

# Enable custom component for testing
pytest_plugins = ["pytest_homeassistant_custom_component"]


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading custom integrations in all tests."""
    yield


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = MagicMock()
    hass.data = {}
    hass.states = MagicMock()
    hass.config_entries = MagicMock()
    return hass


@pytest.fixture
def simple_config_entry_data():
    """Create simple config entry data for testing."""
    return {
        "entities": [
            {
                "name": "test_battery",
                "entity_type": ENTITY_TYPE_BATTERY,
                "config": {
                    "capacity": 10000,
                    "initial_charge_percentage": 50,
                },
            },
            {
                "name": "test_grid",
                "entity_type": ENTITY_TYPE_GRID,
                "config": {
                    "import_limit": 10000,
                    "export_limit": 5000,
                },
            },
        ],
        "connections": [
            {
                "source": "test_battery",
                "target": "test_grid",
            }
        ],
    }
