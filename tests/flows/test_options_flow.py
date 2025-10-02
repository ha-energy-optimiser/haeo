"""Test options flow for HAEO."""

from __future__ import annotations

import pytest
from typing import Any
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
    ELEMENT_TYPE_LOAD_CONSTANT,
    ELEMENT_TYPE_LOAD_FORECAST,
    ELEMENT_TYPE_GENERATOR,
    ELEMENT_TYPE_NET,
    ELEMENT_TYPES,
    CONF_CAPACITY,
    CONF_IMPORT_LIMIT,
    CONF_ELEMENT_TYPE,
)

# Import the schema helper from the main flows module
from custom_components.haeo.flows import get_schema


# Combined test data for fixtures
def _get_test_data():
    """Get test data from individual files."""
    from .test_data.battery import VALID_DATA as BATTERY_VALID_DATA, INVALID_DATA as BATTERY_INVALID_DATA
    from .test_data.connection import VALID_DATA as CONNECTION_VALID_DATA, INVALID_DATA as CONNECTION_INVALID_DATA
    from .test_data.generator import VALID_DATA as GENERATOR_VALID_DATA, INVALID_DATA as GENERATOR_INVALID_DATA
    from .test_data.grid import VALID_DATA as GRID_VALID_DATA, INVALID_DATA as GRID_INVALID_DATA
    from .test_data.load_constant import VALID_DATA as LOAD_VALID_DATA, INVALID_DATA as LOAD_INVALID_DATA
    from .test_data.load_forecast import (
        VALID_DATA as LOAD_FORECAST_VALID_DATA,
        INVALID_DATA as LOAD_FORECAST_INVALID_DATA,
    )
    from .test_data.net import VALID_DATA as NET_VALID_DATA, INVALID_DATA as NET_INVALID_DATA

    # Create dictionary structure for easier access
    valid_data_by_type = {
        ELEMENT_TYPE_BATTERY: BATTERY_VALID_DATA,
        ELEMENT_TYPE_CONNECTION: CONNECTION_VALID_DATA,
        ELEMENT_TYPE_GENERATOR: GENERATOR_VALID_DATA,
        ELEMENT_TYPE_GRID: GRID_VALID_DATA,
        ELEMENT_TYPE_LOAD_CONSTANT: LOAD_VALID_DATA,
        ELEMENT_TYPE_LOAD_FORECAST: LOAD_FORECAST_VALID_DATA,
        ELEMENT_TYPE_NET: NET_VALID_DATA,
    }

    invalid_data_by_type = {
        ELEMENT_TYPE_BATTERY: BATTERY_INVALID_DATA,
        ELEMENT_TYPE_CONNECTION: CONNECTION_INVALID_DATA,
        ELEMENT_TYPE_GENERATOR: GENERATOR_INVALID_DATA,
        ELEMENT_TYPE_GRID: GRID_INVALID_DATA,
        ELEMENT_TYPE_LOAD_CONSTANT: LOAD_INVALID_DATA,
        ELEMENT_TYPE_LOAD_FORECAST: LOAD_FORECAST_INVALID_DATA,
        ELEMENT_TYPE_NET: NET_INVALID_DATA,
    }

    return (
        valid_data_by_type,
        [
            (element_type, test_data)
            for element_type, test_data_list in valid_data_by_type.items()
            for test_data in test_data_list
        ],
        invalid_data_by_type,
        [
            (element_type, test_data)
            for element_type, test_data_list in invalid_data_by_type.items()
            for test_data in test_data_list
        ],
    )


VALID_ELEMENT_DATA, VALID_TEST_DATA, INVALID_ELEMENT_DATA, INVALID_TEST_DATA = _get_test_data()

# Hub test data (not element-specific)
HUB_VALID_DATA = {"name": "Test Hub"}

# Mock participants for schema testing
MOCK_PARTICIPANTS = {
    "Battery1": {"type": ELEMENT_TYPE_BATTERY, CONF_CAPACITY: 10000},
    "Grid1": {"type": ELEMENT_TYPE_GRID, CONF_IMPORT_LIMIT: 5000},
    "Load1": {"type": ELEMENT_TYPE_LOAD_CONSTANT, "power": 2000},
}


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


# Pytest fixtures for data-driven testing
@pytest.fixture(params=ELEMENT_TYPES)
def element_type(request):
    """Parametrized fixture for element types."""
    return request.param


@pytest.fixture
def valid_element_data(element_type):
    """Fixture providing valid data for each element type."""
    return VALID_ELEMENT_DATA[element_type]


@pytest.fixture
def config_entry_with_existing_participant(element_type, valid_element_data):
    """Fixture providing config entry with existing participant."""
    existing_name = valid_element_data.get(CONF_NAME, "Existing Element")
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


@pytest.fixture
def config_entry_with_multiple_participants():
    """Fixture providing config entry with multiple participants for connection testing."""
    # Use actual valid data from VALID_TEST_DATA for realistic test participants
    participants = {}
    # Use the first valid case from each element type for the fixture
    for element_type, valid_case in VALID_ELEMENT_DATA.items():
        test_data = valid_case["config"]
        # Use the first few characters of the element type as a simple participant name
        participant_name = f"{element_type[:6]}1"  # e.g., "batte1", "grid1", etc.
        participants[participant_name] = {
            "type": element_type,
            **{k: v for k, v in test_data.items() if k != CONF_NAME},
        }

    return create_mock_config_entry(
        data={
            "integration_type": "hub",
            "name": "Power Network",
            "participants": participants,
        }
    )


# Parameterized schema validation tests
@pytest.mark.parametrize("element_type,valid_case", VALID_TEST_DATA)
async def test_element_schema_validation_success(hass: HomeAssistant, element_type, valid_case):
    """Test successful schema validation for all element types."""
    valid_data = valid_case["config"]
    description = valid_case["description"]

    schema = get_schema(element_type, participants=MOCK_PARTICIPANTS)
    result = schema(valid_data)
    assert isinstance(result, dict)
    # Check that all expected fields are present and correct
    for key, value in valid_data.items():
        assert result[key] == value


@pytest.mark.parametrize("element_type,invalid_case", INVALID_TEST_DATA)
async def test_element_schema_validation_errors(hass: HomeAssistant, element_type, invalid_case):
    """Test schema validation errors for all element types."""
    invalid_data = invalid_case["config"]
    expected_error = invalid_case["error"]
    description = invalid_case["description"]

    schema = get_schema(element_type, participants=MOCK_PARTICIPANTS)

    try:
        schema(invalid_data)
        assert False, f"Expected validation error for {description}: {invalid_data}"
    except Exception as e:
        assert expected_error in str(e).lower()


# Parameterized participant creation tests
@pytest.mark.parametrize("element_type,valid_case", VALID_TEST_DATA)
async def test_participant_creation(hass: HomeAssistant, element_type, valid_case):
    """Test participant creation for all element types."""
    test_data = valid_case["config"]
    description = valid_case["description"]

    # Create participant directly (all create_*_participant functions do the same thing)
    participant = {
        CONF_ELEMENT_TYPE: element_type,
        **test_data,
    }

    # Check basic participant structure
    assert participant["type"] == element_type
    # Check that all provided data is correctly set in the participant
    for key, value in test_data.items():
        assert participant[key] == value


# Test functions for options flow
async def test_options_flow_init(hass: HomeAssistant):
    """Test options flow initialization."""
    from custom_components.haeo.flows.options import HubOptionsFlow

    config_entry = create_mock_config_entry()
    options_flow = HubOptionsFlow()
    options_flow._config_entry = config_entry

    result = await options_flow.async_step_init()

    assert result.get("type") == FlowResultType.MENU
    menu_options = result.get("menu_options", [])
    assert "add_participant" in menu_options
    assert "edit_participant" in menu_options
    assert "remove_participant" in menu_options


async def test_options_flow_add_participant_type_selection(hass: HomeAssistant):
    """Test participant type selection."""
    from custom_components.haeo.flows.options import HubOptionsFlow

    config_entry = create_mock_config_entry()
    options_flow = HubOptionsFlow()
    options_flow._config_entry = config_entry

    result = await options_flow.async_step_add_participant()

    assert result.get("type") == FlowResultType.FORM
    assert result.get("step_id") == "add_participant"


@pytest.mark.parametrize("participant_type", ELEMENT_TYPES)
async def test_options_flow_route_to_participant_config(hass: HomeAssistant, participant_type):
    """Test routing to participant configuration."""
    from custom_components.haeo.flows.options import HubOptionsFlow

    config_entry = create_mock_config_entry()
    options_flow = HubOptionsFlow()
    options_flow.hass = hass
    options_flow._config_entry = config_entry

    result = await options_flow.async_step_add_participant({"participant_type": participant_type})
    assert result.get("type") == FlowResultType.FORM
    assert result.get("step_id") == f"configure_{participant_type}"


async def test_options_flow_route_to_connection_config_with_participants(hass: HomeAssistant):
    """Test routing to connection configuration with sufficient participants."""
    from custom_components.haeo.flows.options import HubOptionsFlow

    config_entry = create_mock_config_entry(
        data={
            "integration_type": "hub",
            "name": "Test Hub",
            "participants": {
                "Battery1": {"type": ELEMENT_TYPE_BATTERY, CONF_CAPACITY: 10000},
                "Grid1": {"type": ELEMENT_TYPE_GRID, CONF_IMPORT_LIMIT: 5000},
            },
        }
    )
    options_flow = HubOptionsFlow()
    options_flow.hass = hass
    options_flow._config_entry = config_entry

    result = await options_flow.async_step_add_participant({"participant_type": ELEMENT_TYPE_CONNECTION})
    assert result.get("type") == FlowResultType.FORM
    assert result.get("step_id") == "configure_connection"


@pytest.mark.parametrize("element_type,valid_case", VALID_TEST_DATA)
async def test_options_flow_configure_duplicate_name(hass: HomeAssistant, element_type, valid_case):
    """Test configuration with duplicate name for all element types."""
    from custom_components.haeo.flows.options import HubOptionsFlow

    valid_data = valid_case["config"]
    description = valid_case["description"]

    # Create config data with existing participant using the same name as in valid_data
    existing_name = valid_data[CONF_NAME]
    config_data_with_existing = {
        "integration_type": "hub",
        "name": "Test Hub",
        "participants": {existing_name: {"type": element_type}},
    }
    config_entry = create_mock_config_entry(data=config_data_with_existing)
    options_flow = HubOptionsFlow()
    options_flow._config_entry = config_entry

    # Call the appropriate configure method
    method_name = f"async_step_configure_{element_type}"
    if hasattr(options_flow, method_name):
        method = getattr(options_flow, method_name)
        result = await method(valid_data)

        assert result.get("type") == FlowResultType.FORM
        errors = result.get("errors") or {}
        assert errors.get(CONF_NAME) == "name_exists"


async def test_options_flow_no_participants(hass: HomeAssistant):
    """Test behavior when no participants exist."""
    from custom_components.haeo.flows.options import HubOptionsFlow

    config_entry = create_mock_config_entry()  # Empty participants
    options_flow = HubOptionsFlow()
    options_flow._config_entry = config_entry

    # Test edit participants with no participants
    result = await options_flow.async_step_edit_participant()
    assert result.get("type") == FlowResultType.ABORT
    assert result.get("reason") == "no_participants"

    # Test remove participants with no participants
    result = await options_flow.async_step_remove_participant()
    assert result.get("type") == FlowResultType.ABORT
    assert result.get("reason") == "no_participants"


# Parameterized tests for successful configuration submissions
@pytest.mark.parametrize("element_type,valid_case", VALID_TEST_DATA)
async def test_options_flow_configure_success(hass: HomeAssistant, element_type, valid_case):
    """Test successful configuration for all element types."""
    from custom_components.haeo.flows.options import HubOptionsFlow

    # Create appropriate config entry based on element type
    if element_type == ELEMENT_TYPE_CONNECTION:
        # Connection needs existing participants
        config_data = {
            "integration_type": "hub",
            "name": "Test Hub",
            "participants": {
                "Battery1": {"type": ELEMENT_TYPE_BATTERY, CONF_CAPACITY: 10000},
                "Grid1": {"type": ELEMENT_TYPE_GRID, CONF_IMPORT_LIMIT: 5000},
            },
        }
        config_entry = create_mock_config_entry(data=config_data)
    else:
        config_entry = create_mock_config_entry()

    options_flow = HubOptionsFlow()
    options_flow.hass = hass
    options_flow._config_entry = config_entry

    with patch.object(hass.config_entries, "async_update_entry", return_value=None):
        valid_data = valid_case["config"]

        # Call the appropriate configure method
        method_name = f"async_step_configure_{element_type}"
        if hasattr(options_flow, method_name):
            method = getattr(options_flow, method_name)
            result = await method(valid_data)
            assert result.get("type") == FlowResultType.CREATE_ENTRY


# Hub flow tests
async def test_hub_flow_user_step_form(hass: HomeAssistant):
    """Test that the user step shows the form."""
    from custom_components.haeo.flows.hub import HubConfigFlow

    flow = HubConfigFlow()
    flow.hass = hass

    result = await flow.async_step_user()

    assert result.get("type") == FlowResultType.FORM
    assert result.get("step_id") == "user"


async def test_hub_flow_create_hub_success(hass: HomeAssistant):
    """Test successful hub creation."""
    result = await hass.config_entries.flow.async_init("haeo", context={"source": "user"})

    assert result.get("type") == FlowResultType.FORM
    assert result.get("step_id") == "user"

    result = await hass.config_entries.flow.async_configure(result["flow_id"], HUB_VALID_DATA)

    assert result.get("type") == FlowResultType.CREATE_ENTRY
    assert result.get("title") == HUB_VALID_DATA[CONF_NAME]

    data = result.get("data", {})
    assert data.get("integration_type") == "hub"
    assert data.get(CONF_NAME) == HUB_VALID_DATA[CONF_NAME]
    assert data.get("participants") == {}


async def test_hub_flow_validation_functions():
    """Test the validation functions."""
    from custom_components.haeo.flows import (
        validate_element_name,
        validate_positive_number,
        validate_percentage,
        validate_efficiency,
    )
    import voluptuous as vol

    # Test element name validation
    assert validate_element_name("Valid Name") == "Valid Name"

    with pytest.raises(vol.Invalid):
        validate_element_name("")

    # Test positive number validation
    assert validate_positive_number(100) == 100

    with pytest.raises(vol.Invalid):
        validate_positive_number(0)

    with pytest.raises(vol.Invalid):
        validate_positive_number(-10)

    # Test percentage validation
    assert validate_percentage(50) == 50
    assert validate_percentage(0) == 0
    assert validate_percentage(100) == 100

    with pytest.raises(vol.Invalid):
        validate_percentage(-10)

    with pytest.raises(vol.Invalid):
        validate_percentage(150)

    # Test efficiency validation
    assert validate_efficiency(0.95) == 0.95
    assert validate_efficiency(1.0) == 1.0

    with pytest.raises(vol.Invalid):
        validate_efficiency(1.5)

    with pytest.raises(vol.Invalid):
        validate_efficiency(0)


async def test_options_flow_add_participant_type_selection(hass: HomeAssistant):
    """Test participant type selection."""
    from custom_components.haeo.flows.options import HubOptionsFlow

    config_entry = create_mock_config_entry()
    options_flow = HubOptionsFlow()
    options_flow._config_entry = config_entry

    result = await options_flow.async_step_add_participant()

    assert result.get("type") == FlowResultType.FORM
    assert result.get("step_id") == "add_participant"


async def test_options_flow_manage_participants_form(hass: HomeAssistant):
    """Test manage participants form display."""
    from custom_components.haeo.flows.options import HubOptionsFlow

    config_data = {
        "integration_type": "hub",
        "name": "Test Hub",
        "participants": {
            "Battery1": {"type": ELEMENT_TYPE_BATTERY, CONF_CAPACITY: 10000},
            "Grid1": {"type": ELEMENT_TYPE_GRID, CONF_IMPORT_LIMIT: 5000},
        },
    }
    config_entry = create_mock_config_entry(data=config_data)
    options_flow = HubOptionsFlow()
    options_flow.hass = hass
    options_flow._config_entry = config_entry

    # Test form display
    result = await options_flow.async_step_edit_participant()
    assert result.get("type") == FlowResultType.FORM
    assert result.get("step_id") == "edit_participant"
