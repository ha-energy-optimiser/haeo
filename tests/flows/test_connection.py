"""Test data and validation for connection flow configuration."""

import pytest
from homeassistant.core import HomeAssistant

from custom_components.haeo.flows.connection import (
    get_connection_schema,
    create_connection_participant,
)
from custom_components.haeo.const import (
    CONF_NAME,
    CONF_SOURCE,
    CONF_TARGET,
    CONF_MIN_POWER,
    CONF_MAX_POWER,
    ENTITY_TYPE_BATTERY,
    ENTITY_TYPE_GRID,
    ENTITY_TYPE_GENERATOR,
    ENTITY_TYPE_LOAD,
)


# Mock participants for testing
MOCK_PARTICIPANTS = {
    "battery_1": {"type": ENTITY_TYPE_BATTERY, "name": "Battery 1"},
    "grid_1": {"type": ENTITY_TYPE_GRID, "name": "Grid 1"},
    "solar_1": {"type": ENTITY_TYPE_GENERATOR, "name": "Solar 1"},
    "house_load": {"type": ENTITY_TYPE_LOAD, "name": "House Load"},
}

# Connection-specific test data
CONNECTION_VALID_DATA = {
    CONF_NAME: "Battery to Grid",
    CONF_SOURCE: "battery_1",
    CONF_TARGET: "grid_1",
    CONF_MIN_POWER: 0,
    CONF_MAX_POWER: 2000,
}

CONNECTION_LIMITED_DATA = {
    CONF_NAME: "Solar to Load",
    CONF_SOURCE: "solar_1",
    CONF_TARGET: "house_load",
    CONF_MIN_POWER: 0,
    CONF_MAX_POWER: 5000,
}

CONNECTION_INVALID_DATA = [
    ({CONF_NAME: "Test Connection", CONF_SOURCE: "", CONF_TARGET: "grid_1"}, "value must be one of"),
    ({CONF_NAME: "Test Connection", CONF_SOURCE: "battery_1", CONF_TARGET: ""}, "value must be one of"),
]

CONNECTION_PARTICIPANT_SCENARIOS = [
    # Bidirectional connection (battery-grid)
    (
        {
            CONF_NAME: "Battery to Grid",
            CONF_SOURCE: "battery_1",
            CONF_TARGET: "grid_1",
            CONF_MIN_POWER: 0,
            CONF_MAX_POWER: 2000,
        },
        "bidirectional",
    ),
    # Unidirectional connection (solar-load)
    (
        {
            CONF_NAME: "Solar to Load",
            CONF_SOURCE: "solar_1",
            CONF_TARGET: "house_load",
            CONF_MIN_POWER: 0,
            CONF_MAX_POWER: 5000,
        },
        "unidirectional",
    ),
]


@pytest.fixture
def valid_connection_data():
    """Get valid connection test data."""
    return CONNECTION_VALID_DATA.copy()


async def test_connection_schema_basic_validation(hass: HomeAssistant):
    """Test basic connection schema validation."""
    schema = get_connection_schema(MOCK_PARTICIPANTS)
    result = schema(CONNECTION_VALID_DATA)

    assert result[CONF_NAME] == CONNECTION_VALID_DATA[CONF_NAME]
    assert result[CONF_SOURCE] == CONNECTION_VALID_DATA[CONF_SOURCE]
    assert result[CONF_TARGET] == CONNECTION_VALID_DATA[CONF_TARGET]
    assert result[CONF_MIN_POWER] == 0  # Should be default since negative values are invalid
    assert result[CONF_MAX_POWER] == CONNECTION_VALID_DATA[CONF_MAX_POWER]


async def test_connection_schema_limited_power(hass: HomeAssistant):
    """Test connection schema with power limits."""
    schema = get_connection_schema(MOCK_PARTICIPANTS)
    result = schema(CONNECTION_LIMITED_DATA)

    assert result[CONF_NAME] == CONNECTION_LIMITED_DATA[CONF_NAME]
    assert result[CONF_SOURCE] == CONNECTION_LIMITED_DATA[CONF_SOURCE]
    assert result[CONF_TARGET] == CONNECTION_LIMITED_DATA[CONF_TARGET]
    assert result[CONF_MIN_POWER] == 0  # Should be default since negative values are invalid
    assert result[CONF_MAX_POWER] == CONNECTION_LIMITED_DATA[CONF_MAX_POWER]


@pytest.mark.parametrize("invalid_data,expected_error", CONNECTION_INVALID_DATA)
async def test_connection_schema_validation_errors(
    hass: HomeAssistant,
    invalid_data: dict,
    expected_error: str,
):
    """Test connection schema validation with invalid data."""
    schema = get_connection_schema(MOCK_PARTICIPANTS)

    try:
        schema(invalid_data)
        assert False, f"Expected validation error for {invalid_data}"
    except Exception as e:
        assert expected_error in str(e).lower()


@pytest.mark.parametrize("connection_data,expected_type", CONNECTION_PARTICIPANT_SCENARIOS)
async def test_connection_participant_creation(
    hass: HomeAssistant,
    connection_data: dict,
    expected_type: str,
):
    """Test connection participant creation with various configurations."""
    participant = create_connection_participant(connection_data)

    assert participant[CONF_NAME] == connection_data[CONF_NAME]
    assert participant[CONF_SOURCE] == connection_data[CONF_SOURCE]
    assert participant[CONF_TARGET] == connection_data[CONF_TARGET]
    assert participant[CONF_MIN_POWER] == connection_data[CONF_MIN_POWER]
    assert participant[CONF_MAX_POWER] == connection_data[CONF_MAX_POWER]

    if expected_type == "bidirectional":
        assert participant[CONF_MAX_POWER] > 0
    elif expected_type == "unidirectional":
        assert participant[CONF_MIN_POWER] >= 0
