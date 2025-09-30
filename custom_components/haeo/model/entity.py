from dataclasses import dataclass
from typing import Sequence, MutableSequence
from pulp import LpVariable, LpConstraint, lpSum


@dataclass
class Entity:
    """Generic electrical entity which models the relationship between power and energy."""

    # Name of the entity
    name: str

    # Period for time step calculations
    period: int
    n_periods: int

    # Separate power variables for consumption and production
    power_consumption: Sequence[LpVariable | float] | None = None  # Positive when consuming
    power_production: Sequence[LpVariable | float] | None = None  # Positive when producing

    # Separate prices for consumption and production
    price_consumption: Sequence[float] | None = None  # Cost when consuming
    price_production: Sequence[float] | None = None  # Revenue when producing

    energy: Sequence[LpVariable | float] | None = None
    efficiency: float = 1.0

    def constraints(self) -> Sequence[LpConstraint]:
        """Return constraints for the entity."""
        constraints: MutableSequence[LpConstraint] = []

        # Energy balance constraint using separate power variables
        if self.energy is not None and self.power_consumption is not None and self.power_production is not None:
            # Energy balance: E[t] = E[t-1] + (charge * efficiency) - (discharge / efficiency)
            # Time step is period seconds = p * period/3600 for watt-hour calculations
            for t in range(1, len(self.energy)):
                energy_change = (
                    self.power_consumption[t - 1] * self.efficiency - self.power_production[t - 1] / self.efficiency
                ) * (self.period / 3600)
                constraints.append(self.energy[t] == self.energy[t - 1] + energy_change)

        return constraints

    def cost(self):
        """Return the cost of the entity using separate consumption/production variables."""
        cost = 0
        # Handle separate consumption and production pricing
        if self.price_consumption is not None and self.power_consumption is not None:
            # Revenue for consumption (exporting to grid) - negative cost = revenue
            cost += lpSum(-price * power for price, power in zip(self.price_consumption, self.power_consumption))

        if self.price_production is not None and self.power_production is not None:
            # Cost for production (importing from grid)
            cost += lpSum(price * power for price, power in zip(self.price_production, self.power_production))

        return cost
