from dataclasses import dataclass, field
from typing import Sequence, Dict, Tuple, MutableSequence
from pulp import LpConstraint, LpProblem, LpMinimize, LpStatus, value, lpSum

from .entity import Entity
from .connection import Connection
from .battery import Battery
from .generator import Generator
from .load import Load
from .grid import Grid
from .net import Net


@dataclass
class Network:
    """Network class for electrical system modeling."""

    name: str
    period: int
    n_periods: int
    entities: Dict[str, Entity] = field(default_factory=dict)
    connections: Dict[Tuple[str, str], Connection] = field(default_factory=dict)

    def add(self, entity_type: str, name: str, **kwargs) -> Entity:
        """Add an entity to the network by type.

        Args:
            entity_type: Type of entity ('battery', 'generator', 'load', 'grid', 'net')
            name: Name of the entity
            **kwargs: Additional arguments specific to the entity type

        Returns:
            The created entity
        """
        # Set n_periods if not provided and required by entity type
        self.entities[name] = {
            "battery": Battery,
            "generator": Generator,
            "load": Load,
            "grid": Grid,
            "net": Net,
        }[entity_type.lower()](name=name, period=self.period, n_periods=self.n_periods, **kwargs)

        return self.entities[name]

    def connect(
        self,
        source_name: str,
        target_name: str,
        min_power: float | None = None,
        max_power: float | None = None,
    ) -> Connection:
        """Connect two entities in the network.

        Args:
            source_name: Name of the source entity
            target_name: Name of the target entity
            efficiency: Connection efficiency (0-1)
            min_power: Minimum power flow
            max_power: Maximum power flow

        Returns:
            The created connection
        """
        if source_name not in self.entities:
            raise ValueError(f"Source entity '{source_name}' not found in network")
        if target_name not in self.entities:
            raise ValueError(f"Target entity '{target_name}' not found in network")

        source_entity = self.entities[source_name]
        target_entity = self.entities[target_name]

        connection = Connection(
            period=self.period,
            n_periods=self.n_periods,
            source_entity=source_entity,
            target_entity=target_entity,
            min_power=min_power,
            max_power=max_power,
        )

        # Store connection using tuple of names as key
        connection_key = (source_name, target_name)
        self.connections[connection_key] = connection

        return connection

    def constraints(self) -> Sequence[LpConstraint]:
        """Return constraints for the network."""
        constraints: MutableSequence[LpConstraint] = []

        # Add entity-specific constraints
        for entity in self.entities.values():
            constraints.extend(entity.constraints())

        # Add connection constraints
        for connection in self.connections.values():
            constraints.extend(connection.constraints())

        # Add power balance constraints for each entity based on the connections
        for entity in self.entities.values():
            for t in range(self.n_periods):
                balance_terms = []

                # Add entity's own consumption and production
                if entity.power_consumption is not None:
                    balance_terms.append(-entity.power_consumption[t])
                if entity.power_production is not None:
                    balance_terms.append(entity.power_production[t])

                # Add connection flows
                for connection in self.connections.values():
                    if connection.source_entity == entity:
                        # Power leaving the entity (negative for balance)
                        balance_terms.append(-connection.power[t])
                    elif connection.target_entity == entity:
                        # Power entering the entity (positive for balance)
                        balance_terms.append(connection.power[t])

                # Power balance: sum of all terms should be zero
                if balance_terms:
                    constraints.append(lpSum(balance_terms) == 0)

        return constraints

    def cost(self):
        """Return the cost expression for the network."""
        return lpSum(
            [
                *[e.cost() for e in self.entities.values() if e.cost() != 0],
                *[c.cost() for c in self.connections.values() if c.cost() != 0],
            ]
        )

    def optimize(self) -> float:
        """Solve the optimization problem and return the cost.

        After optimization, access optimized values directly from entities and connections.

        Returns:
            The total optimization cost
        """
        # Create the LP problem
        prob = LpProblem(f"{self.name}_optimization", LpMinimize)

        # Add the objective function (minimize cost)
        prob += self.cost(), "Total_Cost"

        # Add all constraints
        for constraint in self.constraints():
            prob += constraint

        # Solve the problem
        status = prob.solve()

        print(f"Optimization status: {LpStatus[status]}")

        if status == 1:  # Optimal solution found
            objective_value = value(prob.objective) if prob.objective is not None else 0.0
            # Handle PuLP return types - value() can return various types
            if isinstance(objective_value, (int, float)):
                total_cost = float(objective_value)
            else:
                # Fallback for other PuLP types
                total_cost = 0.0
            print(f"Debug: prob.objective = {prob.objective}")
            print(f"Debug: total_cost = {total_cost}")
            print(f"Debug: returning total_cost = {total_cost}")
            return total_cost
        else:
            raise ValueError(f"Optimization failed with status: {LpStatus[status]}")
