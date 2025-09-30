"""Test the HAEO config flow."""

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.haeo.config_flow import HaeoConfigFlow
from custom_components.haeo.const import CONF_ENTITIES, CONF_CONNECTIONS


async def test_config_flow_user_step(hass: HomeAssistant):
    """Test the initial user step."""
    flow = HaeoConfigFlow()
    flow.hass = hass

    result = await flow.async_step_user()

    assert result["type"] == FlowResultType.MENU
    assert "add_entity" in result["menu_options"]
    assert "add_connection" in result["menu_options"]
    assert "finish" in result["menu_options"]


async def test_config_flow_add_battery(hass: HomeAssistant):
    """Test adding a battery entity."""
    flow = HaeoConfigFlow()
    flow.hass = hass

    # First add entity step
    result = await flow.async_step_add_entity({"name": "test_battery", "entity_type": "battery"})

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "configure_battery"

    # Configure battery
    result = await flow.async_step_configure_battery(
        {
            "capacity": 10000,
            "initial_charge_percentage": 50,
            "efficiency": 0.95,
        }
    )

    assert result["type"] == FlowResultType.MENU
    assert len(flow.entities) == 1
    assert flow.entities[0]["name"] == "test_battery"
    assert flow.entities[0]["entity_type"] == "battery"


async def test_config_flow_add_grid(hass: HomeAssistant):
    """Test adding a grid entity."""
    flow = HaeoConfigFlow()
    flow.hass = hass

    # First add entity step
    result = await flow.async_step_add_entity({"name": "test_grid", "entity_type": "grid"})

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "configure_grid"

    # Configure grid
    result = await flow.async_step_configure_grid(
        {
            "import_limit": 10000,
            "export_limit": 5000,
        }
    )

    assert result["type"] == FlowResultType.MENU
    assert len(flow.entities) == 1
    assert flow.entities[0]["name"] == "test_grid"
    assert flow.entities[0]["entity_type"] == "grid"


async def test_config_flow_duplicate_entity_name(hass: HomeAssistant):
    """Test adding entity with duplicate name."""
    flow = HaeoConfigFlow()
    flow.hass = hass
    flow.entities = [{"name": "existing_entity", "entity_type": "battery"}]

    result = await flow.async_step_add_entity({"name": "existing_entity", "entity_type": "grid"})

    assert result["type"] == FlowResultType.FORM
    assert "name_exists" in result["errors"]["name"]


async def test_config_flow_add_connection(hass: HomeAssistant):
    """Test adding a connection."""
    flow = HaeoConfigFlow()
    flow.hass = hass
    flow.entities = [{"name": "battery1", "entity_type": "battery"}, {"name": "grid1", "entity_type": "grid"}]

    result = await flow.async_step_add_connection(
        {
            "source": "battery1",
            "target": "grid1",
            "max_power": 5000,
        }
    )

    assert result["type"] == FlowResultType.MENU
    assert len(flow.connections) == 1
    assert flow.connections[0]["source"] == "battery1"
    assert flow.connections[0]["target"] == "grid1"


async def test_config_flow_connection_same_entity(hass: HomeAssistant):
    """Test adding connection with same source and target."""
    flow = HaeoConfigFlow()
    flow.hass = hass
    flow.entities = [{"name": "entity1", "entity_type": "battery"}]

    result = await flow.async_step_add_connection(
        {
            "source": "entity1",
            "target": "entity1",
        }
    )

    assert result["type"] == FlowResultType.FORM
    assert "same_entity" in result["errors"]["base"]


async def test_config_flow_connection_no_entities(hass: HomeAssistant):
    """Test adding connection with no entities."""
    flow = HaeoConfigFlow()
    flow.hass = hass

    result = await flow.async_step_add_connection()

    assert result["type"] == FlowResultType.FORM
    assert "no_entities" in result["errors"]["base"]


async def test_config_flow_finish_no_entities(hass: HomeAssistant):
    """Test finishing without entities."""
    flow = HaeoConfigFlow()
    flow.hass = hass

    result = await flow.async_step_finish()

    assert result["type"] == FlowResultType.FORM
    assert "no_entities" in result["errors"]["base"]


async def test_config_flow_finish_success(hass: HomeAssistant):
    """Test successful completion."""
    flow = HaeoConfigFlow()
    flow.hass = hass
    flow.entities = [
        {"name": "test_battery", "entity_type": "battery", "config": {"capacity": 10000}},
        {"name": "test_grid", "entity_type": "grid", "config": {"import_limit": 10000, "export_limit": 5000}},
    ]
    flow.connections = [{"source": "test_battery", "target": "test_grid"}]

    result = await flow.async_step_finish()

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert CONF_ENTITIES in result["data"]
    assert CONF_CONNECTIONS in result["data"]
    assert len(result["data"][CONF_ENTITIES]) == 2
    assert len(result["data"][CONF_CONNECTIONS]) == 1


async def test_config_flow_grid_pricing_methods(hass: HomeAssistant):
    """Test grid configuration with different pricing methods."""
    flow = HaeoConfigFlow()
    flow.hass = hass

    # Test with sensor-based pricing
    result = await flow.async_step_add_entity({"name": "test_grid_sensor", "entity_type": "grid"})

    result = await flow.async_step_configure_grid(
        {
            "import_limit": 10000,
            "export_limit": 5000,
            "pricing_method": "sensors",
            "price_import_sensor": "sensor.import_price",
            "price_export_sensor": "sensor.export_price",
        }
    )

    assert result["type"] == FlowResultType.MENU
    grid = flow.entities[0]
    assert grid["config"]["price_import_sensor"] == "sensor.import_price"
    assert grid["config"]["price_export_sensor"] == "sensor.export_price"
    assert "price_import" not in grid["config"]
    assert "price_export" not in grid["config"]


async def test_config_flow_grid_constant_pricing(hass: HomeAssistant):
    """Test grid configuration with constant pricing."""
    flow = HaeoConfigFlow()
    flow.hass = hass

    result = await flow.async_step_add_entity({"name": "test_grid_constant", "entity_type": "grid"})

    result = await flow.async_step_configure_grid(
        {
            "import_limit": 12000,
            "export_limit": 8000,
            "pricing_method": "constants",
            "price_import_constant": 0.30,
            "price_export_constant": 0.12,
        }
    )

    assert result["type"] == FlowResultType.MENU
    grid = flow.entities[0]
    assert grid["config"]["price_import"] == 0.30
    assert grid["config"]["price_export"] == 0.12
    assert "price_import_sensor" not in grid["config"]
    assert "price_export_sensor" not in grid["config"]


async def test_config_flow_add_generator(hass: HomeAssistant):
    """Test adding a generator entity."""
    flow = HaeoConfigFlow()
    flow.hass = hass

    result = await flow.async_step_add_entity({"name": "solar_panels", "entity_type": "generator"})

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "configure_forecast_entity"

    result = await flow.async_step_configure_forecast_entity(
        {
            "forecast_sensors": "sensor.solar_forecast",
            "forecast_aggregation": "sum",
        }
    )

    assert result["type"] == FlowResultType.MENU
    assert len(flow.entities) == 1
    assert flow.entities[0]["name"] == "solar_panels"
    assert flow.entities[0]["entity_type"] == "generator"
    assert flow.entities[0]["config"]["forecast_sensors"] == "sensor.solar_forecast"


async def test_config_flow_add_load(hass: HomeAssistant):
    """Test adding a load entity."""
    flow = HaeoConfigFlow()
    flow.hass = hass

    result = await flow.async_step_add_entity({"name": "home_load", "entity_type": "load"})

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "configure_forecast_entity"

    result = await flow.async_step_configure_forecast_entity(
        {
            "forecast_sensors": "sensor.load_forecast",
            "forecast_aggregation": "sum",
        }
    )

    assert result["type"] == FlowResultType.MENU
    assert len(flow.entities) == 1
    assert flow.entities[0]["name"] == "home_load"
    assert flow.entities[0]["entity_type"] == "load"


async def test_config_flow_add_net(hass: HomeAssistant):
    """Test adding a net entity."""
    flow = HaeoConfigFlow()
    flow.hass = hass

    result = await flow.async_step_add_entity({"name": "net_power", "entity_type": "net"})

    # Net entities don't need additional configuration
    assert result["type"] == FlowResultType.MENU
    assert len(flow.entities) == 1
    assert flow.entities[0]["name"] == "net_power"
    assert flow.entities[0]["entity_type"] == "net"


async def test_config_flow_battery_with_optional_fields(hass: HomeAssistant):
    """Test battery configuration with optional fields."""
    flow = HaeoConfigFlow()
    flow.hass = hass

    result = await flow.async_step_add_entity({"name": "advanced_battery", "entity_type": "battery"})

    result = await flow.async_step_configure_battery(
        {
            "capacity": 25000,
            "initial_charge_percentage": 80,
            "min_charge_percentage": 20,
            "max_charge_percentage": 95,
            "efficiency": 0.92,
            "max_charge_power": 7500,
            "max_discharge_power": 7500,
            "current_charge_sensor": "sensor.battery_soc",
        }
    )

    assert result["type"] == FlowResultType.MENU
    battery = flow.entities[0]
    assert battery["config"]["capacity"] == 25000
    assert battery["config"]["initial_charge_percentage"] == 80
    assert battery["config"]["min_charge_percentage"] == 20
    assert battery["config"]["max_charge_percentage"] == 95
    assert battery["config"]["efficiency"] == 0.92
    assert battery["config"]["max_charge_power"] == 7500
    assert battery["config"]["max_discharge_power"] == 7500
    assert battery["config"]["current_charge_sensor"] == "sensor.battery_soc"


async def test_config_flow_menu_options_with_entities(hass: HomeAssistant):
    """Test menu options when entities exist."""
    flow = HaeoConfigFlow()
    flow.hass = hass
    flow.entities = [{"name": "test_battery", "entity_type": "battery"}]

    result = await flow.async_step_user()

    assert result["type"] == FlowResultType.MENU
    menu_options = result["menu_options"]
    assert "add_entity" in menu_options
    assert "add_connection" in menu_options
    assert "manage_existing" in menu_options
    assert "finish" in menu_options
    assert "quick_setup" not in menu_options  # Should not appear when entities exist


async def test_config_flow_menu_options_empty(hass: HomeAssistant):
    """Test menu options when no entities exist."""
    flow = HaeoConfigFlow()
    flow.hass = hass

    result = await flow.async_step_user()

    assert result["type"] == FlowResultType.MENU
    menu_options = result["menu_options"]
    assert "add_entity" in menu_options
    assert "add_connection" in menu_options
    assert "finish" in menu_options
