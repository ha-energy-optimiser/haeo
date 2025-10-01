"""Test battery config flow."""

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_NAME

from custom_components.haeo.flows.battery import (
    get_battery_schema,
    create_battery_participant,
)
from custom_components.haeo.const import (
    DOMAIN,
    ELEMENT_TYPE_BATTERY,
    CONF_CAPACITY,
    CONF_CURRENT_CHARGE_SENSOR,
    CONF_MIN_CHARGE_PERCENTAGE,
    CONF_MAX_CHARGE_PERCENTAGE,
    CONF_MAX_CHARGE_POWER,
    CONF_MAX_DISCHARGE_POWER,
    CONF_EFFICIENCY,
    CONF_CHARGE_COST,
    CONF_DISCHARGE_COST,
)


# Battery-specific test data
BATTERY_VALID_DATA = {
    CONF_NAME: "Test Battery",
    CONF_CAPACITY: 10000,
    CONF_CURRENT_CHARGE_SENSOR: "sensor.battery_charge",
    CONF_MAX_CHARGE_POWER: 5000,
    CONF_MAX_DISCHARGE_POWER: 5000,
    CONF_CHARGE_COST: 0.0,
    CONF_DISCHARGE_COST: 0.0,
}

BATTERY_DETAILED_DATA = {
    CONF_NAME: "Advanced Battery",
    CONF_CAPACITY: 10000,
    CONF_CURRENT_CHARGE_SENSOR: "sensor.battery_charge",
    CONF_MIN_CHARGE_PERCENTAGE: 10,
    CONF_MAX_CHARGE_PERCENTAGE: 90,
    CONF_MAX_CHARGE_POWER: 5000,
    CONF_MAX_DISCHARGE_POWER: 5000,
    CONF_EFFICIENCY: 0.95,
    CONF_CHARGE_COST: 0.05,
    CONF_DISCHARGE_COST: 0.03,
}

BATTERY_INVALID_DATA = [
    (
        {
            CONF_NAME: "",
            CONF_CAPACITY: 5000,
            CONF_CURRENT_CHARGE_SENSOR: "sensor.test",
            CONF_MAX_CHARGE_POWER: 5000,
            CONF_MAX_DISCHARGE_POWER: 5000,
            CONF_CHARGE_COST: 0.0,
            CONF_DISCHARGE_COST: 0.0,
        },
        "cannot be empty",
    ),
    (
        {
            CONF_NAME: "Test",
            CONF_CAPACITY: -1000,
            CONF_CURRENT_CHARGE_SENSOR: "sensor.test",
            CONF_MAX_CHARGE_POWER: 5000,
            CONF_MAX_DISCHARGE_POWER: 5000,
            CONF_CHARGE_COST: 0.0,
            CONF_DISCHARGE_COST: 0.0,
        },
        "too small",
    ),
]

BATTERY_PARTICIPANT_SCENARIOS = [
    # With efficiency
    (
        {
            CONF_NAME: "Test Battery",
            CONF_CAPACITY: 10000,
            CONF_CURRENT_CHARGE_SENSOR: "sensor.test",
            CONF_MAX_CHARGE_POWER: 5000,
            CONF_MAX_DISCHARGE_POWER: 5000,
            CONF_EFFICIENCY: 0.95,
            CONF_MIN_CHARGE_PERCENTAGE: 10,
            CONF_MAX_CHARGE_PERCENTAGE: 90,
            CONF_CHARGE_COST: 0.05,
            CONF_DISCHARGE_COST: 0.03,
        },
        0.95,
    ),
    # Without efficiency (should use default)
    (
        {
            CONF_NAME: "Test Battery",
            CONF_CAPACITY: 10000,
            CONF_CURRENT_CHARGE_SENSOR: "sensor.test",
            CONF_MAX_CHARGE_POWER: 5000,
            CONF_MAX_DISCHARGE_POWER: 5000,
            CONF_CHARGE_COST: 0.0,
            CONF_DISCHARGE_COST: 0.0,
        },
        None,
    ),
]


# Battery-specific test functions
async def test_battery_schema_basic_validation(hass: HomeAssistant):
    """Test basic battery schema validation."""
    schema = get_battery_schema()
    result = schema(BATTERY_VALID_DATA)

    assert result[CONF_NAME] == BATTERY_VALID_DATA[CONF_NAME]
    assert result[CONF_CAPACITY] == BATTERY_VALID_DATA[CONF_CAPACITY]
    assert result[CONF_CURRENT_CHARGE_SENSOR] == BATTERY_VALID_DATA[CONF_CURRENT_CHARGE_SENSOR]


async def test_battery_schema_with_optional_fields(hass: HomeAssistant):
    """Test battery schema with all optional fields."""
    schema = get_battery_schema()
    result = schema(BATTERY_DETAILED_DATA)

    assert result[CONF_NAME] == BATTERY_DETAILED_DATA[CONF_NAME]
    assert result[CONF_EFFICIENCY] == BATTERY_DETAILED_DATA[CONF_EFFICIENCY]
    assert result[CONF_MIN_CHARGE_PERCENTAGE] == BATTERY_DETAILED_DATA[CONF_MIN_CHARGE_PERCENTAGE]
    assert result[CONF_MAX_CHARGE_PERCENTAGE] == BATTERY_DETAILED_DATA[CONF_MAX_CHARGE_PERCENTAGE]


@pytest.mark.parametrize("invalid_data,expected_error", BATTERY_INVALID_DATA)
async def test_battery_schema_validation_errors(
    hass: HomeAssistant,
    invalid_data: dict,
    expected_error: str,
):
    """Test battery schema validation with invalid data."""
    schema = get_battery_schema()

    try:
        schema(invalid_data)
        assert False, f"Expected validation error for {invalid_data}"
    except Exception as e:
        assert expected_error in str(e).lower()


@pytest.mark.parametrize("battery_data,expected_efficiency", BATTERY_PARTICIPANT_SCENARIOS)
async def test_battery_participant_creation(
    hass: HomeAssistant,
    battery_data: dict,
    expected_efficiency: float | None,
):
    """Test battery participant creation with various configurations."""
    participant = create_battery_participant(battery_data)

    assert participant["type"] == ELEMENT_TYPE_BATTERY
    assert participant[CONF_CAPACITY] == battery_data[CONF_CAPACITY]
    assert participant[CONF_CURRENT_CHARGE_SENSOR] == battery_data[CONF_CURRENT_CHARGE_SENSOR]

    if expected_efficiency is not None:
        assert participant["efficiency"] == expected_efficiency


async def test_battery_participant_with_defaults(hass: HomeAssistant):
    """Test battery participant creation with minimal configuration."""
    minimal_config = {
        CONF_NAME: "Minimal Battery",
        CONF_CAPACITY: 5000,
        CONF_CURRENT_CHARGE_SENSOR: "sensor.battery_level",
        CONF_MAX_CHARGE_POWER: 2000,
        CONF_MAX_DISCHARGE_POWER: 2000,
    }

    participant = create_battery_participant(minimal_config)

    assert participant["type"] == ELEMENT_TYPE_BATTERY
    assert participant[CONF_CAPACITY] == 5000
    assert participant[CONF_CURRENT_CHARGE_SENSOR] == "sensor.battery_level"
    assert participant[CONF_MAX_CHARGE_POWER] == 2000
    assert participant[CONF_MAX_DISCHARGE_POWER] == 2000


@pytest.fixture
def mock_setup_entry():
    """Mock setup entry."""
    from unittest.mock import patch

    with patch("custom_components.haeo.async_setup_entry") as mock:
        mock.return_value = True
        yield mock


async def test_user_flow_success(hass: HomeAssistant, mock_setup_entry):
    """Test successful user flow."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    from homeassistant.config_entries import FlowResult

    assert result["type"] == FlowResult.FORM
    assert result["step_id"] == "user"

    # Test form submission
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Test Battery",
            CONF_CAPACITY: 10000,
            CONF_CURRENT_CHARGE_SENSOR: "sensor.battery_charge",
            CONF_MAX_CHARGE_POWER: 5000,
            CONF_MAX_DISCHARGE_POWER: 5000,
        },
    )
    assert result["type"] == FlowResult.CREATE_ENTRY
    assert result["title"] == "Test Battery"
    assert result["data"]["name"] == "Test Battery"
    assert result["data"]["capacity"] == 10000


async def test_user_flow_invalid_data(hass: HomeAssistant):
    """Test user flow with invalid data."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    from homeassistant.config_entries import FlowResult

    assert result["type"] == FlowResult.FORM

    # Test form submission with invalid data (empty name)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "",  # Invalid empty name
            CONF_CAPACITY: 10000,
            CONF_CURRENT_CHARGE_SENSOR: "sensor.battery_charge",
            CONF_MAX_CHARGE_POWER: 5000,
            CONF_MAX_DISCHARGE_POWER: 5000,
        },
    )
    assert result["type"] == FlowResult.FORM
    assert result["errors"] == {"name": "cannot_be_empty"}


async def test_user_flow_negative_capacity(hass: HomeAssistant):
    """Test user flow with negative capacity."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    from homeassistant.config_entries import FlowResult

    assert result["type"] == FlowResult.FORM

    # Test form submission with invalid data (negative capacity)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Test Battery",
            CONF_CAPACITY: -1000,  # Invalid negative capacity
            CONF_CURRENT_CHARGE_SENSOR: "sensor.battery_charge",
            CONF_MAX_CHARGE_POWER: 5000,
            CONF_MAX_DISCHARGE_POWER: 5000,
        },
    )
    assert result["type"] == FlowResult.FORM
    assert result["errors"] == {"capacity": "too_small"}


async def test_user_flow_optional_fields(hass: HomeAssistant, mock_setup_entry):
    """Test user flow with optional fields."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    from homeassistant.config_entries import FlowResult

    assert result["type"] == FlowResult.FORM

    # Test form submission with optional fields
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Advanced Battery",
            CONF_CAPACITY: 10000,
            CONF_CURRENT_CHARGE_SENSOR: "sensor.battery_charge",
            CONF_MAX_CHARGE_POWER: 5000,
            CONF_MAX_DISCHARGE_POWER: 5000,
            CONF_MIN_CHARGE_PERCENTAGE: 10,
            CONF_MAX_CHARGE_PERCENTAGE: 90,
            CONF_EFFICIENCY: 0.95,
        },
    )
    assert result["type"] == FlowResult.CREATE_ENTRY
    assert result["data"]["efficiency"] == 0.95
    assert result["data"]["min_charge_percentage"] == 10
    assert result["data"]["max_charge_percentage"] == 90
