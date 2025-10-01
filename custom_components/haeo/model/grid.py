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
        import_limit: float,
        export_limit: float,
        price_import: Sequence[float] | None,
        price_export: Sequence[float] | None,
    ):
        # Validate that the forecasts match the number of periods
        if price_import is not None and len(price_import) != n_periods:
            raise ValueError(f"price_import length ({len(price_import)}) must match n_periods ({n_periods})")
        if price_export is not None and len(price_export) != n_periods:
            raise ValueError(f"price_export length ({len(price_export)}) must match n_periods ({n_periods})")

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
            price_consumption=price_export,  # Revenue when exporting (grid pays us)
            price_production=price_import,  # Cost when importing (we pay grid)
        )
