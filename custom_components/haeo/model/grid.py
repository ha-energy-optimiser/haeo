"""Grid entity for electrical system modeling with separate import/export pricing."""

from collections.abc import Sequence

import numpy as np
from pulp import LpVariable

from .element import Element


class Grid(Element):
    """Unified Grid entity for electrical system modeling with separate import/export pricing."""

    def __init__(
        self,
        name: str,
        period: int,
        n_periods: int,
        *,
        import_limit: float | None = None,
        export_limit: float | None = None,
        import_price: Sequence[float] | float | None = None,
        export_price: Sequence[float] | float | None = None,
    ) -> None:
        """Initialize a grid connection entity.

        Args:
            name: Name of the grid connection
            period: Time period in seconds
            n_periods: Number of time periods
            import_limit: Maximum import power in watts
            export_limit: Maximum export power in watts
            import_price: Price per watt when importing
            export_price: Price per watt when exporting

        """

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
            price_consumption=None
            if export_price is None
            else (np.ones(n_periods) * export_price).tolist(),  # Revenue when exporting (grid pays us)
            price_production=None
            if import_price is None
            else (np.ones(n_periods) * import_price).tolist(),  # Cost when importing (we pay grid)
        )
