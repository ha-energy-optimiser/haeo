from collections.abc import Sequence

import numpy as np
from pulp import LpVariable

from .element import Element


class Generator(Element):
    """Generator entity for electrical system modeling."""

    def __init__(
        self,
        name: str,
        period: int,
        n_periods: int,
        forecast: Sequence[float],
        curtailment: bool = True,
        price_production: float | Sequence[float] | None = None,
        price_consumption: float | Sequence[float] | None = None,
    ):
        # Validate forecast length matches n_periods if provided
        if len(forecast) != n_periods:
            raise ValueError(f"forecast length ({len(forecast)}) must match n_periods ({n_periods})")

        ones = np.ones(n_periods)

        # If we can curtail then we can set the power limits from 0 to the forecast
        # Otherwise we just set the power to the forecast
        super().__init__(
            name=name,
            period=period,
            n_periods=n_periods,
            power_production=[
                LpVariable(name=f"{name}_power_{i}", lowBound=0, upBound=v) for i, v in enumerate(forecast)
            ]
            if curtailment
            else forecast,
            # ones * price will either be a noop if price is a sequence or will create a sequence if price is a scalar
            price_production=(ones * price_production).tolist() if price_production is not None else None,
            price_consumption=(ones * price_consumption).tolist() if price_consumption is not None else None,
        )
