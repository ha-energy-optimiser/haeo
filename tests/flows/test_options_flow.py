"""Test options flow for HAEO."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, NamedTuple

from homeassistant.const import CONF_NAME
from homeassistant.data_entry_flow import FlowResultType
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.haeo.const import (
    CONF_CAPACITY,
    CONF_ELEMENT_TYPE,
    CONF_IMPORT_LIMIT,
    DOMAIN,
    ELEMENT_TYPE_BATTERY,
    ELEMENT_TYPE_CONNECTION,
    ELEMENT_TYPE_CONSTANT_LOAD,
    ELEMENT_TYPE_FORECAST_LOAD,
    ELEMENT_TYPE_GENERATOR,
    ELEMENT_TYPE_GRID,
    ELEMENT_TYPE_NET,
    ELEMENT_TYPES,
)
from custom_components.haeo.flows import get_schema
from custom_components.haeo.flows.hub import HubConfigFlow
from custom_components.haeo.flows.options import HubOptionsFlow

# Type aliases for better readability
TestDataDict = dict[str, Any]
ElementType = str
TestCase = dict[str, Any]
TestDataWithDescription = tuple[ElementType, TestCase, str]

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant


# Named tuple with proper type annotations for better type safety and IDE support
class TestDataResult(NamedTuple):
    """Container for test data returned by _get_test_data() function.

    Contains both valid and invalid test cases organized by element type
    for parametrized testing of configuration flows.
    """

    valid_data_by_type: TestDataDict
    valid_test_data: list[tuple[ElementType, TestCase]]
    invalid_data_by_type: TestDataDict
    invalid_test_data: list[tuple[ElementType, TestCase]]
    valid_test_data_with_ids: list[TestDataWithDescription]
    invalid_test_data_with_ids: list[TestDataWithDescription]


# Combined test data for fixtures
def _get_test_data() -> TestDataResult:
    """Get test data from individual files."""
    from .test_data.battery import INVALID_DATA as BATTERY_INVALID_DATA  # noqa: PLC0415
    from .test_data.battery import VALID_DATA as BATTERY_VALID_DATA  # noqa: PLC0415
    from .test_data.connection import INVALID_DATA as CONNECTION_INVALID_DATA  # noqa: PLC0415
    from .test_data.connection import VALID_DATA as CONNECTION_VALID_DATA  # noqa: PLC0415
    from .test_data.constant_load import INVALID_DATA as LOAD_INVALID_DATA  # noqa: PLC0415
    from .test_data.constant_load import VALID_DATA as LOAD_VALID_DATA  # noqa: PLC0415
    from .test_data.forecast_load import INVALID_DATA as LOAD_FORECAST_INVALID_DATA  # noqa: PLC0415
    from .test_data.forecast_load import VALID_DATA as LOAD_FORECAST_VALID_DATA  # noqa: PLC0415
    from .test_data.generator import INVALID_DATA as GENERATOR_INVALID_DATA  # noqa: PLC0415
    from .test_data.generator import VALID_DATA as GENERATOR_VALID_DATA  # noqa: PLC0415
    from .test_data.grid import INVALID_DATA as GRID_INVALID_DATA  # noqa: PLC0415
    from .test_data.grid import VALID_DATA as GRID_VALID_DATA  # noqa: PLC0415
    from .test_data.net import INVALID_DATA as NET_INVALID_DATA  # noqa: PLC0415
    from .test_data.net import VALID_DATA as NET_VALID_DATA  # noqa: PLC0415

    # Create dictionary structure for easier access
    valid_data_by_type = {
        ELEMENT_TYPE_BATTERY: BATTERY_VALID_DATA,
        ELEMENT_TYPE_CONNECTION: CONNECTION_VALID_DATA,
        ELEMENT_TYPE_GENERATOR: GENERATOR_VALID_DATA,
        ELEMENT_TYPE_GRID: GRID_VALID_DATA,
        ELEMENT_TYPE_CONSTANT_LOAD: LOAD_VALID_DATA,
        ELEMENT_TYPE_FORECAST_LOAD: LOAD_FORECAST_VALID_DATA,
        ELEMENT_TYPE_NET: NET_VALID_DATA,
    }

    invalid_data_by_type = {
        ELEMENT_TYPE_BATTERY: BATTERY_INVALID_DATA,
        ELEMENT_TYPE_CONNECTION: CONNECTION_INVALID_DATA,
        ELEMENT_TYPE_GENERATOR: GENERATOR_INVALID_DATA,
        ELEMENT_TYPE_GRID: GRID_INVALID_DATA,
        ELEMENT_TYPE_CONSTANT_LOAD: LOAD_INVALID_DATA,
        ELEMENT_TYPE_FORECAST_LOAD: LOAD_FORECAST_INVALID_DATA,
        ELEMENT_TYPE_NET: NET_INVALID_DATA,
    }

    # Create flat lists with descriptions for parametrized tests
    valid_test_data_with_ids = [
        (element_type, test_data, test_data["description"])
        for element_type, test_data_list in valid_data_by_type.items()
        for test_data in test_data_list
    ]

    invalid_test_data_with_ids = [
        (element_type, test_data, test_data["description"])
        for element_type, test_data_list in invalid_data_by_type.items()
        for test_data in test_data_list
    ]

    return TestDataResult(
        valid_data_by_type=valid_data_by_type,
        valid_test_data=[
            (element_type, test_data)
            for element_type, test_data_list in valid_data_by_type.items()
            for test_data in test_data_list
        ],
        invalid_data_by_type=invalid_data_by_type,
        invalid_test_data=[
            (element_type, test_data)
            for element_type, test_data_list in invalid_data_by_type.items()
            for test_data in test_data_list
        ],
        valid_test_data_with_ids=valid_test_data_with_ids,
        invalid_test_data_with_ids=invalid_test_data_with_ids,
    )


test_data_result = _get_test_data()

# Unpack using named attributes for better readability
VALID_ELEMENT_DATA = test_data_result.valid_data_by_type
VALID_TEST_DATA = test_data_result.valid_test_data
INVALID_ELEMENT_DATA = test_data_result.invalid_data_by_type
INVALID_TEST_DATA = test_data_result.invalid_test_data
VALID_TEST_DATA_WITH_IDS = test_data_result.valid_test_data_with_ids
INVALID_TEST_DATA_WITH_IDS = test_data_result.invalid_test_data_with_ids

# Hub test data (not element-specific)
HUB_VALID_DATA = {"name": "Test Hub"}

# Mock participants for schema testing
MOCK_PARTICIPANTS = {
    "Battery1": {"type": ELEMENT_TYPE_BATTERY, CONF_CAPACITY: 10000},
    "Grid1": {"type": ELEMENT_TYPE_GRID, CONF_IMPORT_LIMIT: 5000},
    "Load1": {"type": ELEMENT_TYPE_CONSTANT_LOAD, "power": 2000},
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
def config_entry():
    """Create basic config entry fixture for testing."""
    return create_mock_config_entry()


@pytest.fixture
def config_entry_with_participants(element_type, valid_element_data):
    """Config entry fixture with a single existing participant."""
    # valid_element_data is a list of test cases, take the first one
    if isinstance(valid_element_data, list) and len(valid_element_data) > 0:
        test_case = valid_element_data[0]
        existing_name = test_case.get(CONF_NAME, "Existing Element")
        config_data = test_case
    else:
        existing_name = valid_element_data.get(CONF_NAME, "Existing Element")
        config_data = valid_element_data

    participants = {
        existing_name: {"type": element_type, **{k: v for k, v in config_data.items() if k != CONF_NAME}},
    }

    return create_mock_config_entry(
        data={
            "integration_type": "hub",
            "name": "Power Network",
            "participants": participants,
        },
    )


@pytest.fixture
def options_flow(hass, config_entry):
    """Create configured options flow fixture."""
    options_flow = HubOptionsFlow()
    options_flow.hass = hass
    options_flow._config_entry = config_entry
    return options_flow


@pytest.fixture
def config_entry_minimal_participants():
    """Config entry with minimal participants for connection testing."""
    return create_mock_config_entry(
        data={
            "integration_type": "hub",
            "name": "Test Hub",
            "participants": {
                "Battery1": {"type": ELEMENT_TYPE_BATTERY, CONF_CAPACITY: 10000},
                "Grid1": {"type": ELEMENT_TYPE_GRID, CONF_IMPORT_LIMIT: 5000},
            },
        },
    )


@pytest.fixture
def options_flow_with_minimal_participants(hass, config_entry_minimal_participants):
    """Options flow fixture with minimal participants for connection testing."""
    options_flow = HubOptionsFlow()
    options_flow.hass = hass
    options_flow._config_entry = config_entry_minimal_participants
    return options_flow


@pytest.fixture
def options_flow_with_participants(hass, config_entry_with_participants):
    """Options flow fixture with existing participant for duplicate name testing."""
    options_flow = HubOptionsFlow()
    options_flow.hass = hass
    options_flow._config_entry = config_entry_with_participants
    return options_flow


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
        },
    )


# Parameterized schema validation tests
@pytest.mark.parametrize(("element_type", "valid_case", "description"), VALID_TEST_DATA_WITH_IDS)
async def test_element_schema_validation_success(element_type, valid_case, description) -> None:
    """Test successful schema validation for all element types."""
    valid_data = valid_case["config"]

    schema = get_schema(element_type, participants=MOCK_PARTICIPANTS)
    result = schema(valid_data)
    assert isinstance(result, dict)
    # Check that all expected fields are present and correct
    for key, value in valid_data.items():
        assert result[key] == value


@pytest.mark.parametrize(("element_type", "invalid_case", "description"), INVALID_TEST_DATA_WITH_IDS)
async def test_element_schema_validation_errors(element_type, invalid_case, description) -> None:
    """Test schema validation errors for all element types."""
    invalid_data = invalid_case["config"]
    expected_error = invalid_case["error"]

    schema = get_schema(element_type, participants=MOCK_PARTICIPANTS)

    try:
        schema(invalid_data)
        assert False, f"Expected validation error for {description}: {invalid_data}"
    except Exception as e:
        assert expected_error in str(e).lower()


# Parameterized participant creation tests
@pytest.mark.parametrize(("element_type", "valid_case", "description"), VALID_TEST_DATA_WITH_IDS)
async def test_participant_creation(element_type, valid_case, description) -> None:
    """Test participant creation for all element types."""
    test_data = valid_case["config"]

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
async def test_options_flow_init(options_flow) -> None:
    """Test options flow initialization."""
    result = await options_flow.async_step_init()

    assert result.get("type") == FlowResultType.MENU
    menu_options = result.get("menu_options", [])
    assert "configure_network" in menu_options
    assert "add_participant" in menu_options
    # edit_participant and remove_participant are only available when there are participants
    assert "edit_participant" not in menu_options
    assert "remove_participant" not in menu_options


async def test_options_flow_init_with_participants(options_flow_with_participants) -> None:
    """Test options flow initialization when participants exist."""
    result = await options_flow_with_participants.async_step_init()

    assert result.get("type") == FlowResultType.MENU
    menu_options = result.get("menu_options", [])
    assert "configure_network" in menu_options
    assert "add_participant" in menu_options
    # edit_participant and remove_participant should be available when there are participants
    assert "edit_participant" in menu_options
    assert "remove_participant" in menu_options


async def test_options_flow_add_participant_type_selection(options_flow) -> None:
    """Test participant type selection."""
    result = await options_flow.async_step_add_participant()

    assert result.get("type") == FlowResultType.FORM
    assert result.get("step_id") == "add_participant"


@pytest.mark.parametrize("participant_type", ELEMENT_TYPES)
async def test_options_flow_route_to_participant_config(options_flow, participant_type) -> None:
    """Test routing to participant configuration."""
    result = await options_flow.async_step_add_participant({"participant_type": participant_type})
    assert result.get("type") == FlowResultType.FORM
    assert result.get("step_id") == f"configure_{participant_type}"


async def test_options_flow_route_to_connection_config_with_participants(
    options_flow_with_minimal_participants,
) -> None:
    """Test routing to connection configuration with sufficient participants."""
    result = await options_flow_with_minimal_participants.async_step_add_participant(
        {"participant_type": ELEMENT_TYPE_CONNECTION}
    )
    assert result.get("type") == FlowResultType.FORM
    assert result.get("step_id") == "configure_connection"


@pytest.mark.parametrize(("element_type", "valid_case", "description"), VALID_TEST_DATA_WITH_IDS)
async def test_options_flow_configure_duplicate_name(
    element_type, valid_case, options_flow_with_participants, description
) -> None:
    """Test configuration with duplicate name for all element types."""
    valid_data = valid_case["config"]

    # Call the appropriate configure method
    method_name = f"async_step_configure_{element_type}"
    if hasattr(options_flow_with_participants, method_name):
        method = getattr(options_flow_with_participants, method_name)
        result = await method(valid_data)

        assert result.get("type") == FlowResultType.FORM
        errors = result.get("errors") or {}
        assert errors.get(CONF_NAME) == "name_exists"


async def test_options_flow_no_participants(options_flow) -> None:
    """Test behavior when no participants exist."""
    # Test edit participants with no participants
    result = await options_flow.async_step_edit_participant()
    assert result.get("type") == FlowResultType.ABORT
    assert result.get("reason") == "no_participants"

    # Test remove participants with no participants
    result = await options_flow.async_step_remove_participant()
    assert result.get("type") == FlowResultType.ABORT
    assert result.get("reason") == "no_participants"


# Parameterized tests for successful configuration submissions
@pytest.mark.parametrize(("element_type", "valid_case", "description"), VALID_TEST_DATA_WITH_IDS)
async def test_options_flow_configure_success(
    hass: HomeAssistant,
    element_type,
    valid_case,
    config_entry_minimal_participants,
    description,
) -> None:
    """Test successful configuration for all element types."""
    # Use the minimal participants config entry for connection types, basic for others
    if element_type == ELEMENT_TYPE_CONNECTION:
        config_entry = config_entry_minimal_participants
    else:
        config_entry = create_mock_config_entry()

    options_flow = HubOptionsFlow()
    options_flow.hass = hass
    options_flow._config_entry = config_entry

    valid_data = valid_case["config"]

    # Call the appropriate configure method
    method_name = f"async_step_configure_{element_type}"
    if hasattr(options_flow, method_name):
        method = getattr(options_flow, method_name)
        result = await method(valid_data)
        assert result.get("type") == FlowResultType.CREATE_ENTRY


# Hub flow tests
async def test_hub_flow_user_step_form(hass: HomeAssistant) -> None:
    """Test that the user step shows the form."""
    flow = HubConfigFlow()
    flow.hass = hass

    result = await flow.async_step_user()

    assert result.get("type") == FlowResultType.FORM
    assert result.get("step_id") == "user"


async def test_hub_flow_create_hub_success(hass: HomeAssistant) -> None:
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


async def test_options_flow_manage_participants_form(options_flow_with_minimal_participants) -> None:
    """Test manage participants form display."""
    # Test form display
    result = await options_flow_with_minimal_participants.async_step_edit_participant()
    assert result.get("type") == FlowResultType.FORM
    assert result.get("step_id") == "edit_participant"


# Schema generation tests
def test_get_schema_grid_flattened_fields() -> None:
    """Test that grid schema generates flattened field names."""
    schema = get_schema(ELEMENT_TYPE_GRID)

    # Check that flattened fields are generated
    flattened_fields = []
    for key in schema.schema:
        key_str = str(key)
        if "price" in key_str and ("_live" in key_str or "_forecast" in key_str):
            flattened_fields.append(key_str)

    # Should have both import and export price fields with live and forecast
    expected_fields = ["import_price_live", "import_price_forecast", "export_price_live", "export_price_forecast"]

    for expected in expected_fields:
        assert expected in flattened_fields, f"Expected field {expected} not found in schema"


def test_get_schema_grid_field_types() -> None:
    """Test that grid schema has correct field types for flattened fields."""
    schema = get_schema(ELEMENT_TYPE_GRID)

    # Check that flattened fields have EntitySelector schemas
    for key in schema.schema:
        key_str = str(key)
        if "price" in key_str and ("_live" in key_str or "_forecast" in key_str):
            field_schema = schema.schema[key]
            # Should be an EntitySelector for sensor selection
            # EntitySelector objects are callable classes, so we check the class name
            assert "EntitySelector" in str(type(field_schema)), f"Field {key_str} should be an EntitySelector"


def test_get_schema_other_elements_no_flattening() -> None:
    """Test that non-price fields don't get flattened."""
    # Test battery schema - should not have flattened fields
    schema = get_schema(ELEMENT_TYPE_BATTERY)

    flattened_fields = []
    for key in schema.schema:
        key_str = str(key)
        if "price" in key_str and ("_live" in key_str or "_forecast" in key_str):
            flattened_fields.append(key_str)

    # Battery should not have price fields
    assert len(flattened_fields) == 0, (
        f"Battery schema should not have flattened price fields, but found: {flattened_fields}"
    )


def test_get_schema_connection_no_flattening() -> None:
    """Test that connection schema doesn't get flattened (only has source/target)."""
    schema = get_schema(ELEMENT_TYPE_CONNECTION)

    flattened_fields = []
    for key in schema.schema:
        key_str = str(key)
        if "price" in key_str and ("_live" in key_str or "_forecast" in key_str):
            flattened_fields.append(key_str)

    # Connection should not have price fields
    assert len(flattened_fields) == 0, (
        f"Connection schema should not have flattened price fields, but found: {flattened_fields}"
    )


def test_get_schema_grid_is_only_element_with_price_fields() -> None:
    """Test that only grid element has flattened price fields."""
    # Test grid - should have price fields
    grid_schema = get_schema(ELEMENT_TYPE_GRID)
    grid_price_fields = []
    for key in grid_schema.schema:
        key_str = str(key)
        if "price" in key_str and ("_live" in key_str or "_forecast" in key_str):
            grid_price_fields.append(key_str)

    expected_grid_fields = ["import_price_live", "import_price_forecast", "export_price_live", "export_price_forecast"]

    for expected in expected_grid_fields:
        assert expected in grid_price_fields, f"Expected field {expected} not found in grid schema"

    # Test forecast_load - should NOT have price fields
    forecast_load_schema = get_schema(ELEMENT_TYPE_FORECAST_LOAD)
    forecast_load_price_fields = []
    for key in forecast_load_schema.schema:
        key_str = str(key)
        if "price" in key_str and ("_live" in key_str or "_forecast" in key_str):
            forecast_load_price_fields.append(key_str)

    # Forecast load should not have price fields
    assert len(forecast_load_price_fields) == 0, (
        f"Forecast load should not have price fields, but found: {forecast_load_price_fields}"
    )
