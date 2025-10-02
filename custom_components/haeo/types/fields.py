"""Field functions for HAEO type system."""

from __future__ import annotations

from typing import Sequence

from homeassistant.components.sensor.const import SensorDeviceClass
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)
from dataclasses import field
import voluptuous as vol


def name_field(description: str, default: str = None) -> str:
    """Field for element name."""
    return field(
        default=default,
        metadata={
            "description": description,
            "schema": vol.All(str, vol.Strip, vol.Length(min=1, msg="Name cannot be empty")),
        },
    )


def element_name_field(description: str, default: str = None) -> str:
    """Field for referencing another element."""
    return field(default=default, metadata={"description": description, "schema": None})


def power_field(description: str, optional: bool = False, default: float = None) -> float:
    """Field for a constant power value."""
    return field(
        default=default,
        metadata={
            "description": description,
            "schema": vol.All(
                vol.Coerce(float),
                vol.Range(min=0, min_included=True, msg="Value must be positive"),
                NumberSelector(
                    NumberSelectorConfig(mode=NumberSelectorMode.BOX, min=1, step=1, unit_of_measurement="W")
                ),
            ),
            "optional": optional,
        },
    )


def power_sensors_field(description: str, optional: bool = False) -> Sequence[str]:
    """Field for a power sensor."""
    return field(
        default_factory=list,
        metadata={
            "description": description,
            "schema": EntitySelector(EntitySelectorConfig(domain="sensor", device_class=[SensorDeviceClass.POWER])),
            "optional": optional,
        },
    )


def power_forecast_sensors_field(description: str, optional: bool = False) -> Sequence[str]:
    """Field for a sequence of power forecast sensors."""
    return field(
        default_factory=list,
        metadata={
            "default_factory": list,
            "description": description,
            "schema": EntitySelector(
                EntitySelectorConfig(domain="sensor", multiple=True, device_class=[SensorDeviceClass.POWER])
            ),
            "optional": optional,
        },
    )


def power_flow_field(description: str, optional: bool = False, default: float = None) -> float:
    """Field for a power flow value."""
    return field(
        default=default,
        metadata={
            "description": description,
            "schema": vol.All(
                vol.Coerce(float),
                NumberSelector(NumberSelectorConfig(mode=NumberSelectorMode.BOX, step=1, unit_of_measurement="W")),
            ),
            "optional": optional,
        },
    )


def energy_field(description: str, optional: bool = False, default: float = None) -> float:
    """Field for an energy value."""
    return field(
        default=default,
        metadata={
            "description": description,
            "schema": vol.All(
                vol.Coerce(float),
                vol.Range(min=0, min_included=True, msg="Value must be positive"),
                NumberSelector(
                    NumberSelectorConfig(mode=NumberSelectorMode.BOX, min=1, step=1, unit_of_measurement="Wh")
                ),
            ),
            "optional": optional,
        },
    )


def energy_sensors_field(description: str, optional: bool = False) -> Sequence[str]:
    """Field for a sequence of energy sensors."""
    return field(
        default_factory=list,
        metadata={
            "description": description,
            "schema": EntitySelector(
                EntitySelectorConfig(
                    domain="sensor",
                    multiple=True,
                    device_class=[SensorDeviceClass.BATTERY, SensorDeviceClass.ENERGY_STORAGE],
                )
            ),
            "optional": optional,
        },
    )


def energy_forecast_sensors_field(description: str, optional: bool = False) -> Sequence[str]:
    """Field for a sequence of energy forecast sensors stored as attributes."""
    return field(
        default_factory=list,
        metadata={
            "description": description,
            "schema": EntitySelector(
                EntitySelectorConfig(domain="sensor", multiple=True, device_class=[SensorDeviceClass.ENERGY])
            ),
            "optional": optional,
        },
    )


def price_field(description: str, optional: bool = False) -> float:
    """Field for a price value."""
    return field(
        default=None,
        metadata={
            "description": description,
            "schema": vol.All(
                vol.Coerce(float),
                NumberSelector(NumberSelectorConfig(mode=NumberSelectorMode.BOX, step=1, unit_of_measurement="$/kWh")),
            ),
            "optional": optional,
        },
    )


def price_sensors_field(description: str, optional: bool = False) -> Sequence[str]:
    """Field for a sequence of price sensors."""
    return field(
        default_factory=list,
        metadata={
            "description": description,
            "schema": EntitySelector(
                EntitySelectorConfig(
                    domain="sensor", multiple=True, device_class=[SensorDeviceClass.MONETARY, SensorDeviceClass.ENERGY]
                )
            ),
            "optional": optional,
        },
    )


def price_forecast_sensors_field(description: str, optional: bool = False) -> Sequence[str]:
    """Field for a sequence of price forecast sensors."""
    return field(
        default_factory=list,
        metadata={
            "description": description,
            "schema": EntitySelector(
                EntitySelectorConfig(
                    domain="sensor", multiple=True, device_class=[SensorDeviceClass.MONETARY, SensorDeviceClass.ENERGY]
                )
            ),
            "optional": optional,
        },
    )


def percentage_field(description: str, optional: bool = False, default: float = None) -> float:
    """Field for a percentage value."""
    return field(
        default=default,
        metadata={
            "description": description,
            "schema": vol.All(vol.Coerce(float), vol.Range(min=0, max=100, msg="Value must be between 0 and 100")),
            "optional": optional,
        },
    )


def battery_soc_sensor_field(description: str, optional: bool = False) -> Sequence[str]:
    """Field for a battery SOC sensor."""
    return field(
        default_factory=list,
        metadata={
            "description": description,
            "schema": EntitySelector(EntitySelectorConfig(domain="sensor", device_class=[SensorDeviceClass.BATTERY])),
            "optional": optional,
        },
    )


def boolean_field(description: str, optional: bool = False, default: bool = None) -> bool:
    """Field for a boolean value."""
    return field(
        default=default,
        metadata={
            "description": description,
            "schema": bool,
            "optional": optional,
        },
    )
