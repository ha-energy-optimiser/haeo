import numpy as np
from pulp import LpVariable

from .entity import Entity


class Battery(Entity):
    """Battery entity for electrical system modeling."""

    def __init__(
        self,
        name: str,
        period: int,
        n_periods: int,
        capacity: float,
        initial_charge_percentage: float,
        min_charge_percentage: float = 10,
        max_charge_percentage: float = 90,
        max_charge_power: float | None = None,
        max_discharge_power: float | None = None,
        efficiency: float = 0.99,
        charge_cost: float | None = None,
        discharge_cost: float | None = None,
    ):
        self.capacity = capacity  # Store capacity in watt-hours

        super().__init__(
            name=name,
            period=period,
            n_periods=n_periods,
            power_consumption=[
                LpVariable(name=f"{name}_power_consumption_{i}", lowBound=0, upBound=max_charge_power)
                for i in range(n_periods)
            ],
            power_production=[
                LpVariable(name=f"{name}_power_production_{i}", lowBound=0, upBound=max_discharge_power)
                for i in range(n_periods)
            ],
            energy=[
                initial_charge_percentage * capacity / 100.0,
                *[
                    LpVariable(
                        name=f"{name}_energy_{i}",
                        lowBound=capacity * (min_charge_percentage / 100.0),
                        upBound=capacity * (max_charge_percentage / 100.0),
                    )
                    for i in range(n_periods - 1)
                ],
            ],
            efficiency=efficiency,
            price_production=(np.ones(n_periods) * discharge_cost).tolist() if discharge_cost is not None else None,
            price_consumption=np.linspace(0, charge_cost, n_periods).tolist() if charge_cost is not None else None,
        )
