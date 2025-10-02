from __future__ import annotations

from typing import Literal
from dataclasses import dataclass

from .fields import name_field, power_field


@dataclass
class LoadConstantConfig:
    """Constant load element configuration."""

    element_type: Literal["load_constant"] = "load_constant"

    name: str = name_field("Load name")

    power: float = power_field("Constant power consumption in W")
