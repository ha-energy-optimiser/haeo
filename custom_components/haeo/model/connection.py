from collections.abc import Sequence
from dataclasses import dataclass

from pulp import LpConstraint, LpVariable


@dataclass
class Connection:
    """Connection class for electrical system modeling."""

    def __init__(
        self,
        name: str,
        period: int,
        n_periods: int,
        source: str,
        target: str,
        min_power: float | None = None,
        max_power: float | None = None,
    ):
        self.name = name
        self.source = source
        self.target = target

        # Initialize power variables for the connection
        # For bidirectional connections, min_power can be negative
        # Positive power = flow from source to target
        # Negative power = flow from target to source
        # None bounds mean no limit (infinite bounds)
        self.power = [
            LpVariable(name=f"{name}_power_{i}", lowBound=min_power, upBound=max_power) for i in range(n_periods)
        ]

    def constraints(self) -> Sequence[LpConstraint]:
        """Return constraints for the connection."""
        return []

    def cost(self) -> float:
        """Return the cost of the connection with cycling penalties."""
        return 0
