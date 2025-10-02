"""Network and connection element configurations for HAEO integration."""

from __future__ import annotations

from typing import Literal
from dataclasses import dataclass

from .fields import name_field, power_flow_field, element_name_field


@dataclass
class ConnectionConfig:
    """Connection element configuration."""

    element_type: Literal["connection"] = "connection"

    name: str = name_field("Connection name")

    source: str = element_name_field("Source element name")
    target: str = element_name_field("Target element name")

    min_power: float | None = power_flow_field("Minimum power flow from source to target", optional=True)
    max_power: float | None = power_flow_field("Maximum power flow from source to target", optional=True)
