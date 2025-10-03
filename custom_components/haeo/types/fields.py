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
            "schema": vol.All(str, vol.Strip, vol.Length(min=1, msg="Name cannot be empty")),
        },
    )


def element_name_field(description: str, *, default: str | None = None) -> str:
    """Field for referencing another element."""
    return field(default=default, metadata={"description": description, "schema": None})


def power_field(description: str, *, optional: bool = False, default: float | None = None) -> float | None:
    """Field for a constant power value."""
    return field(
        default=default,
        metadata={
            "description": description,
            "field_type": (SensorDeviceClass.POWER, "constant"),
            "schema": vol.All(
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
            ),
            "optional": optional,
        },
    )


def power_sensors_field(description: str, *, optional: bool = False) -> Sequence[str]:
    """Field for a power sensor."""
    return field(
        default_factory=list,
        metadata={
            "description": description,
            "field_type": (SensorDeviceClass.POWER, "sensor"),
            "schema": EntitySelector(EntitySelectorConfig(domain="sensor", device_class=[SensorDeviceClass.POWER])),
            "optional": optional,
        },
    )


def power_forecast_field(description: str, *, optional: bool = False) -> Sequence[str]:
    """Field for a sequence of power forecast sensors."""
    return field(
        default_factory=list,
        metadata={
            "default_factory": list,
            "description": description,
            "field_type": (SensorDeviceClass.POWER, "forecast"),
            "schema": EntitySelector(
                EntitySelectorConfig(domain="sensor", multiple=True, device_class=[SensorDeviceClass.POWER]),
            ),
            "optional": optional,
        },
    )


def power_flow_field(description: str, *, optional: bool = False, default: float | None = None) -> float | None:
    """Field for a power flow value."""
    return field(
        default=default,
        metadata={
            "description": description,
            "field_type": (SensorDeviceClass.POWER, "constant"),
            "schema": vol.All(
                vol.Coerce(float),
                NumberSelector(
                    NumberSelectorConfig(mode=NumberSelectorMode.BOX, step=1, unit_of_measurement=UnitOfPower.WATT),
                ),
            ),
            "optional": optional,
        },
    )


def energy_field(description: str, *, optional: bool = False, default: float | None = None) -> float | None:
    """Field for an energy value."""
    return field(
        default=default,
        metadata={
            "description": description,
            "field_type": (SensorDeviceClass.ENERGY, "constant"),
            "schema": vol.All(
                vol.Coerce(float),
                vol.Range(min=0, min_included=True, msg="Value must be positive"),
                NumberSelector(
                    NumberSelectorConfig(mode=NumberSelectorMode.BOX, min=1, step=1, unit_of_measurement="Wh"),
                ),
            ),
            "optional": optional,
        },
    )


def energy_sensors_field(description: str, *, optional: bool = False) -> Sequence[str]:
    """Field for a sequence of energy sensors."""
    return field(
        default_factory=list,
        metadata={
            "description": description,
            "field_type": (SensorDeviceClass.ENERGY, "sensor"),
            "schema": EntitySelector(
                EntitySelectorConfig(
                    domain="sensor",
                    multiple=True,
                    device_class=[SensorDeviceClass.BATTERY, SensorDeviceClass.ENERGY_STORAGE],
                ),
            ),
            "optional": optional,
        },
    )


def energy_forecast_field(description: str, *, optional: bool = False) -> Sequence[str]:
    """Field for a sequence of energy forecast sensors stored as attributes."""
    return field(
        default_factory=list,
        metadata={
            "description": description,
            "field_type": (SensorDeviceClass.ENERGY, "forecast"),
            "schema": EntitySelector(
                EntitySelectorConfig(domain="sensor", multiple=True, device_class=[SensorDeviceClass.ENERGY]),
            ),
            "optional": optional,
        },
    )


def price_field(description: str, *, optional: bool = False) -> float | None:
    """Field for a price value."""
    return field(
        default=None,
        metadata={
            "description": description,
            "field_type": (SensorDeviceClass.MONETARY, "constant"),
            "schema": vol.All(
                vol.Coerce(float),
                NumberSelector(NumberSelectorConfig(mode=NumberSelectorMode.BOX, step=1, unit_of_measurement="$/kWh")),
            ),
            "optional": optional,
        },
    )


def price_sensors_field(description: str, *, optional: bool = False) -> Sequence[str]:
    """Field for a sequence of price sensors."""
    return field(
        default_factory=list,
        metadata={
            "description": description,
            "field_type": (SensorDeviceClass.MONETARY, "sensor"),
            "schema": EntitySelector(
                EntitySelectorConfig(
                    domain="sensor",
                    multiple=True,
                    device_class=[SensorDeviceClass.MONETARY, SensorDeviceClass.ENERGY],
                ),
            ),
            "optional": optional,
        },
    )


def price_forecast_field(description: str, *, optional: bool = False) -> Sequence[str]:
    """Field for a sequence of price forecast sensors."""
    return field(
        default_factory=list,
        metadata={
            "description": description,
            "field_type": (SensorDeviceClass.MONETARY, "forecast"),
            "schema": EntitySelector(
                EntitySelectorConfig(
                    domain="sensor",
                    multiple=True,
                    device_class=[SensorDeviceClass.MONETARY, SensorDeviceClass.ENERGY],
                ),
            ),
            "optional": optional,
        },
    )


def price_live_forecast_field(description: str, *, optional: bool = False) -> dict[str, Any]:
    """Field for both live price sensor and forecast sensors combined."""
    return field(
        default_factory=dict,
        metadata={
            "description": description,
            "field_type": (SensorDeviceClass.MONETARY, "live_forecast"),
            "schema": {
                vol.Optional("live"): EntitySelector(
                    EntitySelectorConfig(
                        domain="sensor",
                        device_class=[SensorDeviceClass.MONETARY, SensorDeviceClass.ENERGY],
                    ),
                ),
                vol.Optional("forecast"): EntitySelector(
                    EntitySelectorConfig(
                        domain="sensor",
                        multiple=True,
                        device_class=[SensorDeviceClass.MONETARY, SensorDeviceClass.ENERGY],
                    ),
                ),
            },
            "optional": optional,
        },
    )


def percentage_field(description: str, *, optional: bool = False, default: float | None = None) -> float | None:
    """Field for a percentage value."""
    return field(
        default=default,
        metadata={
            "description": description,
            "field_type": ("%", "constant"),
            "schema": vol.All(vol.Coerce(float), vol.Range(min=0, max=100, msg="Value must be between 0 and 100")),
            "optional": optional,
        },
    )


def battery_soc_field(description: str, *, optional: bool = False, default: float | None = None) -> float | None:
    """Field for battery state of charge percentage."""
    return field(
        default=default,
        metadata={
            "description": description,
            "field_type": (SensorDeviceClass.BATTERY, "constant"),
            "schema": vol.All(vol.Coerce(float), vol.Range(min=0, max=100, msg="Value must be between 0 and 100")),
            "optional": optional,
        },
    )


def battery_soc_sensor_field(description: str, *, optional: bool = False) -> Sequence[str]:
    """Field for a battery SOC sensor."""
    return field(
        default_factory=list,
        metadata={
            "description": description,
            "field_type": (SensorDeviceClass.BATTERY, "sensor"),
            "schema": EntitySelector(EntitySelectorConfig(domain="sensor", device_class=[SensorDeviceClass.BATTERY])),
            "optional": optional,
        },
    )


def boolean_field(description: str, *, optional: bool = False, default: bool | None = None) -> bool | None:
    """Field for a boolean value."""
    return field(
        default=default,
        metadata={
            "description": description,
            "field_type": ("boolean", "constant"),
            "schema": BooleanSelector(BooleanSelectorConfig()),
            "optional": optional,
        },
    )
