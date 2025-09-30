"""Config flow for Home Assistant Energy Optimization integration."""

import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    DOMAIN,
    CONF_ENTITIES,
    CONF_CONNECTIONS,
    CONF_ENTITY_TYPE,
    CONF_ENTITY_CONFIG,
    ENTITY_TYPES,
    # Battery specific
    CONF_CAPACITY,
    CONF_INITIAL_CHARGE_PERCENTAGE,
    CONF_CURRENT_CHARGE_SENSOR,
    CONF_MIN_CHARGE_PERCENTAGE,
    CONF_MAX_CHARGE_PERCENTAGE,
    CONF_MAX_CHARGE_POWER,
    CONF_MAX_DISCHARGE_POWER,
    CONF_EFFICIENCY,
    # Grid specific
    CONF_IMPORT_LIMIT,
    CONF_EXPORT_LIMIT,
    CONF_PRICE_IMPORT,
    CONF_PRICE_EXPORT,
    CONF_PRICE_IMPORT_SENSOR,
    CONF_PRICE_EXPORT_SENSOR,
    # Forecast specific
    CONF_FORECAST_SENSORS,
    CONF_FORECAST_AGGREGATION,
    CONF_FORECAST_MULTIPLIER,
    FORECAST_AGGREGATION_SUM,
    FORECAST_AGGREGATION_MODES,
    # Defaults
    DEFAULT_EFFICIENCY,
    DEFAULT_MIN_CHARGE_PERCENTAGE,
    DEFAULT_MAX_CHARGE_PERCENTAGE,
    DEFAULT_INITIAL_CHARGE_PERCENTAGE,
)

_LOGGER = logging.getLogger(__name__)


class HaeoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HAEO."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""
        self.entities: list[dict] = []
        self.connections: list[dict] = []
        self.current_entity: Optional[dict] = None

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        """Handle the initial step."""
        menu_options = ["add_entity", "add_connection", "finish"]
        if self.entities or self.connections:
            menu_options.insert(-1, "manage_existing")

        return self.async_show_menu(
            step_id="user",
            menu_options=menu_options,
            description_placeholders={
                "entities_count": str(len(self.entities)),
                "connections_count": str(len(self.connections)),
                "entities_list": self._format_entities_list(),
                "connections_list": self._format_connections_list(),
            },
        )

    def _format_entities_list(self) -> str:
        """Format entities list for display."""
        if not self.entities:
            return "No entities configured"

        lines = []
        for entity in self.entities:
            entity_type = entity.get(CONF_ENTITY_TYPE, "unknown")
            entity_name = entity.get(CONF_NAME, "unnamed")
            lines.append(f"- {entity_name} ({entity_type})")
        return "\n".join(lines)

    def _format_connections_list(self) -> str:
        """Format connections list for display."""
        if not self.connections:
            return "No connections configured"

        lines = []
        for connection in self.connections:
            source = connection.get("source", "unknown")
            target = connection.get("target", "unknown")
            lines.append(f"- {source} → {target}")
        return "\n".join(lines)

    async def async_step_add_entity(self, user_input: Optional[Dict[str, Any]] = None):
        """Handle adding an entity."""
        errors = {}

        if user_input is not None:
            entity_name = user_input[CONF_NAME]
            entity_type = user_input[CONF_ENTITY_TYPE]

            # Check for duplicate names
            if any(entity[CONF_NAME] == entity_name for entity in self.entities):
                errors[CONF_NAME] = "name_exists"
            else:
                # Store current entity and move to specific configuration
                self.current_entity = {
                    CONF_NAME: entity_name,
                    CONF_ENTITY_TYPE: entity_type,
                    CONF_ENTITY_CONFIG: {},
                }

                # Move to entity-specific configuration
                if entity_type == "battery":
                    return await self.async_step_configure_battery()
                elif entity_type == "grid":
                    return await self.async_step_configure_grid()
                elif entity_type in ["load", "generator"]:
                    return await self.async_step_configure_forecast_entity()
                else:  # net
                    # Net entities don't need additional configuration
                    self.entities.append(self.current_entity)
                    self.current_entity = None
                    return await self.async_step_user()

        return self.async_show_form(
            step_id="add_entity",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME): cv.string,
                    vol.Required(CONF_ENTITY_TYPE): SelectSelector(
                        SelectSelectorConfig(
                            options=ENTITY_TYPES,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_manage_existing(self, user_input: Optional[Dict[str, Any]] = None):
        """Handle managing existing entities and connections."""
        if user_input is not None:
            action = user_input["action"]

            if action == "delete_entity":
                return await self.async_step_delete_entity()
            elif action == "delete_connection":
                return await self.async_step_delete_connection()
            else:  # back to user
                return await self.async_step_user()

        # Build management options based on what exists
        action_options = []
        if self.entities:
            action_options.append("delete_entity")
        if self.connections:
            action_options.append("delete_connection")
        action_options.append("back")

        return self.async_show_form(
            step_id="manage_existing",
            data_schema=vol.Schema(
                {
                    vol.Required("action"): SelectSelector(
                        SelectSelectorConfig(
                            options=action_options,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
            description_placeholders={
                "entities_list": self._format_entities_list(),
                "connections_list": self._format_connections_list(),
            },
        )

    async def async_step_delete_entity(self, user_input: Optional[Dict[str, Any]] = None):
        """Handle deleting an entity."""
        if user_input is not None:
            entity_name = user_input["entity"]

            # Remove the entity
            self.entities = [e for e in self.entities if e[CONF_NAME] != entity_name]

            # Remove any connections involving this entity
            self.connections = [
                c for c in self.connections if c["source"] != entity_name and c["target"] != entity_name
            ]

            return await self.async_step_user()

        if not self.entities:
            return await self.async_step_manage_existing()

        entity_options = [entity[CONF_NAME] for entity in self.entities]

        return self.async_show_form(
            step_id="delete_entity",
            data_schema=vol.Schema(
                {
                    vol.Required("entity"): SelectSelector(
                        SelectSelectorConfig(
                            options=entity_options,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
        )

    async def async_step_delete_connection(self, user_input: Optional[Dict[str, Any]] = None):
        """Handle deleting a connection."""
        if user_input is not None:
            connection_index = int(user_input["connection"])

            # Remove the connection
            if 0 <= connection_index < len(self.connections):
                self.connections.pop(connection_index)

            return await self.async_step_user()

        if not self.connections:
            return await self.async_step_manage_existing()

        connection_options = [str(i) for i, conn in enumerate(self.connections)]

        return self.async_show_form(
            step_id="delete_connection",
            data_schema=vol.Schema(
                {
                    vol.Required("connection"): SelectSelector(
                        SelectSelectorConfig(
                            options=connection_options,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
        )

    async def async_step_configure_battery(self, user_input: Optional[Dict[str, Any]] = None):
        """Configure battery entity."""
        if user_input is not None:
            assert self.current_entity is not None
            self.current_entity[CONF_ENTITY_CONFIG].update(user_input)
            self.entities.append(self.current_entity)
            self.current_entity = None
            return await self.async_step_user()

        return self.async_show_form(
            step_id="configure_battery",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CAPACITY): NumberSelector(
                        NumberSelectorConfig(
                            mode=NumberSelectorMode.BOX,
                            min=1.0,
                            unit_of_measurement="Wh",
                        )
                    ),
                    vol.Optional(
                        CONF_INITIAL_CHARGE_PERCENTAGE, default=DEFAULT_INITIAL_CHARGE_PERCENTAGE
                    ): NumberSelector(
                        NumberSelectorConfig(
                            mode=NumberSelectorMode.BOX,
                            min=0,
                            max=100,
                            unit_of_measurement="%",
                        )
                    ),
                    vol.Optional(CONF_CURRENT_CHARGE_SENSOR): EntitySelector(EntitySelectorConfig(domain=["sensor"])),
                    vol.Optional(CONF_MIN_CHARGE_PERCENTAGE, default=DEFAULT_MIN_CHARGE_PERCENTAGE): NumberSelector(
                        NumberSelectorConfig(
                            mode=NumberSelectorMode.BOX,
                            min=0,
                            max=100,
                            unit_of_measurement="%",
                        )
                    ),
                    vol.Optional(CONF_MAX_CHARGE_PERCENTAGE, default=DEFAULT_MAX_CHARGE_PERCENTAGE): NumberSelector(
                        NumberSelectorConfig(
                            mode=NumberSelectorMode.BOX,
                            min=0,
                            max=100,
                            unit_of_measurement="%",
                        )
                    ),
                    vol.Optional(CONF_MAX_CHARGE_POWER): NumberSelector(
                        NumberSelectorConfig(
                            mode=NumberSelectorMode.BOX,
                            min=0.0,
                            unit_of_measurement="W",
                        )
                    ),
                    vol.Optional(CONF_MAX_DISCHARGE_POWER): NumberSelector(
                        NumberSelectorConfig(
                            mode=NumberSelectorMode.BOX,
                            min=0.0,
                            unit_of_measurement="W",
                        )
                    ),
                    vol.Optional(CONF_EFFICIENCY, default=DEFAULT_EFFICIENCY): NumberSelector(
                        NumberSelectorConfig(
                            mode=NumberSelectorMode.BOX,
                            min=0.0,
                            max=1.0,
                            step=0.01,
                        )
                    ),
                }
            ),
        )

    async def async_step_configure_grid(self, user_input: Optional[Dict[str, Any]] = None):
        """Configure grid entity with pricing options."""
        if user_input is not None:
            assert self.current_entity is not None
            # Store basic configuration
            self.current_entity[CONF_ENTITY_CONFIG].update(
                {
                    CONF_IMPORT_LIMIT: user_input[CONF_IMPORT_LIMIT],
                    CONF_EXPORT_LIMIT: user_input[CONF_EXPORT_LIMIT],
                }
            )

            # Process pricing configuration
            pricing_method = user_input.get("pricing_method", "sensors")

            if pricing_method == "sensors":
                # Use sensor-based pricing
                if user_input.get("price_import_sensor"):
                    self.current_entity[CONF_ENTITY_CONFIG][CONF_PRICE_IMPORT_SENSOR] = user_input[
                        "price_import_sensor"
                    ]
                if user_input.get("price_export_sensor"):
                    self.current_entity[CONF_ENTITY_CONFIG][CONF_PRICE_EXPORT_SENSOR] = user_input[
                        "price_export_sensor"
                    ]
            else:  # constants
                # Use constant pricing
                if user_input.get("price_import_constant") is not None:
                    self.current_entity[CONF_ENTITY_CONFIG][CONF_PRICE_IMPORT] = user_input["price_import_constant"]
                if user_input.get("price_export_constant") is not None:
                    self.current_entity[CONF_ENTITY_CONFIG][CONF_PRICE_EXPORT] = user_input["price_export_constant"]

            self.entities.append(self.current_entity)
            self.current_entity = None
            return await self.async_step_user()

        return self.async_show_form(
            step_id="configure_grid",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_IMPORT_LIMIT): NumberSelector(
                        NumberSelectorConfig(
                            mode=NumberSelectorMode.BOX,
                            min=0.0,
                            unit_of_measurement="W",
                        )
                    ),
                    vol.Required(CONF_EXPORT_LIMIT): NumberSelector(
                        NumberSelectorConfig(
                            mode=NumberSelectorMode.BOX,
                            min=0.0,
                            unit_of_measurement="W",
                        )
                    ),
                    vol.Required("pricing_method", default="sensors"): SelectSelector(
                        SelectSelectorConfig(
                            options=[
                                "sensors",  # Use sensor-based pricing
                                "constants",  # Use constant pricing
                            ],
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional("price_import_sensor", description="Import price sensor"): EntitySelector(
                        EntitySelectorConfig(domain=["sensor"])
                    ),
                    vol.Optional("price_export_sensor", description="Export price sensor"): EntitySelector(
                        EntitySelectorConfig(domain=["sensor"])
                    ),
                    vol.Optional(
                        "price_import_constant", description="Constant import price (currency/kWh)"
                    ): NumberSelector(
                        NumberSelectorConfig(
                            mode=NumberSelectorMode.BOX,
                            min=0.0,
                            step=0.01,
                        )
                    ),
                    vol.Optional(
                        "price_export_constant", description="Constant export price (currency/kWh)"
                    ): NumberSelector(
                        NumberSelectorConfig(
                            mode=NumberSelectorMode.BOX,
                            min=0.0,
                            step=0.01,
                        )
                    ),
                }
            ),
        )

    async def async_step_configure_forecast_entity(self, user_input: Optional[Dict[str, Any]] = None):
        """Configure load or generator entity with multiple forecasts."""
        if user_input is not None:
            # Process multiple forecast configuration
            forecast_config = {}

            # Handle multiple forecast sensors
            if "forecast_sensors" in user_input:
                forecast_config[CONF_FORECAST_SENSORS] = user_input["forecast_sensors"]

            # Handle aggregation mode
            if "aggregation_mode" in user_input:
                forecast_config[CONF_FORECAST_AGGREGATION] = user_input["aggregation_mode"]

            # Handle forecast multipliers (if provided)
            if "forecast_multipliers" in user_input and user_input["forecast_multipliers"]:
                forecast_config[CONF_FORECAST_MULTIPLIER] = user_input["forecast_multipliers"]

            assert self.current_entity is not None
            self.current_entity[CONF_ENTITY_CONFIG].update(forecast_config)
            self.entities.append(self.current_entity)
            self.current_entity = None
            return await self.async_step_user()

        assert self.current_entity is not None
        entity_type = self.current_entity[CONF_ENTITY_TYPE]

        return self.async_show_form(
            step_id="configure_forecast_entity",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "forecast_sensors", description="Comma-separated list of sensor entity IDs"
                    ): cv.string,
                    vol.Required("aggregation_mode", default=FORECAST_AGGREGATION_SUM): SelectSelector(
                        SelectSelectorConfig(
                            options=FORECAST_AGGREGATION_MODES,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional(
                        "forecast_multipliers", description="Optional: comma-separated multipliers for each sensor"
                    ): cv.string,
                }
            ),
            description_placeholders={"entity_type": entity_type},
        )

    async def async_step_add_connection(self, user_input: Optional[Dict[str, Any]] = None):
        """Handle adding a connection."""
        errors = {}

        if user_input is not None:
            source = user_input["source"]
            target = user_input["target"]

            if source == target:
                errors["base"] = "same_entity"
            elif any(
                (conn["source"] == source and conn["target"] == target)
                or (conn["source"] == target and conn["target"] == source)
                for conn in self.connections
            ):
                errors["base"] = "connection_exists"
            else:
                connection = {
                    "source": source,
                    "target": target,
                    "bidirectional": True,
                    "capacity": user_input.get("max_power"),
                    "reverse_capacity": user_input.get("reverse_capacity", user_input.get("max_power")),
                }
                self.connections.append(connection)
                return await self.async_step_user()

        if not self.entities:
            return self.async_show_form(
                step_id="add_connection",
                errors={"base": "no_entities"},
            )

        entity_options = [entity[CONF_NAME] for entity in self.entities]

        return self.async_show_form(
            step_id="add_connection",
            data_schema=vol.Schema(
                {
                    vol.Required("source"): SelectSelector(
                        SelectSelectorConfig(
                            options=entity_options,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Required("target"): SelectSelector(
                        SelectSelectorConfig(
                            options=entity_options,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional("max_power"): NumberSelector(
                        NumberSelectorConfig(
                            mode=NumberSelectorMode.BOX,
                            min=0.0,
                            unit_of_measurement="W",
                        )
                    ),
                    vol.Optional("reverse_capacity"): NumberSelector(
                        NumberSelectorConfig(
                            mode=NumberSelectorMode.BOX,
                            min=0.0,
                            unit_of_measurement="W",
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_finish(self, user_input: Optional[Dict[str, Any]] = None):
        """Finish configuration."""
        if not self.entities:
            return self.async_show_form(
                step_id="finish",
                errors={"base": "no_entities"},
            )

        title = f"HAEO ({len(self.entities)} entities)"

        return self.async_create_entry(
            title=title,
            data={
                CONF_ENTITIES: self.entities,
                CONF_CONNECTIONS: self.connections,
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return HaeoOptionsFlowHandler(config_entry)


class HaeoOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for HAEO."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        # Load existing configuration
        self.entities: list[dict] = config_entry.data.get(CONF_ENTITIES, []).copy()
        self.connections: list[dict] = config_entry.data.get(CONF_CONNECTIONS, []).copy()
        self.current_entity: Optional[dict] = None

    async def async_step_init(self, user_input: Optional[Dict[str, Any]] = None):
        """Manage the options."""
        if user_input is not None:
            action = user_input["action"]

            if action == "add_entity":
                return await self.async_step_add_entity()
            elif action == "add_connection":
                return await self.async_step_add_connection()
            elif action == "manage_existing":
                return await self.async_step_manage_existing()
            elif action == "save":
                return await self.async_step_save()

        # Build available actions
        action_options = [
            "add_entity",
            "add_connection",
        ]

        if self.entities or self.connections:
            action_options.append("manage_existing")

        action_options.append("save")

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required("action"): SelectSelector(
                        SelectSelectorConfig(
                            options=action_options,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
            description_placeholders={
                "entities_count": str(len(self.entities)),
                "connections_count": str(len(self.connections)),
                "entities_list": self._format_entities_list(),
                "connections_list": self._format_connections_list(),
            },
        )

    def _format_entities_list(self) -> str:
        """Format entities list for display."""
        if not self.entities:
            return "No entities configured"

        lines = []
        for entity in self.entities:
            entity_type = entity.get(CONF_ENTITY_TYPE, "unknown")
            entity_name = entity.get(CONF_NAME, "unnamed")
            lines.append(f"- {entity_name} ({entity_type})")
        return "\n".join(lines)

    def _format_connections_list(self) -> str:
        """Format connections list for display."""
        if not self.connections:
            return "No connections configured"

        lines = []
        for connection in self.connections:
            source = connection.get("source", "unknown")
            target = connection.get("target", "unknown")
            lines.append(f"- {source} → {target}")
        return "\n".join(lines)

    async def async_step_add_entity(self, user_input: Optional[Dict[str, Any]] = None):
        """Handle adding an entity."""
        errors = {}

        if user_input is not None:
            entity_name = user_input[CONF_NAME]
            entity_type = user_input[CONF_ENTITY_TYPE]

            # Check for duplicate names
            if any(entity[CONF_NAME] == entity_name for entity in self.entities):
                errors[CONF_NAME] = "name_exists"
            else:
                # Store current entity and move to specific configuration
                self.current_entity = {
                    CONF_NAME: entity_name,
                    CONF_ENTITY_TYPE: entity_type,
                    CONF_ENTITY_CONFIG: {},
                }

                # Move to entity-specific configuration
                if entity_type == "battery":
                    return await self.async_step_configure_battery()
                elif entity_type == "grid":
                    return await self.async_step_configure_grid()
                elif entity_type in ["load", "generator"]:
                    return await self.async_step_configure_forecast_entity()
                else:  # net
                    # Net entities don't need additional configuration
                    self.entities.append(self.current_entity)
                    self.current_entity = None
                    return await self.async_step_init()

        return self.async_show_form(
            step_id="add_entity",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME): cv.string,
                    vol.Required(CONF_ENTITY_TYPE): SelectSelector(
                        SelectSelectorConfig(
                            options=ENTITY_TYPES,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_configure_battery(self, user_input: Optional[Dict[str, Any]] = None):
        """Configure battery entity."""
        if user_input is not None:
            assert self.current_entity is not None
            self.current_entity[CONF_ENTITY_CONFIG].update(user_input)
            self.entities.append(self.current_entity)
            self.current_entity = None
            return await self.async_step_init()

        return self.async_show_form(
            step_id="configure_battery",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CAPACITY): NumberSelector(
                        NumberSelectorConfig(
                            mode=NumberSelectorMode.BOX,
                            min=1.0,
                            unit_of_measurement="Wh",
                        )
                    ),
                    vol.Optional(
                        CONF_INITIAL_CHARGE_PERCENTAGE, default=DEFAULT_INITIAL_CHARGE_PERCENTAGE
                    ): NumberSelector(
                        NumberSelectorConfig(
                            mode=NumberSelectorMode.BOX,
                            min=0,
                            max=100,
                            unit_of_measurement="%",
                        )
                    ),
                    vol.Optional(CONF_CURRENT_CHARGE_SENSOR): EntitySelector(EntitySelectorConfig(domain=["sensor"])),
                    vol.Optional(CONF_MIN_CHARGE_PERCENTAGE, default=DEFAULT_MIN_CHARGE_PERCENTAGE): NumberSelector(
                        NumberSelectorConfig(
                            mode=NumberSelectorMode.BOX,
                            min=0,
                            max=100,
                            unit_of_measurement="%",
                        )
                    ),
                    vol.Optional(CONF_MAX_CHARGE_PERCENTAGE, default=DEFAULT_MAX_CHARGE_PERCENTAGE): NumberSelector(
                        NumberSelectorConfig(
                            mode=NumberSelectorMode.BOX,
                            min=0,
                            max=100,
                            unit_of_measurement="%",
                        )
                    ),
                    vol.Optional(CONF_MAX_CHARGE_POWER): NumberSelector(
                        NumberSelectorConfig(
                            mode=NumberSelectorMode.BOX,
                            min=0.0,
                            unit_of_measurement="W",
                        )
                    ),
                    vol.Optional(CONF_MAX_DISCHARGE_POWER): NumberSelector(
                        NumberSelectorConfig(
                            mode=NumberSelectorMode.BOX,
                            min=0.0,
                            unit_of_measurement="W",
                        )
                    ),
                    vol.Optional(CONF_EFFICIENCY, default=DEFAULT_EFFICIENCY): NumberSelector(
                        NumberSelectorConfig(
                            mode=NumberSelectorMode.BOX,
                            min=0.0,
                            max=1.0,
                            step=0.01,
                        )
                    ),
                }
            ),
        )

    async def async_step_configure_grid(self, user_input: Optional[Dict[str, Any]] = None):
        """Configure grid entity with pricing options."""
        if user_input is not None:
            assert self.current_entity is not None
            # Store basic configuration
            self.current_entity[CONF_ENTITY_CONFIG].update(
                {
                    CONF_IMPORT_LIMIT: user_input[CONF_IMPORT_LIMIT],
                    CONF_EXPORT_LIMIT: user_input[CONF_EXPORT_LIMIT],
                }
            )

            # Process pricing configuration
            pricing_method = user_input.get("pricing_method", "sensors")

            if pricing_method == "sensors":
                # Use sensor-based pricing
                if user_input.get("price_import_sensor"):
                    self.current_entity[CONF_ENTITY_CONFIG][CONF_PRICE_IMPORT_SENSOR] = user_input[
                        "price_import_sensor"
                    ]
                if user_input.get("price_export_sensor"):
                    self.current_entity[CONF_ENTITY_CONFIG][CONF_PRICE_EXPORT_SENSOR] = user_input[
                        "price_export_sensor"
                    ]
            else:  # constants
                # Use constant pricing
                if user_input.get("price_import_constant") is not None:
                    self.current_entity[CONF_ENTITY_CONFIG][CONF_PRICE_IMPORT] = user_input["price_import_constant"]
                if user_input.get("price_export_constant") is not None:
                    self.current_entity[CONF_ENTITY_CONFIG][CONF_PRICE_EXPORT] = user_input["price_export_constant"]

            self.entities.append(self.current_entity)
            self.current_entity = None
            return await self.async_step_init()

        return self.async_show_form(
            step_id="configure_grid",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_IMPORT_LIMIT): NumberSelector(
                        NumberSelectorConfig(
                            mode=NumberSelectorMode.BOX,
                            min=0.0,
                            unit_of_measurement="W",
                        )
                    ),
                    vol.Required(CONF_EXPORT_LIMIT): NumberSelector(
                        NumberSelectorConfig(
                            mode=NumberSelectorMode.BOX,
                            min=0.0,
                            unit_of_measurement="W",
                        )
                    ),
                    vol.Required("pricing_method", default="sensors"): SelectSelector(
                        SelectSelectorConfig(
                            options=[
                                "sensors",  # Use sensor-based pricing
                                "constants",  # Use constant pricing
                            ],
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional("price_import_sensor", description="Import price sensor"): EntitySelector(
                        EntitySelectorConfig(domain=["sensor"])
                    ),
                    vol.Optional("price_export_sensor", description="Export price sensor"): EntitySelector(
                        EntitySelectorConfig(domain=["sensor"])
                    ),
                    vol.Optional(
                        "price_import_constant", description="Constant import price (currency/kWh)"
                    ): NumberSelector(
                        NumberSelectorConfig(
                            mode=NumberSelectorMode.BOX,
                            min=0.0,
                            step=0.01,
                        )
                    ),
                    vol.Optional(
                        "price_export_constant", description="Constant export price (currency/kWh)"
                    ): NumberSelector(
                        NumberSelectorConfig(
                            mode=NumberSelectorMode.BOX,
                            min=0.0,
                            step=0.01,
                        )
                    ),
                }
            ),
        )

    async def async_step_configure_forecast_entity(self, user_input: Optional[Dict[str, Any]] = None):
        """Configure load or generator entity with multiple forecasts."""
        if user_input is not None:
            # Process multiple forecast configuration
            forecast_config = {}

            # Handle multiple forecast sensors
            if "forecast_sensors" in user_input:
                forecast_config[CONF_FORECAST_SENSORS] = user_input["forecast_sensors"]

            # Handle aggregation mode
            if "aggregation_mode" in user_input:
                forecast_config[CONF_FORECAST_AGGREGATION] = user_input["aggregation_mode"]

            # Handle forecast multipliers (if provided)
            if "forecast_multipliers" in user_input and user_input["forecast_multipliers"]:
                forecast_config[CONF_FORECAST_MULTIPLIER] = user_input["forecast_multipliers"]

            assert self.current_entity is not None
            self.current_entity[CONF_ENTITY_CONFIG].update(forecast_config)
            self.entities.append(self.current_entity)
            self.current_entity = None
            return await self.async_step_init()

        assert self.current_entity is not None
        entity_type = self.current_entity[CONF_ENTITY_TYPE]

        return self.async_show_form(
            step_id="configure_forecast_entity",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "forecast_sensors", description="Comma-separated list of sensor entity IDs"
                    ): cv.string,
                    vol.Required("aggregation_mode", default=FORECAST_AGGREGATION_SUM): SelectSelector(
                        SelectSelectorConfig(
                            options=FORECAST_AGGREGATION_MODES,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional(
                        "forecast_multipliers", description="Optional: comma-separated multipliers for each sensor"
                    ): cv.string,
                }
            ),
            description_placeholders={"entity_type": entity_type},
        )

    async def async_step_add_connection(self, user_input: Optional[Dict[str, Any]] = None):
        """Handle adding a connection."""
        errors = {}

        if user_input is not None:
            source = user_input["source"]
            target = user_input["target"]

            if source == target:
                errors["base"] = "same_entity"
            elif any(
                (conn["source"] == source and conn["target"] == target)
                or (conn["source"] == target and conn["target"] == source)
                for conn in self.connections
            ):
                errors["base"] = "connection_exists"
            else:
                connection = {
                    "source": source,
                    "target": target,
                    "bidirectional": True,
                    "capacity": user_input.get("max_power"),
                    "reverse_capacity": user_input.get("reverse_capacity", user_input.get("max_power")),
                }
                self.connections.append(connection)
                return await self.async_step_init()

        if not self.entities:
            return self.async_show_form(
                step_id="add_connection",
                errors={"base": "no_entities"},
            )

        entity_options = [entity[CONF_NAME] for entity in self.entities]

        return self.async_show_form(
            step_id="add_connection",
            data_schema=vol.Schema(
                {
                    vol.Required("source"): SelectSelector(
                        SelectSelectorConfig(
                            options=entity_options,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Required("target"): SelectSelector(
                        SelectSelectorConfig(
                            options=entity_options,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional("max_power"): NumberSelector(
                        NumberSelectorConfig(
                            mode=NumberSelectorMode.BOX,
                            min=0.0,
                            unit_of_measurement="W",
                        )
                    ),
                    vol.Optional("reverse_capacity"): NumberSelector(
                        NumberSelectorConfig(
                            mode=NumberSelectorMode.BOX,
                            min=0.0,
                            unit_of_measurement="W",
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_manage_existing(self, user_input: Optional[Dict[str, Any]] = None):
        """Handle managing existing entities and connections."""
        if user_input is not None:
            action = user_input["action"]

            if action == "delete_entity":
                return await self.async_step_delete_entity()
            elif action == "delete_connection":
                return await self.async_step_delete_connection()
            else:  # back to init
                return await self.async_step_init()

        # Build management options based on what exists
        action_options = []
        if self.entities:
            action_options.append({"value": "delete_entity", "label": "Delete entity"})
        if self.connections:
            action_options.append({"value": "delete_connection", "label": "Delete connection"})
        action_options.append({"value": "back", "label": "Back to main menu"})

        return self.async_show_form(
            step_id="manage_existing",
            data_schema=vol.Schema(
                {
                    vol.Required("action"): SelectSelector(
                        SelectSelectorConfig(
                            options=action_options,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
            description_placeholders={
                "entities_list": self._format_entities_list(),
                "connections_list": self._format_connections_list(),
            },
        )

    async def async_step_delete_entity(self, user_input: Optional[Dict[str, Any]] = None):
        """Handle deleting an entity."""
        if user_input is not None:
            entity_name = user_input["entity"]

            # Remove the entity
            self.entities = [e for e in self.entities if e[CONF_NAME] != entity_name]

            # Remove any connections involving this entity
            self.connections = [
                c for c in self.connections if c["source"] != entity_name and c["target"] != entity_name
            ]

            return await self.async_step_init()

        if not self.entities:
            return await self.async_step_manage_existing()

        entity_options = [entity[CONF_NAME] for entity in self.entities]

        return self.async_show_form(
            step_id="delete_entity",
            data_schema=vol.Schema(
                {
                    vol.Required("entity"): SelectSelector(
                        SelectSelectorConfig(
                            options=entity_options,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
        )

    async def async_step_delete_connection(self, user_input: Optional[Dict[str, Any]] = None):
        """Handle deleting a connection."""
        if user_input is not None:
            connection_index = int(user_input["connection"])

            # Remove the connection
            if 0 <= connection_index < len(self.connections):
                self.connections.pop(connection_index)

            return await self.async_step_init()

        if not self.connections:
            return await self.async_step_manage_existing()

        connection_options = [str(i) for i, conn in enumerate(self.connections)]

        return self.async_show_form(
            step_id="delete_connection",
            data_schema=vol.Schema(
                {
                    vol.Required("connection"): SelectSelector(
                        SelectSelectorConfig(
                            options=connection_options,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
        )

    async def async_step_save(self, user_input: Optional[Dict[str, Any]] = None):
        """Save the configuration changes."""
        # Update the config entry data
        new_data = {
            CONF_ENTITIES: self.entities,
            CONF_CONNECTIONS: self.connections,
        }

        # Update the config entry
        self.hass.config_entries.async_update_entry(
            self.config_entry,
            data=new_data,
        )

        # Return to trigger a reload
        return self.async_create_entry(title="", data={})
