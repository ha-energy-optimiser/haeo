"""Test data and validation for net flow configuration."""

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_NAME

from custom_components.haeo.flows.net import (
    get_net_schema,
    create_net_participant,
)
from custom_components.haeo.const import (
    ENTITY_TYPE_NET,
)


# Net-specific test data
NET_VALID_DATA = {
    CONF_NAME: "Test Net",
}

NET_INVALID_DATA = [
    ({CONF_NAME: ""}, "cannot be empty"),
]

NET_PARTICIPANT_SCENARIOS = [
    # Basic net
    ({CONF_NAME: "House Net"}, "basic"),
    ({CONF_NAME: "Solar System Net"}, "basic"),
]


@pytest.fixture
def valid_net_data():
    """Get valid net test data."""
    return NET_VALID_DATA.copy()


async def test_net_schema_basic_validation(hass: HomeAssistant):
    """Test basic net schema validation."""
    schema = get_net_schema()
    result = schema(NET_VALID_DATA)

    assert result[CONF_NAME] == NET_VALID_DATA[CONF_NAME]


@pytest.mark.parametrize("invalid_data,expected_error", NET_INVALID_DATA)
async def test_net_schema_validation_errors(
    hass: HomeAssistant,
    invalid_data: dict,
    expected_error: str,
):
    """Test net schema validation with invalid data."""
    schema = get_net_schema()

    try:
        schema(invalid_data)
        assert False, f"Expected validation error for {invalid_data}"
    except Exception as e:
        assert expected_error in str(e).lower()


@pytest.mark.parametrize("net_data,expected_type", NET_PARTICIPANT_SCENARIOS)
async def test_net_participant_creation(
    hass: HomeAssistant,
    net_data: dict,
    expected_type: str,
):
    """Test net participant creation with various configurations."""
    participant = create_net_participant(net_data)

    assert participant["type"] == ENTITY_TYPE_NET
    assert participant[CONF_NAME] == net_data[CONF_NAME]
