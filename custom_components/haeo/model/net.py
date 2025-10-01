from .element import Element


class Net(Element):
    """Net entity for electrical system modeling."""

    def __init__(self, name: str, period: int, n_periods: int):
        super().__init__(name=name, period=period, n_periods=n_periods)
