from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .fields import name_field


@dataclass
class NetConfig:
    """Net element configuration."""

    element_type: Literal["net"] = "net"

    name: str = name_field("Network node name")
