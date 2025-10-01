"""Test data and validation for forecast load flow configuration."""

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_NAME

from custom_components.haeo.flows.load_forecast import (
    get_forecast_load_schema,
    create_forecast_load_participant,
)
from custom_components.haeo.const import (
    CONF_ENERGY,
    CONF_FORECAST_SENSORS,
    ELEMENT_TYPE_LOAD_FORECAST,
    LOAD_TYPE_FORECAST,
)


# Load-specific test data
LOAD_VARIABLE_DATA = {
    CONF_NAME: "Variable Load",
    CONF_FORECAST_SENSORS: ["sensor.forecast1", "sensor.forecast2"],
}

LOAD_PARTICIPANT_SCENARIOS = [
    # Variable load
    (
        {
            CONF_NAME: "Variable Load",
            CONF_ENERGY: 8000,
        },
        LOAD_TYPE_FORECAST,
    ),
]


@pytest.fixture
def valid_load_data():
    """Get valid load test data."""
    return LOAD_VARIABLE_DATA.copy()


async def test_load_schema_variable_type(hass: HomeAssistant):
    """Test load schema with variable type."""
    schema = get_forecast_load_schema()
    result = schema(LOAD_VARIABLE_DATA)

    assert result[CONF_NAME] == LOAD_VARIABLE_DATA[CONF_NAME]
    assert result[CONF_FORECAST_SENSORS] == LOAD_VARIABLE_DATA[CONF_FORECAST_SENSORS]


@pytest.mark.parametrize("load_data,expected_type", LOAD_PARTICIPANT_SCENARIOS)
async def test_load_participant_creation(
    hass: HomeAssistant,
    load_data: dict,
    expected_type: str,
):
    """Test load participant creation with various configurations."""
    participant = create_forecast_load_participant(load_data)

    assert participant["type"] == ELEMENT_TYPE_LOAD_FORECAST
