from typing import Sequence
from pulp import LpVariable

from .element import Element


class Grid(Element):
    """Unified Grid entity for electrical system modeling with separate import/export pricing."""

    def __init__(
        self,
        name: str,
        period: int,
        n_periods: int,
        import_limit: float | None = None,
        export_limit: float | None = None,
        import_price: Sequence[float] | None = None,
        export_price: Sequence[float] | None = None,
    ):
        # Validate that the forecasts match the number of periods
        if import_price is not None and len(import_price) != n_periods:
            raise ValueError(f"import_price length ({len(import_price)}) must match n_periods ({n_periods})")
        if export_price is not None and len(export_price) != n_periods:
            raise ValueError(f"export_price length ({len(export_price)}) must match n_periods ({n_periods})")

        # power_consumption: positive when exporting to grid (grid consuming our power)
        power_consumption = [
            LpVariable(name=f"{name}_export_{i}", lowBound=0, upBound=export_limit) for i in range(n_periods)
        ]
        # power_production: positive when importing from grid (grid producing power for us)
        power_production = [
            LpVariable(name=f"{name}_import_{i}", lowBound=0, upBound=import_limit) for i in range(n_periods)
        ]

        super().__init__(
            name=name,
            period=period,
            n_periods=n_periods,
            power_consumption=power_consumption,  # Consuming = exporting (grid consuming our power)
            power_production=power_production,  # Producing = importing (grid producing power for us)
            price_consumption=export_price,  # Revenue when exporting (grid pays us)
            price_production=import_price,  # Cost when importing (we pay grid)
        )
