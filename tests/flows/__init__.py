"""Test utilities for HAEO flow tests."""

from __future__ import annotations

import pytest
from typing import Any, Dict, List, Tuple, Callable
from unittest.mock import patch

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.const import CONF_NAME
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.haeo.const import (
    DOMAIN,
    ENTITY_TYPE_BATTERY,
    ENTITY_TYPE_GRID,
    ENTITY_TYPE_LOAD,
    ENTITY_TYPE_GENERATOR,
    ENTITY_TYPE_NET,
)


def create_mock_config_entry(
    title: str = "Power Network",
    data: dict[str, Any] | None = None,
    entry_id: str = "test_entry_id",
) -> MockConfigEntry:
    """Create a mock config entry for testing."""
    if data is None:
        data = {
            "integration_type": "hub",
            "name": title,
            "participants": {},
        }

    return MockConfigEntry(
        domain=DOMAIN,
        title=title,
        data=data,
        entry_id=entry_id,
    )


async def setup_config_entry(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    """Set up a config entry for testing."""
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def unload_config_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Unload a config entry after testing."""
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


def get_valid_test_data() -> Dict[str, Dict[str, Any]]:
    """Get valid test data for all entity types."""
    # Import from individual test files to avoid duplication
    from tests.flows.test_battery import BATTERY_VALID_DATA
    from tests.flows.test_grid import GRID_VALID_DATA
    from tests.flows.test_load import LOAD_VALID_DATA
    from tests.flows.test_generator import GENERATOR_VALID_DATA
    from tests.flows.test_net import NET_VALID_DATA
    from tests.flows.test_connection import CONNECTION_VALID_DATA

    return {
        ENTITY_TYPE_BATTERY: BATTERY_VALID_DATA,
        ENTITY_TYPE_GRID: GRID_VALID_DATA,
        ENTITY_TYPE_LOAD: LOAD_VALID_DATA,
        ENTITY_TYPE_GENERATOR: GENERATOR_VALID_DATA,
        ENTITY_TYPE_NET: NET_VALID_DATA,
        "connection": CONNECTION_VALID_DATA,
    }


def get_invalid_test_data() -> Dict[str, List[Tuple[Dict[str, Any], str]]]:
    """Get invalid test data for validation testing."""
    # Import from individual test files to avoid duplication
    from tests.flows.test_battery import BATTERY_INVALID_DATA
    from tests.flows.test_grid import GRID_INVALID_DATA
    from tests.flows.test_load import LOAD_INVALID_DATA
    from tests.flows.test_generator import GENERATOR_INVALID_DATA
    from tests.flows.test_net import NET_INVALID_DATA
    from tests.flows.test_connection import CONNECTION_INVALID_DATA

    return {
        ENTITY_TYPE_BATTERY: BATTERY_INVALID_DATA,
        ENTITY_TYPE_GRID: GRID_INVALID_DATA,
        ENTITY_TYPE_LOAD: LOAD_INVALID_DATA,
        ENTITY_TYPE_GENERATOR: GENERATOR_INVALID_DATA,
        ENTITY_TYPE_NET: NET_INVALID_DATA,
        "connection": CONNECTION_INVALID_DATA,
    }
