from dataclasses import dataclass
from typing import Sequence
from pulp import LpVariable, LpConstraint

from .entity import Entity as Entity


@dataclass
class Connection:
    """Connection class for electrical system modeling."""

    def __init__(
        self,
        period: int,
        n_periods: int,
        source_entity: Entity,
        target_entity: Entity,
        min_power: float | None = None,
        max_power: float | None = None,
    ):
        self.name = source_entity.name + "_to_" + target_entity.name
        self.source_entity = source_entity
        self.target_entity = target_entity
        self.power = [
            LpVariable(name=f"{self.name}_power_{i}", lowBound=min_power, upBound=max_power) for i in range(n_periods)
        ]

    def constraints(self) -> Sequence[LpConstraint]:
        """Return constraints for the connection."""
        return []

    def cost(self) -> float:
        """Return the cost of the connection with cycling penalties."""
        return 0
