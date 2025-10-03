from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .fields import name_field, power_field


@dataclass
class ConstantLoadConfig:
    """Constant load element configuration."""

    element_type: Literal["constant_load"] = "constant_load"

    name: str = name_field("Load name")

    power: float = power_field("Constant power consumption in W")
