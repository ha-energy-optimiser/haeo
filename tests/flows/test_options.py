"""Test options flow for HAEO hub management."""

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.const import CONF_NAME

from custom_components.haeo.flows.options import HubOptionsFlow
from custom_components.haeo.flows.connection import ENTITY_TYPE_CONNECTION
from custom_components.haeo.const import (
    ENTITY_TYPE_BATTERY,
    ENTITY_TYPE_GRID,
    ENTITY_TYPE_LOAD,
    ENTITY_TYPE_GENERATOR,
    ENTITY_TYPE_NET,
    CONF_CAPACITY,
)

from . import create_mock_config_entry


async def test_options_flow_init(hass: HomeAssistant):
    """Test options flow initialization."""
    config_entry = create_mock_config_entry()
    options_flow = HubOptionsFlow()
    options_flow._config_entry = config_entry

    result = await options_flow.async_step_init()

    assert result.get("type") == FlowResultType.MENU
    menu_options = result.get("menu_options", [])
    assert "add_participant" in menu_options
    assert "manage_participants" in menu_options
    assert "remove_participant" in menu_options


async def test_options_flow_add_participant_type_selection(hass: HomeAssistant):
    """Test participant type selection."""
    config_entry = create_mock_config_entry()
    options_flow = HubOptionsFlow()
    options_flow._config_entry = config_entry

    result = await options_flow.async_step_add_participant()

    assert result.get("type") == FlowResultType.FORM
    assert result.get("step_id") == "add_participant"


async def test_options_flow_route_to_grid_config(hass: HomeAssistant):
    """Test routing to grid configuration."""
    config_entry = create_mock_config_entry()
    options_flow = HubOptionsFlow()
    options_flow.hass = hass
    options_flow._config_entry = config_entry

    result = await options_flow.async_step_add_participant({"participant_type": ENTITY_TYPE_GRID})
    assert result.get("type") == FlowResultType.FORM
    assert result.get("step_id") == "configure_grid"


async def test_options_flow_route_to_load_config(hass: HomeAssistant):
    """Test routing to load configuration."""
    config_entry = create_mock_config_entry()
    options_flow = HubOptionsFlow()
    options_flow.hass = hass
    options_flow._config_entry = config_entry

    result = await options_flow.async_step_add_participant({"participant_type": ENTITY_TYPE_LOAD})
    assert result.get("type") == FlowResultType.FORM
    assert result.get("step_id") == "configure_load"


async def test_options_flow_route_to_generator_config(hass: HomeAssistant):
    """Test routing to generator configuration."""
    config_entry = create_mock_config_entry()
    options_flow = HubOptionsFlow()
    options_flow.hass = hass
    options_flow._config_entry = config_entry

    result = await options_flow.async_step_add_participant({"participant_type": ENTITY_TYPE_GENERATOR})
    assert result.get("type") == FlowResultType.FORM
    assert result.get("step_id") == "configure_generator"


async def test_options_flow_route_to_net_config(hass: HomeAssistant):
    """Test routing to net configuration."""
    config_entry = create_mock_config_entry()
    options_flow = HubOptionsFlow()
    options_flow.hass = hass
    options_flow._config_entry = config_entry

    result = await options_flow.async_step_add_participant({"participant_type": ENTITY_TYPE_NET})
    assert result.get("type") == FlowResultType.FORM
    assert result.get("step_id") == "configure_net"


async def test_options_flow_route_to_connection_config(hass: HomeAssistant):
    """Test routing to connection configuration."""
    config_data = {
        "integration_type": "hub",
        "name": "Test Hub",
        "participants": {
            "Battery1": {"type": ENTITY_TYPE_BATTERY, CONF_CAPACITY: 10000},
            "Grid1": {"type": ENTITY_TYPE_GRID, "import_limit": 5000},
        },
    }
    config_entry = create_mock_config_entry(data=config_data)
    options_flow = HubOptionsFlow()
    options_flow.hass = hass
    options_flow._config_entry = config_entry

    result = await options_flow.async_step_add_participant({"participant_type": ENTITY_TYPE_CONNECTION})
    assert result.get("type") == FlowResultType.FORM
    assert result.get("step_id") == "configure_connection"


async def test_options_flow_route_to_battery_config(hass: HomeAssistant):
    """Test routing to battery configuration."""
    config_entry = create_mock_config_entry()
    options_flow = HubOptionsFlow()
    options_flow._config_entry = config_entry

    result = await options_flow.async_step_add_participant({"participant_type": ENTITY_TYPE_BATTERY})

    assert result.get("type") == FlowResultType.FORM
    assert result.get("step_id") == "configure_battery"


async def test_options_flow_battery_duplicate_name(hass: HomeAssistant):
    """Test error when battery name already exists."""
    config_data = {
        "integration_type": "hub",
        "name": "Test Hub",
        "participants": {"Existing Battery": {"type": ENTITY_TYPE_BATTERY, CONF_CAPACITY: 5000}},
    }
    config_entry = create_mock_config_entry(data=config_data)
    options_flow = HubOptionsFlow()
    options_flow._config_entry = config_entry

    battery_config = {
        CONF_NAME: "Existing Battery",  # Same name as existing
        CONF_CAPACITY: 10000,
        "initial_charge_percentage": 50,
        "min_charge_percentage": 10,
        "max_charge_percentage": 90,
        "max_charge_power": 5000,
        "max_discharge_power": 5000,
        "efficiency": 0.95,
    }

    result = await options_flow.async_step_configure_battery(battery_config)

    assert result.get("type") == FlowResultType.FORM
    errors = result.get("errors") or {}
    assert errors.get(CONF_NAME) == "name_exists"


async def test_options_flow_no_participants(hass: HomeAssistant):
    """Test behavior when no participants exist."""
    config_entry = create_mock_config_entry()  # Empty participants
    options_flow = HubOptionsFlow()
    options_flow._config_entry = config_entry

    # Test manage participants with no participants
    result = await options_flow.async_step_manage_participants()
    assert result.get("type") == FlowResultType.ABORT
    assert result.get("reason") == "no_participants"

    # Test remove participants with no participants
    result = await options_flow.async_step_remove_participant()
    assert result.get("type") == FlowResultType.ABORT
    assert result.get("reason") == "no_participants"


async def test_options_flow_connection_insufficient_devices(hass: HomeAssistant):
    """Test connection configuration with insufficient devices."""
    config_data = {
        "integration_type": "hub",
        "name": "Test Hub",
        "participants": {"Battery1": {"type": ENTITY_TYPE_BATTERY, CONF_CAPACITY: 10000}},
    }
    config_entry = create_mock_config_entry(data=config_data)
    options_flow = HubOptionsFlow()
    options_flow._config_entry = config_entry

    result = await options_flow.async_step_configure_connection()

    assert result.get("type") == FlowResultType.ABORT
    assert result.get("reason") == "insufficient_devices"


async def test_options_flow_configure_grid_success(hass: HomeAssistant):
    """Test successful grid configuration."""
    config_entry = create_mock_config_entry()
    options_flow = HubOptionsFlow()
    options_flow.hass = hass
    options_flow._config_entry = config_entry

    # Mock the hass config entries update method to avoid real update
    from unittest.mock import patch

    with patch.object(hass.config_entries, "async_update_entry", return_value=None) as mock_update:
        # Test form display
        result = await options_flow.async_step_configure_grid()
        assert result.get("type") == FlowResultType.FORM
        assert result.get("step_id") == "configure_grid"

        # Test successful submission
        grid_data = {
            CONF_NAME: "Main Grid",
            "import_limit": 5000,
            "export_limit": 3000,
        }
        result = await options_flow.async_step_configure_grid(grid_data)
        assert result.get("type") == FlowResultType.CREATE_ENTRY
        mock_update.assert_called_once()


async def test_options_flow_configure_load_success(hass: HomeAssistant):
    """Test successful load configuration."""
    config_entry = create_mock_config_entry()
    options_flow = HubOptionsFlow()
    options_flow.hass = hass
    options_flow._config_entry = config_entry

    from unittest.mock import patch

    with patch.object(hass.config_entries, "async_update_entry", return_value=None):
        # Test form display
        result = await options_flow.async_step_configure_load()
        assert result.get("type") == FlowResultType.FORM
        assert result.get("step_id") == "configure_load"

        # Test successful submission
        load_data = {
            CONF_NAME: "House Load",
            "load_type": "fixed",
            "power": 2000,
        }
        result = await options_flow.async_step_configure_load(load_data)
        assert result.get("type") == FlowResultType.CREATE_ENTRY


async def test_options_flow_configure_generator_success(hass: HomeAssistant):
    """Test successful generator configuration."""
    config_entry = create_mock_config_entry()
    options_flow = HubOptionsFlow()
    options_flow.hass = hass
    options_flow._config_entry = config_entry

    from unittest.mock import patch

    with patch.object(hass.config_entries, "async_update_entry", return_value=None):
        # Test form display
        result = await options_flow.async_step_configure_generator()
        assert result.get("type") == FlowResultType.FORM
        assert result.get("step_id") == "configure_generator"

        # Test successful submission
        generator_data = {
            CONF_NAME: "Solar Panel",
            "max_power": 6000,
            "curtailment": True,
        }
        result = await options_flow.async_step_configure_generator(generator_data)
        assert result.get("type") == FlowResultType.CREATE_ENTRY


async def test_options_flow_configure_net_success(hass: HomeAssistant):
    """Test successful net configuration."""
    config_entry = create_mock_config_entry()
    options_flow = HubOptionsFlow()
    options_flow.hass = hass
    options_flow._config_entry = config_entry

    from unittest.mock import patch

    with patch.object(hass.config_entries, "async_update_entry", return_value=None):
        # Test form display
        result = await options_flow.async_step_configure_net()
        assert result.get("type") == FlowResultType.FORM
        assert result.get("step_id") == "configure_net"

        # Test successful submission
        net_data = {
            CONF_NAME: "Grid Net",
        }
        result = await options_flow.async_step_configure_net(net_data)
        assert result.get("type") == FlowResultType.CREATE_ENTRY


async def test_options_flow_configure_connection_success(hass: HomeAssistant):
    """Test successful connection configuration."""
    config_data = {
        "integration_type": "hub",
        "name": "Test Hub",
        "participants": {
            "Battery1": {"type": ENTITY_TYPE_BATTERY, CONF_CAPACITY: 10000},
            "Grid1": {"type": ENTITY_TYPE_GRID, "import_limit": 5000},
        },
    }
    config_entry = create_mock_config_entry(data=config_data)
    options_flow = HubOptionsFlow()
    options_flow.hass = hass
    options_flow._config_entry = config_entry

    from unittest.mock import patch

    with patch.object(hass.config_entries, "async_update_entry", return_value=None):
        # Test form display
        result = await options_flow.async_step_configure_connection()
        assert result.get("type") == FlowResultType.FORM
        assert result.get("step_id") == "configure_connection"

        # Test successful submission
        connection_data = {
            CONF_NAME: "Battery-Grid Connection",
            "source": "Battery1",
            "target": "Grid1",
            "max_power": 3000,
        }
        result = await options_flow.async_step_configure_connection(connection_data)
        assert result.get("type") == FlowResultType.CREATE_ENTRY


async def test_options_flow_grid_duplicate_name(hass: HomeAssistant):
    """Test grid configuration with duplicate name."""
    config_data = {
        "integration_type": "hub",
        "name": "Test Hub",
        "participants": {"Existing Grid": {"type": ENTITY_TYPE_GRID}},
    }
    config_entry = create_mock_config_entry(data=config_data)
    options_flow = HubOptionsFlow()
    options_flow._config_entry = config_entry

    grid_data = {
        CONF_NAME: "Existing Grid",  # Duplicate name
        "import_limit": 5000,
    }
    result = await options_flow.async_step_configure_grid(grid_data)
    assert result.get("type") == FlowResultType.FORM
    if "errors" in result and result["errors"]:
        assert result["errors"].get(CONF_NAME) == "name_exists"


async def test_options_flow_load_duplicate_name(hass: HomeAssistant):
    """Test load configuration with duplicate name."""
    config_data = {
        "integration_type": "hub",
        "name": "Test Hub",
        "participants": {"Existing Load": {"type": ENTITY_TYPE_LOAD}},
    }
    config_entry = create_mock_config_entry(data=config_data)
    options_flow = HubOptionsFlow()
    options_flow._config_entry = config_entry

    load_data = {
        CONF_NAME: "Existing Load",  # Duplicate name
        "load_type": "fixed",
        "power": 2000,
    }
    result = await options_flow.async_step_configure_load(load_data)
    assert result.get("type") == FlowResultType.FORM
    if "errors" in result and result["errors"]:
        assert result["errors"].get(CONF_NAME) == "name_exists"


async def test_options_flow_generator_duplicate_name(hass: HomeAssistant):
    """Test generator configuration with duplicate name."""
    config_data = {
        "integration_type": "hub",
        "name": "Test Hub",
        "participants": {"Existing Generator": {"type": ENTITY_TYPE_GENERATOR}},
    }
    config_entry = create_mock_config_entry(data=config_data)
    options_flow = HubOptionsFlow()
    options_flow._config_entry = config_entry

    generator_data = {
        CONF_NAME: "Existing Generator",  # Duplicate name
        "max_power": 6000,
    }
    result = await options_flow.async_step_configure_generator(generator_data)
    assert result.get("type") == FlowResultType.FORM
    if "errors" in result and result["errors"]:
        assert result["errors"].get(CONF_NAME) == "name_exists"


async def test_options_flow_net_duplicate_name(hass: HomeAssistant):
    """Test net configuration with duplicate name."""
    config_data = {
        "integration_type": "hub",
        "name": "Test Hub",
        "participants": {"Existing Net": {"type": ENTITY_TYPE_NET}},
    }
    config_entry = create_mock_config_entry(data=config_data)
    options_flow = HubOptionsFlow()
    options_flow._config_entry = config_entry

    net_data = {
        CONF_NAME: "Existing Net",  # Duplicate name
    }
    result = await options_flow.async_step_configure_net(net_data)
    assert result.get("type") == FlowResultType.FORM
    if "errors" in result and result["errors"]:
        assert result["errors"].get(CONF_NAME) == "name_exists"


async def test_options_flow_connection_duplicate_name(hass: HomeAssistant):
    """Test connection duplicate name error."""
    config_data = {
        "integration_type": "hub",
        "name": "Test Hub",
        "participants": {
            "Connection1": {"type": ENTITY_TYPE_CONNECTION, "source": "Battery1", "target": "Grid1"},
            "Battery1": {"type": ENTITY_TYPE_BATTERY, CONF_CAPACITY: 10000},
            "Grid1": {"type": ENTITY_TYPE_GRID, "import_limit": 5000},
        },
    }
    config_entry = create_mock_config_entry(data=config_data)
    options_flow = HubOptionsFlow()
    options_flow.hass = hass
    options_flow._config_entry = config_entry

    connection_data = {
        CONF_NAME: "Connection1",  # Duplicate name
        "source": "Battery1",
        "target": "Grid1",
        "max_power": 3000,
    }
    result = await options_flow.async_step_configure_connection(connection_data)
    assert result.get("type") == FlowResultType.FORM
    errors = result.get("errors")
    assert errors is not None
    assert errors.get(CONF_NAME) == "name_exists"


async def test_options_flow_remove_participant_form(hass: HomeAssistant):
    """Test remove participant form display."""
    config_data = {
        "integration_type": "hub",
        "name": "Test Hub",
        "participants": {
            "Battery1": {"type": ENTITY_TYPE_BATTERY, CONF_CAPACITY: 10000},
            "Grid1": {"type": ENTITY_TYPE_GRID, "import_limit": 5000},
        },
    }
    config_entry = create_mock_config_entry(data=config_data)
    options_flow = HubOptionsFlow()
    options_flow.hass = hass
    options_flow._config_entry = config_entry

    # Test form display
    result = await options_flow.async_step_remove_participant()
    assert result.get("type") == FlowResultType.FORM
    assert result.get("step_id") == "remove_participant"


async def test_options_flow_remove_participant_success(hass: HomeAssistant):
    """Test successful participant removal."""
    config_data = {
        "integration_type": "hub",
        "name": "Test Hub",
        "participants": {
            "Battery1": {"type": ENTITY_TYPE_BATTERY, CONF_CAPACITY: 10000},
            "Grid1": {"type": ENTITY_TYPE_GRID, "import_limit": 5000},
        },
    }
    config_entry = create_mock_config_entry(data=config_data)
    options_flow = HubOptionsFlow()
    options_flow.hass = hass
    options_flow._config_entry = config_entry

    from unittest.mock import patch

    with patch.object(hass.config_entries, "async_update_entry", return_value=None):
        # Test successful removal
        removal_data = {
            "participant": "Battery1",
        }
        result = await options_flow.async_step_remove_participant(removal_data)
        assert result.get("type") == FlowResultType.CREATE_ENTRY


async def test_options_flow_remove_participant_no_participants(hass: HomeAssistant):
    """Test remove participant with no participants."""
    config_entry = create_mock_config_entry()  # Empty participants
    options_flow = HubOptionsFlow()
    options_flow.hass = hass
    options_flow._config_entry = config_entry

    # Test no participants case
    result = await options_flow.async_step_remove_participant()
    assert result.get("type") == FlowResultType.ABORT
    assert result.get("reason") == "no_participants"


async def test_options_flow_configure_battery_form_display(hass: HomeAssistant):
    """Test battery configuration form display."""
    config_entry = create_mock_config_entry()
    options_flow = HubOptionsFlow()
    options_flow.hass = hass
    options_flow._config_entry = config_entry

    # Test form display without user input
    result = await options_flow.async_step_configure_battery()
    assert result.get("type") == FlowResultType.FORM
    assert result.get("step_id") == "configure_battery"


async def test_options_flow_configure_battery_success(hass: HomeAssistant):
    """Test successful battery configuration."""
    config_entry = create_mock_config_entry()
    options_flow = HubOptionsFlow()
    options_flow.hass = hass
    options_flow._config_entry = config_entry

    from unittest.mock import patch

    with patch.object(hass.config_entries, "async_update_entry", return_value=None):
        # Test successful submission
        battery_data = {
            CONF_NAME: "House Battery",
            CONF_CAPACITY: 10000,
            "current_charge_sensor": "sensor.battery_charge",
        }
        result = await options_flow.async_step_configure_battery(battery_data)
        assert result.get("type") == FlowResultType.CREATE_ENTRY


async def test_options_flow_manage_participants_form(hass: HomeAssistant):
    """Test manage participants form display."""
    config_data = {
        "integration_type": "hub",
        "name": "Test Hub",
        "participants": {
            "Battery1": {"type": ENTITY_TYPE_BATTERY, CONF_CAPACITY: 10000},
            "Grid1": {"type": ENTITY_TYPE_GRID, "import_limit": 5000},
        },
    }
    config_entry = create_mock_config_entry(data=config_data)
    options_flow = HubOptionsFlow()
    options_flow.hass = hass
    options_flow._config_entry = config_entry

    # Test form display
    result = await options_flow.async_step_manage_participants()
    assert result.get("type") == FlowResultType.FORM
    assert result.get("step_id") == "manage_participants"


async def test_options_flow_manage_participants_success(hass: HomeAssistant):
    """Test manage participants selection."""
    config_data = {
        "integration_type": "hub",
        "name": "Test Hub",
        "participants": {
            "Battery1": {"type": ENTITY_TYPE_BATTERY, CONF_CAPACITY: 10000},
            "Grid1": {"type": ENTITY_TYPE_GRID, "import_limit": 5000},
        },
    }
    config_entry = create_mock_config_entry(data=config_data)
    options_flow = HubOptionsFlow()
    options_flow.hass = hass
    options_flow._config_entry = config_entry

    # Test participant selection
    participant_data = {
        "participant": "Battery1",
    }
    result = await options_flow.async_step_manage_participants(participant_data)
    assert result.get("type") == FlowResultType.CREATE_ENTRY


async def test_options_flow_manage_participants_no_participants(hass: HomeAssistant):
    """Test manage participants with no participants."""
    config_entry = create_mock_config_entry()  # Empty participants
    options_flow = HubOptionsFlow()
    options_flow.hass = hass
    options_flow._config_entry = config_entry

    # Test no participants case
    result = await options_flow.async_step_manage_participants()
    assert result.get("type") == FlowResultType.ABORT
    assert result.get("reason") == "no_participants"
    """Test connection configuration with duplicate name."""
    config_data = {
        "integration_type": "hub",
        "name": "Test Hub",
        "participants": {
            "Battery1": {"type": ENTITY_TYPE_BATTERY, CONF_CAPACITY: 10000},
            "Grid1": {"type": ENTITY_TYPE_GRID, "import_limit": 5000},
            "Existing Connection": {"type": ENTITY_TYPE_CONNECTION},
        },
    }
    config_entry = create_mock_config_entry(data=config_data)
    options_flow = HubOptionsFlow()
    options_flow._config_entry = config_entry

    connection_data = {
        CONF_NAME: "Existing Connection",  # Duplicate name
        "source": "Battery1",
        "target": "Grid1",
    }
    result = await options_flow.async_step_configure_connection(connection_data)
    assert result.get("type") == FlowResultType.FORM
    if "errors" in result and result["errors"]:
        assert result["errors"].get(CONF_NAME) == "name_exists"
