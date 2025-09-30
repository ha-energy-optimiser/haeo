"""Common tests for all entity types using data-driven testing."""

import pytest
from homeassistant.core import HomeAssistant

from custom_components.haeo.flows.battery import BatteryConfigFlow
from custom_components.haeo.flows.grid import GridConfigFlow
from custom_components.haeo.flows.load import LoadConfigFlow
from custom_components.haeo.flows.generator import GeneratorConfigFlow
from custom_components.haeo.flows.net import NetConfigFlow

from . import (
    test_entity_duplicate_name_handling,
    test_entity_form_display,
    test_entity_successful_submission,
    test_entity_schema_validation,
)


# Map entity types to their flow classes
FLOW_CLASSES = {
    "battery": BatteryConfigFlow,
    "grid": GridConfigFlow,
    "load": LoadConfigFlow,
    "generator": GeneratorConfigFlow,
    "net": NetConfigFlow,
}


# Map entity types to their schema functions
SCHEMA_FUNCTIONS = {
    "battery": lambda: __import__(
        "custom_components.haeo.flows.battery", fromlist=["get_battery_schema"]
    ).get_battery_schema(),
    "grid": lambda: __import__("custom_components.haeo.flows.grid", fromlist=["get_grid_schema"]).get_grid_schema(),
    "load": lambda: __import__("custom_components.haeo.flows.load", fromlist=["get_load_schema"]).get_load_schema(),
    "generator": lambda: __import__(
        "custom_components.haeo.flows.generator", fromlist=["get_generator_schema"]
    ).get_generator_schema(),
    "net": lambda: __import__("custom_components.haeo.flows.net", fromlist=["get_net_schema"]).get_net_schema(),
}


@pytest.mark.parametrize("entity_type", ["battery", "grid", "load", "generator", "net"])
async def test_entity_form_display_generic(hass: HomeAssistant, entity_type):
    """Test form display for all entity types."""
    flow_class = FLOW_CLASSES[entity_type]
    await test_entity_form_display(hass, flow_class, entity_type)


@pytest.mark.parametrize("entity_type", ["battery", "grid", "load", "generator", "net"])
async def test_entity_successful_submission_generic(
    hass: HomeAssistant,
    entity_type,
    valid_entity_data,
):
    """Test successful submission for all entity types."""
    flow_class = FLOW_CLASSES[entity_type]
    await test_entity_successful_submission(hass, flow_class, entity_type, valid_entity_data)


@pytest.mark.parametrize("entity_type", ["battery", "grid", "load", "generator", "net"])
async def test_entity_duplicate_name_handling_generic(
    hass: HomeAssistant,
    entity_type,
    valid_entity_data,
    config_entry_with_existing_participant,
):
    """Test duplicate name handling for all entity types."""
    flow_class = FLOW_CLASSES[entity_type]
    await test_entity_duplicate_name_handling(
        hass, flow_class, entity_type, valid_entity_data, config_entry_with_existing_participant
    )


@pytest.mark.parametrize("entity_type", ["battery", "grid", "load", "generator", "net"])
async def test_entity_schema_validation_generic(
    hass: HomeAssistant,
    entity_type,
    valid_entity_data,
):
    """Test schema validation for all entity types."""
    schema_func = SCHEMA_FUNCTIONS[entity_type]

    # Define expected fields for each entity type
    expected_fields_map = {
        "battery": ["name", "capacity", "current_charge_sensor"],
        "grid": ["name", "import_limit", "export_limit"],
        "load": ["name", "load_type"],
        "generator": ["name", "max_power"],
        "net": ["name"],
    }

    expected_fields = expected_fields_map[entity_type]
    await test_entity_schema_validation(hass, entity_type, valid_entity_data, expected_fields, schema_func)
