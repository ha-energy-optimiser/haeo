"""Field functions for HAEO type system."""

from __future__ import annotations

from dataclasses import field
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor.const import SensorDeviceClass
from homeassistant.const import UnitOfPower
from homeassistant.helpers.selector import (
    BooleanSelector,
    BooleanSelectorConfig,
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)
import voluptuous as vol

if TYPE_CHECKING:
    from collections.abc import Sequence


def name_field(description: str, *, default: str | None = None) -> str | None:
    """Field for element name."""
    return field(
        default=default,
        metadata={
            "description": description,
            "schema": {vol.Required("name"): vol.All(str, vol.Strip, vol.Length(min=1, msg="Name cannot be empty"))},
        },
    )


def element_name_field(description: str, *, optional: bool = False, default: str | None = None) -> str | None:
    """Field for referencing another element."""
    wrap = vol.Required if not optional else vol.Optional
    return field(
        default=default,
        metadata={
            "description": description,
            "schema": {
                wrap("element_name"): vol.All(str, vol.Strip, vol.Length(min=1, msg="Element name cannot be empty"))
            },
        },
    )


def power_field(description: str, *, optional: bool = False, default: float | None = None) -> float | None:
    """Field for a constant power value."""
    wrap = vol.Required if not optional else vol.Optional
    return field(
        default=default,
        metadata={
            "description": description,
            "field_type": (SensorDeviceClass.POWER, "constant"),
            "schema": {
                wrap("power"): vol.All(
                    vol.Coerce(float),
                    vol.Range(min=0, min_included=True, msg="Value must be positive"),
                    NumberSelector(
                        NumberSelectorConfig(
                            mode=NumberSelectorMode.BOX,
                            min=1,
                            step=1,
                            unit_of_measurement=UnitOfPower.WATT,
                        ),
                    ),
                )
            },
            "optional": optional,
        },
    )


def power_sensors_field(description: str, *, optional: bool = False) -> Sequence[str]:
    """Field for a power sensor."""
    wrap = vol.Required if not optional else vol.Optional
    return field(
        default_factory=list,
        metadata={
            "description": description,
            "field_type": (SensorDeviceClass.POWER, "sensor"),
            "schema": {
                wrap("sensors"): EntitySelector(
                    EntitySelectorConfig(domain="sensor", device_class=[SensorDeviceClass.POWER])
                )
            },
        },
    )


def power_forecast_field(description: str, *, optional: bool = False) -> dict[str, Any]:
    """Field for a sequence of power forecast sensors."""
    wrap = vol.Required if not optional else vol.Optional
    return field(
        default_factory=dict,
        metadata={
            "default_factory": list,
            "description": description,
            "field_type": (SensorDeviceClass.POWER, "forecast"),
            "schema": {
                wrap("forecast"): EntitySelector(
                    EntitySelectorConfig(domain="sensor", multiple=True, device_class=[SensorDeviceClass.POWER]),
                )
            },
        },
    )


def power_flow_field(description: str, *, optional: bool = False, default: float | None = None) -> float | None:
    """Field for a power flow value."""
    wrap = vol.Required if not optional else vol.Optional
    return field(
        default=default,
        metadata={
            "description": description,
            "field_type": (SensorDeviceClass.POWER, "constant"),
            "schema": {
                wrap("power_flow"): vol.All(
                    vol.Coerce(float),
                    NumberSelector(
                        NumberSelectorConfig(mode=NumberSelectorMode.BOX, step=1, unit_of_measurement=UnitOfPower.WATT),
                    ),
                )
            },
        },
    )


def energy_field(description: str, *, optional: bool = False, default: float | None = None) -> float | None:
    """Field for an energy value."""
    wrap = vol.Required if not optional else vol.Optional
    return field(
        default=default,
        metadata={
            "description": description,
            "field_type": (SensorDeviceClass.ENERGY, "constant"),
            "schema": {
                wrap("energy"): vol.All(
                    vol.Coerce(float),
                    vol.Range(min=0, min_included=True, msg="Value must be positive"),
                    NumberSelector(
                        NumberSelectorConfig(mode=NumberSelectorMode.BOX, min=1, step=1, unit_of_measurement="Wh"),
                    ),
                )
            },
        },
    )


def energy_sensors_field(description: str, *, optional: bool = False) -> Sequence[str]:
    """Field for a sequence of energy sensors."""
    wrap = vol.Required if not optional else vol.Optional
    return field(
        default_factory=list,
        metadata={
            "description": description,
            "field_type": (SensorDeviceClass.ENERGY, "sensor"),
            "schema": {
                wrap("sensors"): EntitySelector(
                    EntitySelectorConfig(
                        domain="sensor",
                        multiple=True,
                        device_class=[SensorDeviceClass.BATTERY, SensorDeviceClass.ENERGY_STORAGE],
                    ),
                )
            },
        },
    )


def energy_forecast_field(description: str, *, optional: bool = False) -> Sequence[str]:
    """Field for a sequence of energy forecast sensors stored as attributes."""
    wrap = vol.Required if not optional else vol.Optional
    return field(
        default_factory=list,
        metadata={
            "description": description,
            "field_type": (SensorDeviceClass.ENERGY, "forecast"),
            "schema": {
                wrap("forecast"): EntitySelector(
                    EntitySelectorConfig(domain="sensor", multiple=True, device_class=[SensorDeviceClass.ENERGY])
                )
            },
        },
    )


def price_field(description: str, *, optional: bool = False) -> float | None:
    """Field for a price value."""
    wrap = vol.Required if not optional else vol.Optional
    return field(
        default=None,
        metadata={
            "description": description,
            "field_type": (SensorDeviceClass.MONETARY, "constant"),
            "schema": {
                wrap("price"): vol.All(
                    vol.Coerce(float),
                    NumberSelector(
                        NumberSelectorConfig(mode=NumberSelectorMode.BOX, step=1, unit_of_measurement="$/kWh")
                    ),
                )
            },
        },
    )


def price_sensors_field(description: str, *, optional: bool = False) -> Sequence[str]:
    """Field for a sequence of price sensors."""
    return field(
        default_factory=list,
        metadata={
            "description": description,
            "field_type": (SensorDeviceClass.MONETARY, "sensor"),
            "schema": {wrap("sensors"): EntitySelector(EntitySelectorConfig(domain="sensor", multiple=True))},
        },
    )


def price_forecast_field(description: str, *, optional: bool = False) -> Sequence[str]:
    """Field for a sequence of price forecast sensors."""
    wrap = vol.Required if not optional else vol.Optional
    return field(
        default_factory=list,
        metadata={
            "description": description,
            "field_type": (SensorDeviceClass.MONETARY, "forecast"),
            "schema": {wrap("forecast"): EntitySelector(EntitySelectorConfig(domain="sensor", multiple=True))},
        },
    )


def price_live_forecast_field(description: str) -> dict[str, Any]:
    """Field for both live price sensor and forecast sensors combined."""
    return field(
        default_factory=dict,
        metadata={
            "description": description,
            "field_type": (SensorDeviceClass.MONETARY, "live_forecast"),
            "schema": {
                vol.Optional("live"): EntitySelector(EntitySelectorConfig(domain="sensor", multiple=True)),
                vol.Optional("forecast"): EntitySelector(EntitySelectorConfig(domain="sensor", multiple=True)),
            },
        },
    )


def percentage_field(description: str, *, optional: bool = False, default: float | None = None) -> float | None:
    """Field for a percentage value."""
    wrap = vol.Required if not optional else vol.Optional
    return field(
        default=default,
        metadata={
            "description": description,
            "field_type": ("%", "constant"),
            "schema": {
                wrap("percentage"): vol.All(
                    vol.Coerce(float), vol.Range(min=0, max=100, msg="Value must be between 0 and 100")
                )
            },
        },
    )


def battery_soc_field(description: str, *, optional: bool = False, default: float | None = None) -> float | None:
    """Field for battery state of charge percentage."""
    wrap = vol.Required if not optional else vol.Optional
    return field(
        default=default,
        metadata={
            "description": description,
            "field_type": (SensorDeviceClass.BATTERY, "constant"),
            "schema": {
                wrap("battery_soc"): vol.All(
                    vol.Coerce(float), vol.Range(min=0, max=100, msg="Value must be between 0 and 100")
                )
            },
        },
    )


def battery_soc_sensor_field(description: str, *, optional: bool = False) -> Sequence[str]:
    """Field for a battery SOC sensor."""
    wrap = vol.Required if not optional else vol.Optional
    return field(
        default_factory=list,
        metadata={
            "description": description,
            "field_type": (SensorDeviceClass.BATTERY, "sensor"),
            "schema": {
                wrap("sensors"): EntitySelector(
                    EntitySelectorConfig(domain="sensor", device_class=[SensorDeviceClass.BATTERY])
                )
            },
        },
    )


def boolean_field(description: str, *, optional: bool = False, default: bool | None = None) -> bool | None:
    """Field for a boolean value."""
    wrap = vol.Required if not optional else vol.Optional
    return field(
        default=default,
        metadata={
            "description": description,
            "field_type": ("boolean", "constant"),
            "schema": {wrap("value"): BooleanSelector(BooleanSelectorConfig())},
        },
    )
