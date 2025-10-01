"""Test data and validation for grid flow configuration."""

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_NAME

from custom_components.haeo.flows.grid import (
    get_grid_schema,
    create_grid_participant,
)
from custom_components.haeo.const import (
    ELEMENT_TYPE_GRID,
    CONF_IMPORT_LIMIT,
    CONF_EXPORT_LIMIT,
    CONF_PRICE_IMPORT_SENSOR,
    CONF_PRICE_EXPORT_SENSOR,
)


# Grid-specific test data
GRID_VALID_DATA = {
    CONF_NAME: "Test Grid",
    CONF_IMPORT_LIMIT: 5000,
    CONF_EXPORT_LIMIT: 3000,
}

GRID_SENSOR_DATA = {
    CONF_NAME: "Sensor Grid",
    CONF_IMPORT_LIMIT: 8000,
    CONF_EXPORT_LIMIT: 5000,
    CONF_PRICE_IMPORT_SENSOR: "sensor.import_price",
    CONF_PRICE_EXPORT_SENSOR: "sensor.export_price",
}

GRID_INVALID_DATA = [
    ({CONF_NAME: "", CONF_IMPORT_LIMIT: 5000}, "cannot be empty"),
    ({CONF_NAME: "Test", CONF_IMPORT_LIMIT: -1000}, "too small"),
]

GRID_PARTICIPANT_SCENARIOS = [
    (
        {
            CONF_NAME: "Sensor Grid",
            CONF_IMPORT_LIMIT: 8000,
            CONF_EXPORT_LIMIT: 5000,
            CONF_PRICE_IMPORT_SENSOR: "sensor.import_price",
            CONF_PRICE_EXPORT_SENSOR: "sensor.export_price",
        },
        "sensor",
    ),
]


async def test_grid_schema_basic_validation(hass: HomeAssistant):
    """Test basic grid schema validation."""
    schema = get_grid_schema()
    result = schema(GRID_VALID_DATA)

    assert result[CONF_NAME] == GRID_VALID_DATA[CONF_NAME]
    assert result[CONF_IMPORT_LIMIT] == GRID_VALID_DATA[CONF_IMPORT_LIMIT]
    assert result[CONF_EXPORT_LIMIT] == GRID_VALID_DATA[CONF_EXPORT_LIMIT]


async def test_grid_schema_with_sensors(hass: HomeAssistant):
    """Test grid schema with sensor-based pricing."""
    schema = get_grid_schema()
    result = schema(GRID_SENSOR_DATA)

    assert result[CONF_NAME] == GRID_SENSOR_DATA[CONF_NAME]
    assert result[CONF_PRICE_IMPORT_SENSOR] == GRID_SENSOR_DATA[CONF_PRICE_IMPORT_SENSOR]
    assert result[CONF_PRICE_EXPORT_SENSOR] == GRID_SENSOR_DATA[CONF_PRICE_EXPORT_SENSOR]


@pytest.mark.parametrize("invalid_data,expected_error", GRID_INVALID_DATA)
async def test_grid_schema_validation_errors(
    hass: HomeAssistant,
    invalid_data: dict,
    expected_error: str,
):
    """Test grid schema validation with invalid data."""
    schema = get_grid_schema()

    try:
        schema(invalid_data)
        assert False, f"Expected validation error for {invalid_data}"
    except Exception as e:
        assert expected_error in str(e).lower()


@pytest.mark.parametrize("grid_data", GRID_PARTICIPANT_SCENARIOS)
async def test_grid_participant_creation(
    hass: HomeAssistant,
    grid_data: dict,
):
    """Test grid participant creation with various configurations."""
    participant = create_grid_participant(grid_data)

    assert participant["type"] == ELEMENT_TYPE_GRID
    assert participant[CONF_IMPORT_LIMIT] == grid_data[CONF_IMPORT_LIMIT]
    assert CONF_PRICE_IMPORT_SENSOR in participant
    assert CONF_PRICE_EXPORT_SENSOR in participant
