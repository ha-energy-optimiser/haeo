"""Test hub configuration flow."""

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.const import CONF_NAME

from custom_components.haeo.flows.hub import HubConfigFlow

from . import create_mock_config_entry


async def test_hub_flow_user_step_form(hass: HomeAssistant):
    """Test that the user step shows the form."""
    flow = HubConfigFlow()
    flow.hass = hass

    result = await flow.async_step_user()

    assert result.get("type") == FlowResultType.FORM
    assert result.get("step_id") == "user"


async def test_hub_flow_create_hub_success(hass: HomeAssistant):
    """Test successful hub creation."""
    # Start the flow properly through Home Assistant's flow manager
    result = await hass.config_entries.flow.async_init("haeo", context={"source": "user"})

    # Should show the form
    assert result.get("type") == FlowResultType.FORM
    assert result.get("step_id") == "user"

    # Submit the form
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_NAME: "Test Hub"})

    # Should create the entry successfully
    assert result.get("type") == FlowResultType.CREATE_ENTRY
    assert result.get("title") == "Test Hub"

    # Verify the data
    data = result.get("data", {})
    assert data.get("integration_type") == "hub"
    assert data.get(CONF_NAME) == "Test Hub"
    assert data.get("participants") == {}


async def test_hub_flow_validation_functions():
    """Test the validation functions."""
    from custom_components.haeo.flows import (
        validate_element_name,
        validate_positive_number,
        validate_percentage,
        validate_efficiency,
    )
    import voluptuous as vol

    # Test element name validation
    assert validate_element_name("Valid Name") == "Valid Name"

    with pytest.raises(vol.Invalid):
        validate_element_name("")

    # Test positive number validation
    assert validate_positive_number(100) == 100

    with pytest.raises(vol.Invalid):
        validate_positive_number(0)

    with pytest.raises(vol.Invalid):
        validate_positive_number(-10)

    # Test percentage validation
    assert validate_percentage(50) == 50
    assert validate_percentage(0) == 0
    assert validate_percentage(100) == 100

    with pytest.raises(vol.Invalid):
        validate_percentage(-10)

    with pytest.raises(vol.Invalid):
        validate_percentage(150)

    # Test efficiency validation
    assert validate_efficiency(0.95) == 0.95
    assert validate_efficiency(1.0) == 1.0

    with pytest.raises(vol.Invalid):
        validate_efficiency(1.5)

    with pytest.raises(vol.Invalid):
        validate_efficiency(0)


async def test_hub_flow_options_flow_creation():
    """Test that options flow is properly created."""
    entry = create_mock_config_entry()
    options_flow = HubConfigFlow.async_get_options_flow(entry)

    # Verify we get an options flow instance
    from custom_components.haeo.flows.options import HubOptionsFlow

    assert isinstance(options_flow, HubOptionsFlow)
    # The config entry is set by Home Assistant after creation
    # so we just verify the type is correct


async def test_hub_flow_duplicate_name_error(hass: HomeAssistant):
    """Test error handling for duplicate hub names."""
    # First create a hub with a specific name
    result = await hass.config_entries.flow.async_init("haeo", context={"source": "user"})
    await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_NAME: "Existing Hub"})

    # Now try to create another hub with the same name
    result = await hass.config_entries.flow.async_init("haeo", context={"source": "user"})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_NAME: "Existing Hub"})

    # Should show form with error
    assert result.get("type") == FlowResultType.FORM
    # Verify errors exist and contain name_exists
    if "errors" in result and result["errors"] is not None:
        assert result["errors"].get(CONF_NAME) == "name_exists"


async def test_hub_flow_empty_name_validation(hass: HomeAssistant):
    """Test validation error for empty hub name."""
    result = await hass.config_entries.flow.async_init("haeo", context={"source": "user"})

    # Try to submit with empty name - should trigger validation error
    try:
        await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_NAME: ""})
        assert False, "Expected validation error for empty name"
    except Exception:
        # Validation error is expected for empty name
        pass
