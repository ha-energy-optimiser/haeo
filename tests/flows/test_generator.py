"""Test data and validation for generator flow configuration."""

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_NAME

from custom_components.haeo.flows.generator import (
    get_generator_schema,
    create_generator_participant,
)
from custom_components.haeo.const import (
    ENTITY_TYPE_GENERATOR,
    CONF_MAX_POWER,
    CONF_ENERGY,
    CONF_CURTAILMENT,
    CONF_FORECAST_SENSORS,
)


# Generator-specific test data
GENERATOR_VALID_DATA = {
    CONF_NAME: "Test Generator",
    CONF_MAX_POWER: 3000,
    CONF_CURTAILMENT: False,
}

GENERATOR_CURTAILABLE_DATA = {
    CONF_NAME: "Curtailable Generator",
    CONF_MAX_POWER: 5000,
    CONF_CURTAILMENT: True,
}

GENERATOR_FORECAST_DATA = {
    CONF_NAME: "Solar Generator",
    CONF_MAX_POWER: 4000,
    CONF_CURTAILMENT: True,
    CONF_FORECAST_SENSORS: ["sensor.solar_forecast"],
}

GENERATOR_INVALID_DATA = [
    ({CONF_NAME: "", CONF_MAX_POWER: 3000}, "cannot be empty"),
    ({CONF_NAME: "Test", CONF_MAX_POWER: -1000}, "too small"),
]

GENERATOR_PARTICIPANT_SCENARIOS = [
    # Basic generator
    (
        {
            CONF_NAME: "Basic Generator",
            CONF_MAX_POWER: 3000,
            CONF_ENERGY: 12000,
            CONF_CURTAILMENT: False,
        },
        "basic",
    ),
    # Curtailable generator
    (
        {
            CONF_NAME: "Curtailable Generator",
            CONF_MAX_POWER: 5000,
            CONF_CURTAILMENT: True,
        },
        "curtailable",
    ),
    # Generator with forecast
    (
        {
            CONF_NAME: "Solar Generator",
            CONF_MAX_POWER: 4000,
            CONF_ENERGY: 16000,
            CONF_CURTAILMENT: True,
            CONF_FORECAST_SENSORS: ["sensor.solar_forecast"],
        },
        "forecast",
    ),
]


@pytest.fixture
def valid_generator_data():
    """Get valid generator test data."""
    return GENERATOR_VALID_DATA.copy()


async def test_generator_schema_basic_validation(hass: HomeAssistant):
    """Test basic generator schema validation."""
    schema = get_generator_schema()
    result = schema(GENERATOR_VALID_DATA)

    assert result[CONF_NAME] == GENERATOR_VALID_DATA[CONF_NAME]
    assert result[CONF_MAX_POWER] == GENERATOR_VALID_DATA[CONF_MAX_POWER]


async def test_generator_schema_curtailable(hass: HomeAssistant):
    """Test generator schema with curtailable option."""
    schema = get_generator_schema()
    result = schema(GENERATOR_CURTAILABLE_DATA)

    assert result[CONF_NAME] == GENERATOR_CURTAILABLE_DATA[CONF_NAME]
    assert result[CONF_CURTAILMENT] == GENERATOR_CURTAILABLE_DATA[CONF_CURTAILMENT]


async def test_generator_schema_with_forecast(hass: HomeAssistant):
    """Test generator schema with forecast sensor."""
    schema = get_generator_schema()
    result = schema(GENERATOR_FORECAST_DATA)

    assert result[CONF_NAME] == GENERATOR_FORECAST_DATA[CONF_NAME]
    assert result[CONF_FORECAST_SENSORS] == GENERATOR_FORECAST_DATA[CONF_FORECAST_SENSORS]


@pytest.mark.parametrize("invalid_data,expected_error", GENERATOR_INVALID_DATA)
async def test_generator_schema_validation_errors(
    hass: HomeAssistant,
    invalid_data: dict,
    expected_error: str,
):
    """Test generator schema validation with invalid data."""
    schema = get_generator_schema()

    try:
        schema(invalid_data)
        assert False, f"Expected validation error for {invalid_data}"
    except Exception as e:
        assert expected_error in str(e).lower()


@pytest.mark.parametrize("generator_data,expected_type", GENERATOR_PARTICIPANT_SCENARIOS)
async def test_generator_participant_creation(
    hass: HomeAssistant,
    generator_data: dict,
    expected_type: str,
):
    """Test generator participant creation with various configurations."""
    participant = create_generator_participant(generator_data)

    assert participant["type"] == ENTITY_TYPE_GENERATOR
    assert participant[CONF_MAX_POWER] == generator_data[CONF_MAX_POWER]

    if expected_type in ["curtailable", "forecast"]:
        assert participant[CONF_CURTAILMENT] == generator_data[CONF_CURTAILMENT]

    if expected_type == "forecast":
        assert participant[CONF_FORECAST_SENSORS] == generator_data[CONF_FORECAST_SENSORS]
