"""HAEO type system with field-based metadata."""

from __future__ import annotations

from typing import Union

from .battery import BatteryConfig
from .grid import GridConfig
from .load_constant import LoadConstantConfig
from .load_forecast import LoadForecastConfig
from .generator import GeneratorConfig
from .connection import ConnectionConfig
from .net import NetConfig

# List of all element types for iteration
ELEMENT_TYPES = {
    "battery": BatteryConfig,
    "connection": ConnectionConfig,
    "generator": GeneratorConfig,
    "grid": GridConfig,
    "load_constant": LoadConstantConfig,
    "load_forecast": LoadForecastConfig,
    "net": NetConfig,
}

# Type-safe discriminated union for element configurations
ElementConfig = Union[
    BatteryConfig,
    GridConfig,
    LoadConstantConfig,
    LoadForecastConfig,
    GeneratorConfig,
    NetConfig,
    ConnectionConfig,
]
