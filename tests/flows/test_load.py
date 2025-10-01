"""Test data and validation for load flow configuration."""

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_NAME

from custom_components.haeo.flows.load import (
    get_load_schema,
    create_load_participant,
)
from custom_components.haeo.const import (
    ELEMENT_TYPE_LOAD,
    CONF_LOAD_TYPE,
    CONF_POWER,
    CONF_ENERGY,
    LOAD_TYPE_FIXED,
    LOAD_TYPE_VARIABLE,
)


# Load-specific test data
LOAD_VALID_DATA = {
    CONF_NAME: "Test Load",
    CONF_LOAD_TYPE: LOAD_TYPE_FIXED,
    CONF_POWER: 1500,
}

LOAD_VARIABLE_DATA = {
    CONF_NAME: "Variable Load",
    CONF_LOAD_TYPE: LOAD_TYPE_VARIABLE,
    CONF_POWER: 2000,
    CONF_ENERGY: 8000,
}

LOAD_INVALID_DATA = [
    ({CONF_NAME: "", CONF_LOAD_TYPE: LOAD_TYPE_FIXED}, "cannot be empty"),
    ({CONF_NAME: "Test", CONF_POWER: -500}, "too small"),
]

LOAD_PARTICIPANT_SCENARIOS = [
    # Fixed load
    (
        {
            CONF_NAME: "Fixed Load",
            CONF_LOAD_TYPE: LOAD_TYPE_FIXED,
            CONF_POWER: 1500,
        },
        LOAD_TYPE_FIXED,
    ),
    # Variable load
    (
        {
            CONF_NAME: "Variable Load",
            CONF_LOAD_TYPE: LOAD_TYPE_VARIABLE,
            CONF_POWER: 2000,
            CONF_ENERGY: 8000,
        },
        LOAD_TYPE_VARIABLE,
    ),
]


@pytest.fixture
def valid_load_data():
    """Get valid load test data."""
    return LOAD_VALID_DATA.copy()


async def test_load_schema_basic_validation(hass: HomeAssistant):
    """Test basic load schema validation."""
    schema = get_load_schema()
    result = schema(LOAD_VALID_DATA)

    assert result[CONF_NAME] == LOAD_VALID_DATA[CONF_NAME]
    assert result[CONF_LOAD_TYPE] == LOAD_VALID_DATA[CONF_LOAD_TYPE]
    assert result[CONF_POWER] == LOAD_VALID_DATA[CONF_POWER]


async def test_load_schema_variable_type(hass: HomeAssistant):
    """Test load schema with variable type."""
    schema = get_load_schema()
    result = schema(LOAD_VARIABLE_DATA)

    assert result[CONF_NAME] == LOAD_VARIABLE_DATA[CONF_NAME]
    assert result[CONF_LOAD_TYPE] == LOAD_TYPE_VARIABLE
    assert result[CONF_ENERGY] == LOAD_VARIABLE_DATA[CONF_ENERGY]


@pytest.mark.parametrize("invalid_data,expected_error", LOAD_INVALID_DATA)
async def test_load_schema_validation_errors(
    hass: HomeAssistant,
    invalid_data: dict,
    expected_error: str,
):
    """Test load schema validation with invalid data."""
    schema = get_load_schema()

    try:
        schema(invalid_data)
        assert False, f"Expected validation error for {invalid_data}"
    except Exception as e:
        assert expected_error in str(e).lower()


@pytest.mark.parametrize("load_data,expected_type", LOAD_PARTICIPANT_SCENARIOS)
async def test_load_participant_creation(
    hass: HomeAssistant,
    load_data: dict,
    expected_type: str,
):
    """Test load participant creation with various configurations."""
    participant = create_load_participant(load_data)

    assert participant["type"] == ELEMENT_TYPE_LOAD
    assert participant[CONF_LOAD_TYPE] == expected_type
    assert participant[CONF_POWER] == load_data[CONF_POWER]
