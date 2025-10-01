"""Test data and validation for constant load flow configuration."""

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_NAME

from custom_components.haeo.flows.load_constant import (
    get_constant_load_schema,
    create_constant_load_participant,
)
from custom_components.haeo.const import (
    CONF_POWER,
    ELEMENT_TYPE_LOAD_FIXED,
    LOAD_TYPE_FIXED,
)


# Load-specific test data
LOAD_VALID_DATA = {
    CONF_NAME: "Test Load",
    CONF_POWER: 1500,
}

LOAD_INVALID_DATA = [
    ({CONF_NAME: ""}, "cannot be empty"),
    ({CONF_NAME: "Test", CONF_POWER: -500}, "too small"),
]

LOAD_PARTICIPANT_SCENARIOS = [
    # Fixed load
    (
        {
            CONF_NAME: "Fixed Load",
            CONF_POWER: 1500,
        },
        LOAD_TYPE_FIXED,
    ),
]


async def test_load_schema_basic_validation(hass: HomeAssistant):
    """Test basic load schema validation."""
    schema = get_constant_load_schema()
    result = schema(LOAD_VALID_DATA)

    assert result[CONF_NAME] == LOAD_VALID_DATA[CONF_NAME]
    assert result[CONF_POWER] == LOAD_VALID_DATA[CONF_POWER]


@pytest.mark.parametrize("invalid_data,expected_error", LOAD_INVALID_DATA)
async def test_load_schema_validation_errors(
    hass: HomeAssistant,
    invalid_data: dict,
    expected_error: str,
):
    """Test load schema validation with invalid data."""
    schema = get_constant_load_schema()

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
    participant = create_constant_load_participant(load_data)

    assert participant["type"] == ELEMENT_TYPE_LOAD_FIXED
    assert participant[CONF_POWER] == load_data[CONF_POWER]
