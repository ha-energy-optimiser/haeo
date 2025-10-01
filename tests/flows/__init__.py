"""Test utilities for HAEO flow tests."""

from __future__ import annotations

import pytest
from typing import Any, Dict, List, Tuple, Callable
from unittest.mock import patch

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.haeo.const import (
    DOMAIN,
    ELEMENT_TYPE_BATTERY,
    ELEMENT_TYPE_CONNECTION,
    ELEMENT_TYPE_GRID,
    ELEMENT_TYPE_LOAD_FIXED,
    ELEMENT_TYPE_LOAD_FORECAST,
    ELEMENT_TYPE_GENERATOR,
    ELEMENT_TYPE_NET,
    ELEMENT_TYPES,
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
    """Get valid test data for all element types."""
    # Import from individual test files to avoid duplication
    from tests.flows.test_battery import BATTERY_VALID_DATA
    from tests.flows.test_grid import GRID_VALID_DATA
    from tests.flows.test_load import LOAD_VALID_DATA, LOAD_VARIABLE_DATA
    from tests.flows.test_generator import GENERATOR_VALID_DATA
    from tests.flows.test_net import NET_VALID_DATA
    from tests.flows.test_connection import CONNECTION_VALID_DATA

    return {
        ELEMENT_TYPE_BATTERY: BATTERY_VALID_DATA,
        ELEMENT_TYPE_GRID: GRID_VALID_DATA,
        ELEMENT_TYPE_LOAD: LOAD_VALID_DATA,
        ELEMENT_TYPE_LOAD_FIXED: LOAD_VALID_DATA,
        ELEMENT_TYPE_LOAD_FORECAST: LOAD_VARIABLE_DATA,
        ELEMENT_TYPE_GENERATOR: GENERATOR_VALID_DATA,
        ELEMENT_TYPE_NET: NET_VALID_DATA,
        ELEMENT_TYPE_CONNECTION: CONNECTION_VALID_DATA,
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
        ELEMENT_TYPE_BATTERY: BATTERY_INVALID_DATA,
        ELEMENT_TYPE_GRID: GRID_INVALID_DATA,
        ELEMENT_TYPE_LOAD: LOAD_INVALID_DATA,
        ELEMENT_TYPE_LOAD_FIXED: LOAD_INVALID_DATA,
        ELEMENT_TYPE_LOAD_FORECAST: LOAD_INVALID_DATA,
        ELEMENT_TYPE_GENERATOR: GENERATOR_INVALID_DATA,
        ELEMENT_TYPE_NET: NET_INVALID_DATA,
        ELEMENT_TYPE_CONNECTION: CONNECTION_INVALID_DATA,
    }


# Pytest fixtures for data-driven testing
@pytest.fixture(params=ELEMENT_TYPES)
def element_type(request):
    """Parametrized fixture for element types."""
    return request.param


@pytest.fixture
def valid_element_data(element_type):
    """Fixture providing valid data for each element type."""
    return get_valid_test_data()[element_type]


@pytest.fixture
def config_entry_with_existing_participant(element_type, valid_element_data):
    """Fixture providing config entry with existing participant."""
    existing_name = valid_element_data[CONF_NAME]
    participants = {
        existing_name: {"type": element_type, **{k: v for k, v in valid_element_data.items() if k != CONF_NAME}}
    }

    return create_mock_config_entry(
        data={
            "integration_type": "hub",
            "name": "Power Network",
            "participants": participants,
        }
    )


async def test_element_duplicate_name_handling(
    hass: HomeAssistant,
    flow_class: type,
    element_type: str,
    test_data: Dict[str, Any],
    config_entry_with_existing: MockConfigEntry,
) -> None:
    """Generic test for duplicate name handling."""
    flow = flow_class()
    flow.hass = hass
    flow._config_entry = config_entry_with_existing

    with patch.object(hass.config_entries, "async_update_entry", return_value=None):
        # Attempt to add element with duplicate name
        method_name = f"async_step_configure_{element_type}"
        if hasattr(flow, method_name):
            method = getattr(flow, method_name)
            result = await method(test_data)

            assert result.get("type") == FlowResultType.FORM
            errors = result.get("errors", {})
            assert errors.get(CONF_NAME) == "name_exists"


async def test_element_form_display(
    hass: HomeAssistant,
    flow_class: type,
    element_type: str,
) -> None:
    """Generic test for element form display."""
    config_entry = create_mock_config_entry()
    flow = flow_class()
    flow.hass = hass
    flow._config_entry = config_entry

    method_name = f"async_step_configure_{element_type}"
    if hasattr(flow, method_name):
        method = getattr(flow, method_name)
        result = await method()

        assert result.get("type") == FlowResultType.FORM
        assert result.get("step_id") == f"configure_{element_type}"


async def test_element_successful_submission(
    hass: HomeAssistant,
    flow_class: type,
    element_type: str,
    test_data: Dict[str, Any],
) -> None:
    """Generic test for successful element submission."""
    config_entry = create_mock_config_entry()
    flow = flow_class()
    flow.hass = hass
    flow._config_entry = config_entry

    with patch.object(hass.config_entries, "async_update_entry", return_value=None):
        method_name = f"async_step_configure_{element_type}"
        if hasattr(flow, method_name):
            method = getattr(flow, method_name)
            result = await method(test_data)

            assert result.get("type") == FlowResultType.CREATE_ENTRY


async def test_element_schema_validation(
    hass: HomeAssistant,
    element_type: str,
    valid_data: Dict[str, Any],
    expected_fields: List[str],
    schema_func: Callable,
) -> None:
    """Generic test for element schema validation."""
    schema = schema_func()
    result = schema(valid_data)

    # Check that expected fields are present in result
    for field in expected_fields:
        assert field in result, f"Field '{field}' not found in schema result"
        assert result[field] == valid_data.get(field)


@pytest.mark.parametrize("invalid_data,expected_error", [])
async def test_element_schema_validation_errors(
    hass: HomeAssistant,
    invalid_data: dict,
    expected_error: str,
    schema_func: Callable,
) -> None:
    """Generic test for element schema validation with invalid data."""
    schema = schema_func()

    try:
        schema(invalid_data)
        assert False, f"Expected validation error for {invalid_data}"
    except Exception as e:
        assert expected_error in str(e).lower()
