"""Test configuration and fixtures."""

import pytest

from custom_components.haeo.const import (
    DOMAIN,
    ELEMENT_TYPE_BATTERY,
    ELEMENT_TYPE_GRID,
)

# Enable custom component for testing
pytest_plugins = ["pytest_homeassistant_custom_component"]


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading custom integrations in all tests."""
    yield


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry for testing."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    return MockConfigEntry(
        title="Test HAEO",
        domain=DOMAIN,
        entry_id="test_entry_id",
        data={
            "participants": {
                "test_battery": {
                    "type": ELEMENT_TYPE_BATTERY,
                    "capacity": 10000,
                    "initial_charge_percentage": 50,
                    "max_charge_power": 5000,
                    "max_discharge_power": 5000,
                },
                "test_grid": {
                    "type": ELEMENT_TYPE_GRID,
                    "import_limit": 10000,
                    "export_limit": 5000,
                    "price_import": [0.1, 0.2, 0.15],
                    "price_export": [0.05, 0.08, 0.06],
                },
            },
        },
    )
