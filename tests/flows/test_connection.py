"""Test data and validation for connection flow configuration."""

import pytest
from homeassistant.core import HomeAssistant

from custom_components.haeo.flows.connection import (
    get_connection_schema,
    create_connection_participant,
    validate_connection_config,
)
from custom_components.haeo.const import (
    CONF_NAME,
    CONF_SOURCE,
    CONF_TARGET,
    CONF_MIN_POWER,
    CONF_MAX_POWER,
    ELEMENT_TYPE_BATTERY,
    ELEMENT_TYPE_GRID,
    ELEMENT_TYPE_GENERATOR,
    ELEMENT_TYPE_LOAD_FIXED,
)


# Mock participants for testing
MOCK_PARTICIPANTS = {
    "battery_1": {"type": ELEMENT_TYPE_BATTERY, "name": "Battery 1"},
    "grid_1": {"type": ELEMENT_TYPE_GRID, "name": "Grid 1"},
    "solar_1": {"type": ELEMENT_TYPE_GENERATOR, "name": "Solar 1"},
    "house_load": {"type": ELEMENT_TYPE_LOAD_FIXED, "name": "House Load"},
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
    # Schema validation only checks basic field validation, not logical constraints
    # Logical constraints like self-connections and power range validation are handled by custom validation
]

CONNECTION_PARTICIPANT_SCENARIOS = [
    # Unidirectional connection (battery-grid) - only forward flow
    (
        {
            CONF_NAME: "Battery to Grid",
            CONF_SOURCE: "battery_1",
            CONF_TARGET: "grid_1",
            CONF_MIN_POWER: 0,
            CONF_MAX_POWER: 2000,
        },
        "unidirectional",
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
    # True bidirectional connection (battery-grid with reverse flow)
    (
        {
            CONF_NAME: "Battery Grid Bidirectional",
            CONF_SOURCE: "battery_1",
            CONF_TARGET: "grid_1",
            CONF_MIN_POWER: -1000,  # Allow reverse flow up to 1000W
            CONF_MAX_POWER: 2000,  # Allow forward flow up to 2000W
        },
        "bidirectional",
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
        # For bidirectional connections, max_power should be positive and min_power can be negative
        assert participant[CONF_MAX_POWER] > 0
        # min_power can be negative for true bidirectional connections
    elif expected_type == "unidirectional":
        assert participant[CONF_MIN_POWER] >= 0


def validate_connection_config_helper(min_power: float | None = None, max_power: float | None = None) -> dict[str, str]:
    """Helper function to test connection validation with specific power limits."""
    config = {
        CONF_NAME: "Test Connection",
        CONF_SOURCE: "battery_1",
        CONF_TARGET: "grid_1",
    }
    if min_power is not None:
        config[CONF_MIN_POWER] = min_power
    if max_power is not None:
        config[CONF_MAX_POWER] = max_power

    return validate_connection_config(config)


class TestValidateConnectionConfig:
    """Test connection configuration validation."""

    def test_valid_connection_config(self):
        """Test validation of valid connection config."""
        errors = validate_connection_config_helper(min_power=0, max_power=2000)
        assert errors == {}

    def test_self_connection_error(self):
        """Test validation error for self-connection."""
        config = {
            CONF_NAME: "Battery to Battery",
            CONF_SOURCE: "battery_1",
            CONF_TARGET: "battery_1",  # Same as source
            CONF_MIN_POWER: 0,
            CONF_MAX_POWER: 2000,
        }

        errors = validate_connection_config(config)

        assert CONF_TARGET in errors
        assert "cannot_connect_to_self" in errors[CONF_TARGET]

    def test_min_power_greater_than_max_power_error(self):
        """Test validation error when min power exceeds max power."""
        errors = validate_connection_config_helper(min_power=3000, max_power=2000)
        assert CONF_MIN_POWER in errors
        assert "min_power_too_high" in errors[CONF_MIN_POWER]

    def test_min_power_equals_max_power_valid(self):
        """Test that min power equal to max power is valid."""
        errors = validate_connection_config_helper(min_power=2000, max_power=2000)
        assert errors == {}

    def test_no_max_power_specified(self):
        """Test validation when max power is not specified."""
        errors = validate_connection_config_helper(min_power=0)
        assert errors == {}

    def test_no_min_power_specified(self):
        """Test validation when min power is not specified."""
        errors = validate_connection_config_helper(max_power=2000)
        assert errors == {}

    def test_empty_config(self):
        """Test validation of empty config."""
        config = {}

        errors = validate_connection_config(config)

        # Should not crash, but may have different behavior since required fields are missing
        assert isinstance(errors, dict)

    def test_negative_min_power_with_positive_max_power(self):
        """Test validation with negative min power and positive max power (valid bidirectional)."""
        errors = validate_connection_config_helper(min_power=-1000, max_power=2000)
        assert errors == {}

    def test_unlimited_connection_validation(self):
        """Test validation with no power limits (unlimited connection)."""
        errors = validate_connection_config_helper()
        assert errors == {}

    def test_negative_min_power_allowed_independently(self):
        """Test that negative min_power is allowed independently."""
        errors = validate_connection_config_helper(min_power=-100)
        assert errors == {}

    def test_negative_max_power_allowed_independently(self):
        """Test that negative max_power is allowed independently (though unusual)."""
        errors = validate_connection_config_helper(max_power=-100)
        assert errors == {}
